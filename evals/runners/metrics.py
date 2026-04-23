"""Aggregate metrics across a list of EvalResults."""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Iterable

from .eval_runner import EvalResult


@dataclass
class SafetyMetrics:
    """Aggregated metrics for one control over a dataset."""

    control_id: str
    total: int
    passed: int
    pass_rate: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    risk_id_match_rate: float = 0.0
    by_action: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """JSON-serializable view."""
        return {
            "control_id": self.control_id,
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "latency_p50": self.latency_p50,
            "latency_p95": self.latency_p95,
            "latency_p99": self.latency_p99,
            "risk_id_match_rate": self.risk_id_match_rate,
            "by_action": dict(self.by_action),
        }


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = max(0, min(len(values) - 1, int(round((pct / 100) * (len(values) - 1)))))
    return values[k]


def compute_metrics(results: Iterable[EvalResult]) -> SafetyMetrics:
    """Compute aggregated metrics for a list of EvalResults."""
    results = list(results)
    if not results:
        return SafetyMetrics("", 0, 0, 0.0, 0.0, 0.0, 0.0)

    control_id = results[0].control_id
    passed = sum(1 for r in results if r.passed)
    latencies = [r.latency_ms for r in results]
    risk_matches = sum(1 for r in results if r.risk_ids_match)

    by_action: dict[str, int] = {}
    for r in results:
        by_action[r.actual_action] = by_action.get(r.actual_action, 0) + 1

    return SafetyMetrics(
        control_id=control_id,
        total=len(results),
        passed=passed,
        pass_rate=passed / len(results),
        latency_p50=statistics.median(latencies),
        latency_p95=_percentile(latencies, 95),
        latency_p99=_percentile(latencies, 99),
        risk_id_match_rate=risk_matches / len(results),
        by_action=by_action,
    )
