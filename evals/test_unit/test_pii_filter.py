"""Unit tests for PIIFilter (CTRL-002)."""
from __future__ import annotations

import pytest

from controls import PIIFilter


@pytest.fixture
def pii() -> PIIFilter:
    return PIIFilter()


@pytest.mark.parametrize(
    "text,expected_type",
    [
        ("Contact me at alice@example.com", "EMAIL"),
        ("Call (555) 123-4567", "PHONE"),
        ("SSN: 123-45-6789", "SSN"),
        ("Card: 4111-1111-1111-1111", "CREDIT_CARD"),
    ],
)
def test_detects_pii_types(pii: PIIFilter, text: str, expected_type: str) -> None:
    result = pii.evaluate(prompt="user", response=text)
    assert not result.passed
    assert result.action == "redact"
    assert "RISK-002" in result.risk_ids
    assert expected_type in result.metadata.get("types", [])


def test_clean_response_passes(pii: PIIFilter) -> None:
    result = pii.evaluate(prompt="user", response="The launch is scheduled next week.")
    assert result.passed
    assert result.action == "allow"


def test_empty_response_passes(pii: PIIFilter) -> None:
    result = pii.evaluate(prompt="user", response="")
    assert result.passed


def test_redacted_text_in_metadata(pii: PIIFilter) -> None:
    result = pii.evaluate(prompt="user", response="Reach out to bob@corp.io please")
    assert "redacted" in result.metadata
    assert "bob@corp.io" not in result.metadata["redacted"]
