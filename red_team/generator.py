"""Red team dataset amplification engine.

Takes a seed set of AttackCases and produces an amplified dataset by
applying one or more mutations per case. Output is deterministic given
the RNG seed, and expected actions / risk IDs carry through unchanged.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from controls._log import get_logger

from . import mutations

_logger = get_logger("red_team.generator")


@dataclass
class AttackCase:
    """A single adversarial test case, seed or mutated."""

    case_id: str
    prompt: str
    expected_action: str
    expected_risk_ids: list[str]
    category: str | None = None
    mutations: list[str] = field(default_factory=list)
    source_case_id: str | None = None

    @classmethod
    def from_jsonl_row(cls, row: dict[str, Any]) -> "AttackCase":
        return cls(
            case_id=row["case_id"],
            prompt=row["prompt"],
            expected_action=row.get("expected_action", "allow"),
            expected_risk_ids=list(row.get("expected_risk_ids", [])),
            category=row.get("category"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "prompt": self.prompt,
            "expected_action": self.expected_action,
            "expected_risk_ids": self.expected_risk_ids,
            "category": self.category,
            "mutations": self.mutations,
            "source_case_id": self.source_case_id,
        }


class RedTeamGenerator:
    """Amplify seed cases into a larger adversarial corpus.

    Determinism: identical (seed, seeds, mutation_set, max_compound)
    produce identical output.
    """

    DEFAULT_MUTATIONS: tuple[str, ...] = (
        "paraphrase",
        "prefix_inject",
        "suffix_inject",
        "case_scramble",
        "unicode_homoglyph",
        "base64_wrap",
    )

    def __init__(
        self,
        seed: int = 42,
        mutations_to_use: Iterable[str] = DEFAULT_MUTATIONS,
        max_compound: int = 2,
    ) -> None:
        """Configure the generator.

        Args:
            seed: RNG seed for determinism.
            mutations_to_use: names of mutations to draw from.
            max_compound: maximum number of mutations stacked per variant.
        """
        self._rng = random.Random(seed)
        self._names = list(mutations_to_use)
        for name in self._names:
            if name not in mutations.REGISTRY:
                raise ValueError(f"Unknown mutation: {name!r}")
        self._max_compound = max(1, max_compound)

    def amplify_case(self, seed_case: AttackCase, n: int) -> list[AttackCase]:
        """Produce ``n`` mutated variants of a single seed case."""
        variants: list[AttackCase] = []
        for i in range(n):
            k = self._rng.randint(1, self._max_compound)
            chosen = self._rng.sample(self._names, min(k, len(self._names)))
            prompt = seed_case.prompt
            for name in chosen:
                prompt = mutations.apply(name, prompt, self._rng)
            variants.append(
                AttackCase(
                    case_id=f"{seed_case.case_id}.mut.{i + 1:03d}",
                    prompt=prompt,
                    expected_action=seed_case.expected_action,
                    expected_risk_ids=list(seed_case.expected_risk_ids),
                    category=seed_case.category,
                    mutations=list(chosen),
                    source_case_id=seed_case.case_id,
                )
            )
        return variants

    def amplify_file(
        self,
        seed_path: Path,
        out_path: Path,
        n_per_seed: int,
    ) -> int:
        """Amplify a JSONL file in place. Returns the number of cases written."""
        seeds = [
            AttackCase.from_jsonl_row(json.loads(line))
            for line in seed_path.read_text().splitlines()
            if line.strip()
        ]
        total = 0
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as f:
            for seed_case in seeds:
                for variant in self.amplify_case(seed_case, n_per_seed):
                    f.write(json.dumps(variant.to_dict()) + "\n")
                    total += 1
        _logger.info(
            json.dumps(
                {
                    "event": "amplified",
                    "seed_path": str(seed_path),
                    "out_path": str(out_path),
                    "seeds": len(seeds),
                    "n_per_seed": n_per_seed,
                    "total": total,
                }
            )
        )
        return total
