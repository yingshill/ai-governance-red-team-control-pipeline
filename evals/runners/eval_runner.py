"""Core evaluation orchestrator — runs controls against JSONL datasets."""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

from controls._log import get_logger
from controls.registry import ControlRegistry

_logger = get_logger("evals.runner")


@dataclass
class EvalCase:
    """One line from a JSONL dataset."""

    case_id: str
    prompt: str
    response: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    expected_action: str = "allow"
    expected_risk_ids: list[str] = field(default_factory=list)


@dataclass
class EvalResult:
    """Result of applying one control to one case."""

    case_id: str
    control_id: str
    passed: bool
    actual_action: str
    expected_action: str
    actual_risk_ids: list[str]
    expected_risk_ids: list[str]
    risk_ids_match: bool
    latency_ms: float
    confidence: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable view."""
        return asdict(self)


class EvalRunner:
    """Run one or more JSONL datasets through the control registry."""

    DATASET_MAP: dict[str, str] = {
        "CTRL-002": "pii_cases.jsonl",
        "CTRL-003": "jailbreak_cases.jsonl",
        "CTRL-004": "citation_cases.jsonl",
        "CTRL-005": "hitl_trigger_cases.jsonl",
    }

    def __init__(
        self,
        dataset_dir: str | Path = "evals/datasets",
        registry: ControlRegistry | None = None,
    ) -> None:
        """Initialize the runner with a dataset directory and control registry."""
        self.dataset_dir = Path(dataset_dir)
        self.registry = registry or ControlRegistry.load_default()

    def load_dataset(self, filename: str) -> Iterator[EvalCase]:
        """Yield ``EvalCase`` objects from a JSONL file."""
        path = self.dataset_dir / filename
        with path.open() as fh:
            for line_no, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield EvalCase(**json.loads(line))
                except (TypeError, json.JSONDecodeError) as exc:
                    raise ValueError(
                        f"Invalid case at {path}:{line_no}: {exc}"
                    ) from exc

    def run_for_control(self, control_id: str) -> list[EvalResult]:
        """Run a single control against its configured dataset."""
        dataset = self.DATASET_MAP.get(control_id)
        if dataset is None:
            raise KeyError(f"No dataset mapped for control {control_id!r}")
        controls = self.registry.get([control_id])
        if not controls:
            raise KeyError(f"Control {control_id!r} not in registry")
        control = controls[0]

        results: list[EvalResult] = []
        for case in self.load_dataset(dataset):
            start = time.perf_counter()
            outcome = (
                control.post_inference(case.prompt, case.response, case.context)
                if case.response
                else control.pre_inference(case.prompt, case.context)
            )
            latency_ms = (time.perf_counter() - start) * 1000
            actual_risk_ids = outcome.risk_ids if not outcome.passed else []
            risk_ids_match = (
                sorted(actual_risk_ids) == sorted(case.expected_risk_ids)
            )
            results.append(
                EvalResult(
                    case_id=case.case_id,
                    control_id=control.control_id,
                    passed=outcome.action == case.expected_action,
                    actual_action=outcome.action,
                    expected_action=case.expected_action,
                    actual_risk_ids=actual_risk_ids,
                    expected_risk_ids=case.expected_risk_ids,
                    risk_ids_match=risk_ids_match,
                    latency_ms=latency_ms,
                    confidence=outcome.confidence,
                    reason=outcome.reason,
                )
            )
        _logger.info(
            json.dumps(
                {"event": "control_eval", "control_id": control_id,
                 "cases": len(results)}
            )
        )
        return results
