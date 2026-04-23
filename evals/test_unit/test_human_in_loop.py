"""Unit tests for HumanInLoopTrigger (CTRL-005)."""
from __future__ import annotations

from controls import HumanInLoopTrigger


def test_high_stakes_action_escalates() -> None:
    hitl = HumanInLoopTrigger()
    result = hitl.evaluate(
        prompt="send an email",
        context={"action_type": "send_email", "reversible": False},
    )
    assert not result.passed
    assert result.action == "escalate"
    assert "RISK-005" in result.risk_ids


def test_low_stakes_action_allows() -> None:
    hitl = HumanInLoopTrigger()
    result = hitl.evaluate(
        prompt="summarize doc",
        context={"action_type": "read_only", "reversible": True},
    )
    assert result.passed
    assert result.action == "allow"


def test_missing_context_fails_closed() -> None:
    hitl = HumanInLoopTrigger()
    result = hitl.evaluate(prompt="do something")
    assert not result.passed
    assert result.action == "escalate"
