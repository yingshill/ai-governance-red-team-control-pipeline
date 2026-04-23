"""Unit tests for CitationEnforcer (CTRL-004)."""
from __future__ import annotations

from controls import CitationEnforcer


def test_response_with_citation_passes() -> None:
    enforcer = CitationEnforcer()
    result = enforcer.evaluate(
        prompt="research question",
        response="The study found X [^smith2024].",
        context={"requires_citation": True},
    )
    assert result.passed


def test_response_with_url_passes() -> None:
    enforcer = CitationEnforcer()
    result = enforcer.evaluate(
        prompt="q",
        response="See https://example.com/source for details.",
        context={"requires_citation": True},
    )
    assert result.passed


def test_uncited_claim_blocks() -> None:
    enforcer = CitationEnforcer()
    result = enforcer.evaluate(
        prompt="q",
        response="The answer is definitely 42.",
        context={"requires_citation": True},
    )
    assert not result.passed
    assert result.action == "block"
    assert "RISK-003" in result.risk_ids


def test_citation_not_required_allows() -> None:
    enforcer = CitationEnforcer()
    result = enforcer.evaluate(
        prompt="q",
        response="casual reply",
        context={"requires_citation": False},
    )
    assert result.passed
