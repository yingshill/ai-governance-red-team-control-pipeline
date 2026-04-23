"""Citation enforcement control — addresses RISK-003.

When ``context['require_citations']`` is true, the response MUST contain at
least one citation-like token (``[^...]`` footnote, URL, or ``(Source: ...)``).
"""
from __future__ import annotations

import re
from typing import Any, Final

from .base import BaseControl, ControlResult

_CITATION: Final = re.compile(
    r"\[\^[^\]]+\]|https?://\S+|\(Source:\s.+?\)",
    re.IGNORECASE,
)


class CitationEnforcer(BaseControl):
    control_id = "CTRL-004"
    description = "Require citations for claims in high-stakes contexts"
    risk_ids = ["RISK-003"]

    def evaluate(
        self,
        *,
        prompt: str,
        response: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ControlResult:
        context = context or {}
        response = response or ""
        if not context.get("require_citations", False):
            return ControlResult(
                passed=True,
                control_id=self.control_id,
                risk_ids=self.risk_ids,
                action="allow",
                reason="Citations not required for this request",
            )

        if _CITATION.search(response):
            return ControlResult(
                passed=True,
                control_id=self.control_id,
                risk_ids=self.risk_ids,
                action="allow",
                reason="Citations present",
            )

        return ControlResult(
            passed=False,
            control_id=self.control_id,
            risk_ids=self.risk_ids,
            action="block",
            reason="Response is missing required citations",
        )
