"""Jailbreak and adversarial prompt detection — addresses RISK-001.

A lightweight, pattern-based first layer. An optional second layer
(fine-tuned classifier) can be plugged in via the constructor.

The per-prompt result cache is an LRU with a bounded size so it cannot grow
unbounded in a long-running process.
"""
from __future__ import annotations

import hashlib
import re
from collections import OrderedDict
from typing import Any, Callable, Final

from ._log import get_logger
from .base import BaseControl, ControlResult

_KNOWN_PATTERNS: Final = (
    r"ignore (all |previous |your )?(instructions|prompt|system)",
    r"you are now (DAN|a different|an unrestricted)",
    r"pretend (you have no|you are not|there are no) (restrictions|limits|rules)",
    r"developer mode",
    r"\bjailbreak\b",
    r"act as (?!a helpful)",
)

_logger = get_logger("controls.jailbreak")


class JailbreakDetector(BaseControl):
    """Pattern-first jailbreak detector with an optional plug-in classifier."""

    control_id = "CTRL-003"
    description = "Multi-layer jailbreak detection: patterns + optional classifier"
    risk_ids = ["RISK-001"]

    DEFAULT_CACHE_SIZE: Final = 4096

    def __init__(
        self,
        classifier: Callable[[str], tuple[str, float]] | None = None,
        classifier_threshold: float = 0.90,
        cache_size: int = DEFAULT_CACHE_SIZE,
    ) -> None:
        """Configure the detector.

        Args:
            classifier: Optional callable returning ``(label, score)`` given a
                prompt. When ``label == "INJECTION"`` and ``score >= threshold``,
                the prompt is blocked.
            classifier_threshold: Minimum classifier score for a block.
            cache_size: Maximum number of prompt hashes kept in the LRU cache.
        """
        self._patterns = [re.compile(p, re.IGNORECASE) for p in _KNOWN_PATTERNS]
        self._classifier = classifier
        self._threshold = classifier_threshold
        self._cache: OrderedDict[str, ControlResult] = OrderedDict()
        self._cache_size = cache_size

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def _cache_get(self, key: str) -> ControlResult | None:
        result = self._cache.get(key)
        if result is not None:
            self._cache.move_to_end(key)
        return result

    def _cache_put(self, key: str, value: ControlResult) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    def evaluate(
        self,
        *,
        prompt: str,
        response: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ControlResult:
        """Evaluate a prompt for jailbreak indicators."""
        key = self._key(prompt)
        cached = self._cache_get(key)
        if cached is not None:
            return cached

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
                self._cache_put(key, result)
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
                    self._cache_put(key, result)
                    return result
            except Exception as exc:  # noqa: BLE001 — fail closed on classifier error
                _logger.exception("classifier_error")
                result = ControlResult(
                    passed=False,
                    control_id=self.control_id,
                    risk_ids=self.risk_ids,
                    action="block",
                    reason=f"Classifier error — failing closed: {exc}",
                    confidence=0.0,
                )
                self._cache_put(key, result)
                return result

        result = ControlResult(
            passed=True,
            control_id=self.control_id,
            risk_ids=self.risk_ids,
            action="allow",
            reason="No jailbreak indicators detected",
        )
        self._cache_put(key, result)
        return result
