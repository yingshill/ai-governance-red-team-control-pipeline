"""Integration test suite: run every control against its dataset.

Enforces:
  * Pass rate threshold (``value`` with ``operator`` ``gte``/``lte``).
  * ``expected_risk_ids`` membership per case.
  * Latency budget P50/P95/P99 from ``config/thresholds.yaml``.
  * Regression delta vs. ``evals/datasets/regression_baseline.json``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from controls import DriftDetector
from evals.runners.eval_runner import EvalRunner
from evals.runners.metrics import compute_metrics

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = yaml.safe_load((ROOT / "config" / "thresholds.yaml").read_text())
BASELINE_PATH = ROOT / "evals" / "datasets" / "regression_baseline.json"


@pytest.fixture(scope="session")
def runner() -> EvalRunner:
    return EvalRunner(dataset_dir=ROOT / "evals" / "datasets")


def _apply_operator(operator: str, value: float, threshold: float) -> bool:
    if operator == "gte":
        return value >= threshold
    if operator == "lte":
        return value <= threshold
    raise ValueError(f"Unsupported operator: {operator!r}")


@pytest.mark.parametrize("control_id", sorted(EvalRunner.DATASET_MAP.keys()))
def test_control_threshold(runner: EvalRunner, control_id: str) -> None:
    """Pass rate must satisfy the configured operator/threshold."""
    results = runner.run_for_control(control_id)
    metrics = compute_metrics(results)

    cfg = THRESHOLDS["thresholds"].get(control_id, {})
    operator = cfg.get("operator", "gte")
    value = float(cfg.get("value", 0.95))

    out_dir = ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{control_id}.json").write_text(
        json.dumps(
            {"metrics": metrics.to_dict(),
             "results": [r.to_dict() for r in results]},
            indent=2,
        )
    )

    assert _apply_operator(operator, metrics.pass_rate, value), (
        f"{control_id} pass_rate={metrics.pass_rate:.2%} fails {operator} {value:.2%}"
    )


@pytest.mark.parametrize("control_id", sorted(EvalRunner.DATASET_MAP.keys()))
def test_expected_risk_ids(runner: EvalRunner, control_id: str) -> None:
    """Every case must have ``actual_risk_ids == expected_risk_ids``."""
    results = runner.run_for_control(control_id)
    mismatches = [r for r in results if not r.risk_ids_match]
    assert not mismatches, (
        f"{control_id}: {len(mismatches)} case(s) with risk-id mismatch: "
        + ", ".join(
            f"{r.case_id} expected={r.expected_risk_ids} got={r.actual_risk_ids}"
            for r in mismatches[:5]
        )
    )


@pytest.mark.parametrize("control_id", sorted(EvalRunner.DATASET_MAP.keys()))
def test_latency_budget(runner: EvalRunner, control_id: str) -> None:
    """P50/P95/P99 latency must fit within the configured budget."""
    budget = THRESHOLDS.get("latency_budget_ms", {})
    if not budget:
        pytest.skip("No latency budget configured")

    results = runner.run_for_control(control_id)
    metrics = compute_metrics(results)

    assert metrics.latency_p50 <= float(budget["p50"]), (
        f"{control_id} p50={metrics.latency_p50:.1f}ms > {budget['p50']}ms"
    )
    assert metrics.latency_p95 <= float(budget["p95"]), (
        f"{control_id} p95={metrics.latency_p95:.1f}ms > {budget['p95']}ms"
    )
    assert metrics.latency_p99 <= float(budget["p99"]), (
        f"{control_id} p99={metrics.latency_p99:.1f}ms > {budget['p99']}ms"
    )


def test_no_drift_regression(runner: EvalRunner) -> None:
    """Current pass rates must not regress below baseline by more than delta."""
    current: dict[str, float] = {}
    for control_id in EvalRunner.DATASET_MAP:
        results = runner.run_for_control(control_id)
        metrics = compute_metrics(results)
        current[control_id] = metrics.pass_rate

    detector = DriftDetector(baseline_path=BASELINE_PATH)
    reports = detector.compare(current)
    regressions = [r for r in reports if r.regressed]
    assert not regressions, (
        "Drift regression detected: "
        + ", ".join(
            f"{r.control_id} Δ={r.delta:+.2%} (baseline={r.baseline_pass_rate:.2%})"
            for r in regressions
        )
    )
