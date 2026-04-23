"""Behavioral drift detector — addresses RISK-004.

Compares the current run's per-control pass rates against a stored baseline
(``evals/datasets/regression_baseline.json``). If any control regresses by
more than the configured ``regression_delta``, the control is flagged.

This is a detective control: it does not block individual requests, it is
invoked offline by the eval runner / CI gate.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ._log import get_logger
from .base import BaseControl, ControlResult

_logger = get_logger("controls.drift")


@dataclass
class DriftReport:
    """Per-control drift finding."""

    control_id: str
    baseline_pass_rate: float
    current_pass_rate: float
    delta: float
    regressed: bool


class DriftDetector(BaseControl):
    """Compare current metrics to a stored baseline and flag regressions."""

    control_id = "CTRL-006"
    description = "Detect behavioral drift vs. regression baseline"
    risk_ids = ["RISK-004"]

    DEFAULT_BASELINE = Path("evals/datasets/regression_baseline.json")

    def __init__(
        self,
        baseline_path: Path | str = DEFAULT_BASELINE,
        regression_delta: float = -0.02,
    ) -> None:
        """Configure the drift detector.

        Args:
            baseline_path: JSON file mapping ``control_id -> {"pass_rate":...}``.
            regression_delta: Maximum allowed drop (negative number). If the
                current pass rate is below baseline + delta, drift is flagged.
        """
        self.baseline_path = Path(baseline_path)
        self.regression_delta = regression_delta

    def load_baseline(self) -> dict[str, float]:
        """Load ``control_id -> pass_rate`` mapping from the baseline file."""
        if not self.baseline_path.exists():
            _logger.warning(json.dumps({"event": "baseline_missing",
                                        "path": str(self.baseline_path)}))
            return {}
        data = json.loads(self.baseline_path.read_text())
        return {cid: float(entry["pass_rate"]) for cid, entry in data.items()}

    def compare(self, current: Mapping[str, float]) -> list[DriftReport]:
        """Compare current pass rates against baseline. Returns per-control reports."""
        baseline = self.load_baseline()
        reports: list[DriftReport] = []
        for cid, curr in current.items():
            base = baseline.get(cid)
            if base is None:
                continue
            delta = curr - base
            regressed = delta < self.regression_delta
            reports.append(
                DriftReport(
                    control_id=cid,
                    baseline_pass_rate=base,
                    current_pass_rate=curr,
                    delta=delta,
                    regressed=regressed,
                )
            )
            if regressed:
                _logger.warning(
                    json.dumps(
                        {
                            "event": "drift_regression",
                            "control_id": cid,
                            "delta": delta,
                            "baseline": base,
                            "current": curr,
                        }
                    )
                )
        return reports

    def evaluate(
        self,
        *,
        prompt: str,
        response: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ControlResult:
        """Not used at request time; drift is computed at eval time via ``compare``."""
        return ControlResult(
            passed=True,
            control_id=self.control_id,
            risk_ids=self.risk_ids,
            action="allow",
            reason="Drift detector is evaluated at release time, not per-request",
        )
