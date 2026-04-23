"""Aggregate metrics across a list of EvalResults."""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Iterable

from .eval_runner import EvalResult


@dataclass
class SafetyMetrics:
    control_id: str
    total: int
    passed: int
    pass_rate: float
    latency_p50: float
    latency_p95: float
    latency_p99: float


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = max(0, min(len(values) - 1, int(round((pct / 100) * (len(values) - 1)))))
    return values[k]


def compute_metrics(results: Iterable[EvalResult]) -> SafetyMetrics:
    results = list(results)
    if not results:
        return SafetyMetrics("", 0, 0, 0.0, 0.0, 0.0, 0.0)

    control_id = results[0].control_id
    passed = sum(1 for r in results if r.passed)
    latencies = [r.latency_ms for r in results]

    return SafetyMetrics(
        control_id=control_id,
        total=len(results),
        passed=passed,
        pass_rate=passed / len(results),
        latency_p50=statistics.median(latencies),
        latency_p95=_percentile(latencies, 95),
        latency_p99=_percentile(latencies, 99),
    )
