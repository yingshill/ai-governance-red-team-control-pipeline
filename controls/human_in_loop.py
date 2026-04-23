"""Human-in-the-loop trigger logic — addresses RISK-005."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .base import BaseControl, ControlResult


@dataclass
class HITLPolicy:
    """Configuration for when to escalate to a human reviewer."""

    action_patterns: list[str] = field(
        default_factory=lambda: [
            r"send (email|message|notification)",
            r"(delete|remove|drop) (database|table|record|user)",
            r"(transfer|pay|charge|refund) \$?[\d,]+",
            r"deploy|rollout|release to production",
            r"(create|modify|revoke) (api key|credential|permission|access)",
        ]
    )
    context_keywords: list[str] = field(
        default_factory=lambda: ["medical", "legal", "financial", "hipaa", "gdpr", "phi"]
    )
    confidence_threshold: float = 0.75
    max_cost_usd: float = 100.0


class HumanInLoopTrigger(BaseControl):
    control_id = "CTRL-005"
    description = "Trigger human review for high-stakes agentic actions"
    risk_ids = ["RISK-005"]

    def __init__(self, policy: HITLPolicy | None = None) -> None:
        self.policy = policy or HITLPolicy()
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.policy.action_patterns]

    def evaluate(
        self,
        *,
        prompt: str,
        response: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ControlResult:
        context = context or {}
        reasons: list[str] = []
        target = f"{response or ''} {prompt}"

        for pattern in self._compiled:
            if pattern.search(target):
                reasons.append(f"High-risk action pattern: {pattern.pattern}")

        lower = target.lower()
        for kw in self.policy.context_keywords:
            if kw.lower() in lower:
                reasons.append(f"Sensitive domain keyword: {kw}")

        model_conf = float(context.get("model_confidence", 1.0))
        if model_conf < self.policy.confidence_threshold:
            reasons.append(f"Low model confidence: {model_conf:.2f}")

        cost = float(context.get("estimated_cost_usd", 0.0))
        if cost > self.policy.max_cost_usd:
            reasons.append(f"Cost exceeds threshold: ${cost:.2f}")

        if reasons:
            return ControlResult(
                passed=False,
                control_id=self.control_id,
                risk_ids=self.risk_ids,
                action="escalate",
                reason=" | ".join(reasons),
                metadata={"hitl_reasons": reasons, "context": context},
            )

        return ControlResult(
            passed=True,
            control_id=self.control_id,
            risk_ids=self.risk_ids,
            action="allow",
            reason="No HITL triggers activated",
        )
