"""Jailbreak and adversarial prompt detection — addresses RISK-001.

This is a lightweight, pattern-based first layer. A second optional layer
(e.g. a fine-tuned classifier) can be plugged in via :class:`JailbreakDetector`
constructor.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Callable, Final

from .base import BaseControl, ControlResult

_KNOWN_PATTERNS: Final = (
    r"ignore (all |previous |your )?(instructions|prompt|system)",
    r"you are now (DAN|a different|an unrestricted)",
    r"pretend (you have no|you are not|there are no) (restrictions|limits|rules)",
    r"developer mode",
    r"\bjailbreak\b",
    r"act as (?!a helpful)",
)


class JailbreakDetector(BaseControl):
    control_id = "CTRL-003"
    description = "Multi-layer jailbreak detection: patterns + optional classifier"
    risk_ids = ["RISK-001"]

    def __init__(
        self,
        classifier: Callable[[str], tuple[str, float]] | None = None,
        classifier_threshold: float = 0.90,
    ) -> None:
        self._patterns = [re.compile(p, re.IGNORECASE) for p in _KNOWN_PATTERNS]
        self._classifier = classifier
        self._threshold = classifier_threshold
        self._cache: dict[str, ControlResult] = {}

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def evaluate(
        self,
        *,
        prompt: str,
        response: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ControlResult:
        key = self._key(prompt)
        if key in self._cache:
            return self._cache[key]

        for pattern in self._patterns:
            if pattern.search(prompt):
                result = ControlResult(
                    passed=False,
                    control_id=self.control_id,
                    risk_ids=self.risk_ids,
                    action="block",
                    reason=f"Matched adversarial pattern: {pattern.pattern}",
                    confidence=1.0,
                )
                self._cache[key] = result
                return result

        if self._classifier is not None:
            try:
                label, score = self._classifier(prompt[:512])
                if label.upper() == "INJECTION" and score >= self._threshold:
                    result = ControlResult(
                        passed=False,
                        control_id=self.control_id,
                        risk_ids=self.risk_ids,
                        action="block",
                        reason="Classifier flagged prompt as injection attempt",
                        metadata={"score": score},
                        confidence=score,
                    )
                    self._cache[key] = result
                    return result
            except Exception as exc:  # noqa: BLE001 — fail closed on classifier error
                result = ControlResult(
                    passed=False,
                    control_id=self.control_id,
                    risk_ids=self.risk_ids,
                    action="block",
                    reason=f"Classifier error — failing closed: {exc}",
                    confidence=0.0,
                )
                self._cache[key] = result
                return result

        result = ControlResult(
            passed=True,
            control_id=self.control_id,
            risk_ids=self.risk_ids,
            action="allow",
            reason="No jailbreak indicators detected",
        )
        self._cache[key] = result
        return result
