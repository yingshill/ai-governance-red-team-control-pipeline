"""Pytest suite that runs every control against its dataset and asserts pass rate.

Thresholds are loaded from ``config/thresholds.yaml``; each control must meet
its configured minimum pass rate or the suite fails the CI safety gate.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from evals.runners.eval_runner import EvalRunner
from evals.runners.metrics import compute_metrics

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = yaml.safe_load((ROOT / "config" / "thresholds.yaml").read_text())


@pytest.fixture(scope="session")
def runner() -> EvalRunner:
    return EvalRunner(dataset_dir=ROOT / "evals" / "datasets")


@pytest.mark.parametrize("control_id", sorted(EvalRunner.DATASET_MAP.keys()))
def test_control_pass_rate(runner: EvalRunner, control_id: str) -> None:
    results = runner.run_for_control(control_id)
    metrics = compute_metrics(results)

    threshold_cfg = THRESHOLDS["thresholds"].get(control_id, {})
    min_pass_rate = float(threshold_cfg.get("value", 0.95))

    # Write per-control JSON for the gate script + report generator.
    out_dir = ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{control_id}.json").write_text(
        json.dumps(
            {"metrics": metrics.__dict__, "results": [r.to_dict() for r in results]},
            indent=2,
        )
    )

    assert metrics.pass_rate >= min_pass_rate, (
        f"{control_id} pass rate {metrics.pass_rate:.2%} below threshold {min_pass_rate:.2%}"
    )
