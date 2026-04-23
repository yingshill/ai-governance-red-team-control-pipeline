"""PII detection and redaction control — addresses RISK-002."""
from __future__ import annotations

import re
from typing import Any, Final

from .base import BaseControl, ControlResult

_EMAIL: Final = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_PHONE: Final = re.compile(r"\+?\d{1,3}[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")
_SSN: Final = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CC: Final = re.compile(r"\b(?:\d[ -]?){13,16}\b")

_DETECTORS: Final = (
    ("EMAIL", _EMAIL),
    ("PHONE", _PHONE),
    ("SSN", _SSN),
    ("CREDIT_CARD", _CC),
)


class PIIFilter(BaseControl):
    """Detect PII entities in prompts/responses and redact or block them.

    Semantic convention (shared with all BaseControl subclasses):
        - ``passed=True`` means the control did **not** need to intervene.
        - ``passed=False`` means the control **did** intervene (redact, block,
          escalate, etc.). The intervening risk_ids are reported downstream.
    """

    control_id = "CTRL-002"
    description = "Detect and redact PII from model outputs"
    risk_ids = ["RISK-002"]

    def __init__(self, mode: str = "redact") -> None:
        if mode not in {"redact", "block", "flag"}:
            raise ValueError(f"Invalid PIIFilter mode: {mode!r}")
        self.mode = mode

    def evaluate(
        self,
        *,
        prompt: str,
        response: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ControlResult:
        target = response if response is not None else prompt
        hits: dict[str, list[str]] = {}
        redacted = target
        for label, pattern in _DETECTORS:
            found = pattern.findall(target)
            if found:
                hits[label] = found
                redacted = pattern.sub(f"[REDACTED_{label}]", redacted)

        if not hits:
            return ControlResult(
                passed=True,
                control_id=self.control_id,
                risk_ids=self.risk_ids,
                action="allow",
                reason="No PII detected",
            )

        if self.mode == "block":
            return ControlResult(
                passed=False,
                control_id=self.control_id,
                risk_ids=self.risk_ids,
                action="block",
                reason=f"PII detected: {sorted(hits)}",
                metadata={"entities": hits},
            )

        if self.mode == "flag":
            return ControlResult(
                passed=False,
                control_id=self.control_id,
                risk_ids=self.risk_ids,
                action="allow",
                reason=f"PII flagged (not redacted): {sorted(hits)}",
                metadata={"entities": hits},
            )

        # mode == "redact"
        return ControlResult(
            passed=False,  # intervention occurred — see class docstring
            control_id=self.control_id,
            risk_ids=self.risk_ids,
            action="redact",
            reason=f"Redacted PII entities: {sorted(hits)}",
            metadata={"entities": hits, "redacted_text": redacted},
        )
