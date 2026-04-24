"""Attack taxonomy and OWASP LLM Top 10 (2025) mapping.

Each AttackCategory maps to:
- One or more OWASP LLM Top 10 (2025) entries
- One or more RISK-* IDs from the project's risk register
- A default expected_action for the control under attack

These categories are the coordinate system red-team generators operate in:
every mutation produces output cases labeled with one category, which
anchors them to both an external framework (OWASP) and the internal
risk register (RISK-*).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OwaspLLMCategory(str, Enum):
    """Subset of the OWASP LLM Top 10 (2025) relevant to this project."""

    LLM01_PROMPT_INJECTION = "LLM01:2025 Prompt Injection"
    LLM02_SENSITIVE_DISCLOSURE = "LLM02:2025 Sensitive Information Disclosure"
    LLM05_IMPROPER_OUTPUT = "LLM05:2025 Improper Output Handling"
    LLM06_EXCESSIVE_AGENCY = "LLM06:2025 Excessive Agency"
    LLM07_SYSTEM_PROMPT_LEAK = "LLM07:2025 System Prompt Leakage"
    LLM09_MISINFORMATION = "LLM09:2025 Misinformation"


@dataclass(frozen=True)
class AttackCategory:
    """Metadata describing one class of adversarial attack."""

    name: str
    description: str
    owasp: tuple[OwaspLLMCategory, ...]
    risk_ids: tuple[str, ...]
    default_expected_action: str  # allow | block | redact | escalate


CATEGORIES: dict[str, AttackCategory] = {
    "prompt_injection": AttackCategory(
        name="Prompt Injection",
        description="Override system instructions via user-supplied content.",
        owasp=(
            OwaspLLMCategory.LLM01_PROMPT_INJECTION,
            OwaspLLMCategory.LLM07_SYSTEM_PROMPT_LEAK,
        ),
        risk_ids=("RISK-001",),
        default_expected_action="block",
    ),
    "pii_extraction": AttackCategory(
        name="PII Extraction",
        description="Solicit or leak personally identifiable information.",
        owasp=(OwaspLLMCategory.LLM02_SENSITIVE_DISCLOSURE,),
        risk_ids=("RISK-002",),
        default_expected_action="redact",
    ),
    "hallucinated_citation": AttackCategory(
        name="Hallucinated Citation",
        description="Elicit factual claims without sourceable evidence.",
        owasp=(
            OwaspLLMCategory.LLM09_MISINFORMATION,
            OwaspLLMCategory.LLM05_IMPROPER_OUTPUT,
        ),
        risk_ids=("RISK-003",),
        default_expected_action="block",
    ),
    "excessive_agency": AttackCategory(
        name="Excessive Agency",
        description="Trigger irreversible high-stakes action without HITL.",
        owasp=(OwaspLLMCategory.LLM06_EXCESSIVE_AGENCY,),
        risk_ids=("RISK-005",),
        default_expected_action="escalate",
    ),
}
