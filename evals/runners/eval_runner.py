"""Core evaluation orchestrator — runs controls against JSONL datasets."""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator

from controls.registry import ControlRegistry


@dataclass
class EvalCase:
    case_id: str
    prompt: str
    response: str = ""
    context: dict = field(default_factory=dict)
    expected_action: str = "allow"
    expected_risk_ids: list[str] = field(default_factory=list)


@dataclass
class EvalResult:
    case_id: str
    control_id: str
    passed: bool
    actual_action: str
    expected_action: str
    latency_ms: float
    confidence: float
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


class EvalRunner:
    """Run one or more JSONL datasets through the control registry.

    Mapping from control_id -> dataset file lives in :attr:`DATASET_MAP`.
    """

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
        self.dataset_dir = Path(dataset_dir)
        self.registry = registry or ControlRegistry.load_default()

    def load_dataset(self, filename: str) -> Iterator[EvalCase]:
        path = self.dataset_dir / filename
        with path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                yield EvalCase(**json.loads(line))

    def run_for_control(self, control_id: str) -> list[EvalResult]:
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
            results.append(
                EvalResult(
                    case_id=case.case_id,
                    control_id=control.control_id,
                    passed=outcome.action == case.expected_action,
                    actual_action=outcome.action,
                    expected_action=case.expected_action,
                    latency_ms=latency_ms,
                    confidence=outcome.confidence,
                    reason=outcome.reason,
                )
            )
        return results

    def run_all(self) -> dict[str, list[EvalResult]]:
        return {cid: self.run_for_control(cid) for cid in self.DATASET_MAP}
