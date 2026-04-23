"""Abstract base interface for all safety controls.

All controls are pure functions of ``(prompt, response, context)``. They MUST
be deterministic given the same inputs and MUST NOT raise exceptions on the
happy path — wrap fallible logic and fail closed (``action="block"``).
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

from ._log import get_logger

Action = Literal["allow", "block", "redact", "escalate"]

_logger = get_logger("controls.base")


@dataclass
class ControlResult:
    """Outcome of a control evaluation.

    Attributes:
        passed: ``True`` if the control did not need to intervene.
        control_id: Stable identifier, e.g. ``"CTRL-002"``.
        risk_ids: Risk register IDs this control addresses.
        action: One of ``allow | block | redact | escalate``.
        reason: Human-readable explanation (used in logs + PR comments).
        metadata: Optional structured payload (e.g. redacted text, scores).
        confidence: 0.0–1.0 detector confidence.
    """

    passed: bool
    control_id: str
    risk_ids: list[str]
    action: Action
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


class BaseControl(ABC):
    """Abstract base class for all safety controls."""

    control_id: str
    description: str
    risk_ids: list[str]

    @abstractmethod
    def evaluate(
        self,
        *,
        prompt: str,
        response: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ControlResult:
        """Evaluate a prompt/response pair. Called pre- and/or post-inference."""

    def pre_inference(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> ControlResult:
        """Run before calling the model. Typically blocks dangerous prompts."""
        result = self.evaluate(prompt=prompt, context=context)
        self._emit(result, phase="pre")
        return result

    def post_inference(
        self, prompt: str, response: str, context: dict[str, Any] | None = None
    ) -> ControlResult:
        """Run after calling the model. Typically redacts or blocks outputs."""
        result = self.evaluate(prompt=prompt, response=response, context=context)
        self._emit(result, phase="post")
        return result

    def _emit(self, result: ControlResult, *, phase: str) -> None:
        payload = {
            "phase": phase,
            "control_id": result.control_id,
            "risk_ids": result.risk_ids,
            "action": result.action,
            "passed": result.passed,
            "confidence": result.confidence,
        }
        level = "info" if result.passed else "warning"
        getattr(_logger, level)(json.dumps(payload))
