"""Amplified coverage runner — measures control robustness under red-team mutations.

This runner is deliberately **non-blocking**: it produces a coverage report,
never a pass/fail verdict. Its purpose is to surface gaps honestly — which
mutation classes evade which controls — so that remediation can be
prioritized. Coverage regressions should be reviewed, not auto-blocked.

Scope (v1):
- CTRL-003 JailbreakDetector ← jailbreak_cases.jsonl (prompt mutations)
- CTRL-005 HumanInLoopTrigger ← hitl_trigger_cases.jsonl (prompt mutations)

Deferred (roadmap in docs/RED_TEAM.md):
- CTRL-002 PIIFilter     — operates on model responses; needs response mutations
- CTRL-004 CitationEnforcer — operates on model responses; needs citation mutations
- CTRL-006 DriftDetector — operates on aggregate statistics; needs drift mutations
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from controls._log import get_logger
from controls.registry import ControlRegistry
from red_team.generator import AttackCase, RedTeamGenerator

_logger = get_logger("evals.amplified_coverage")


# Controls whose seed cases are text prompts amenable to mutation-based
# amplification. See module docstring for deferred controls.
AMPLIFIABLE_CONTROLS: dict[str, str] = {
    "CTRL-003": "jailbreak_cases.jsonl",
    "CTRL-005": "hitl_trigger_cases.jsonl",
}


@dataclass
class MutationBreakdown:
    """Per-mutation aggregated results for one control."""

    mutation: str
    n_cases: int
    n_matched: int
    match_rate: float


@dataclass
class ControlCoverage:
    """Coverage metrics for one control against its amplified dataset."""

    control_id: str
    dataset: str
    n_seeds: int
    n_amplified: int
    n_matched: int
    match_rate: float
    by_mutation: list[MutationBreakdown]
    weakest_mutations: list[str]


@dataclass
class CoverageReport:
    """Full coverage report for one amplified-coverage run."""

    run_id: str
    rng_seed: int
    n_per_seed: int
    overall_match_rate: float
    controls: list[ControlCoverage]

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable view."""
        return asdict(self)

    def to_markdown(self) -> str:
        """Render a human-readable markdown summary."""
        lines: list[str] = [
            "# Amplified Coverage Report",
            "",
            f"- **Run:** `{self.run_id}`",
            f"- **RNG seed:** `{self.rng_seed}`",
            f"- **Variants per seed:** `{self.n_per_seed}`",
            f"- **Overall match rate:** `{self.overall_match_rate:.1%}`",
            "",
            (
                "> **Match rate** = % of amplified cases where the control's "
                "action matched the seed's expected action. Lower values "
                "indicate mutation classes the control fails to catch — "
                "these are honest coverage gaps, surfaced as data, not CI "
                "failures."
            ),
            "",
            "## Per-control coverage",
            "",
            "| Control | Seeds | Amplified | Matched | Match rate | Weakest mutations |",
            "|---|---:|---:|---:|---:|---|",
        ]
        for c in self.controls:
            weakest = ", ".join(f"`{m}`" for m in c.weakest_mutations) or "—"
            lines.append(
                f"| `{c.control_id}` | {c.n_seeds} | {c.n_amplified} | "
                f"{c.n_matched} | {c.match_rate:.1%} | {weakest} |"
            )
        lines.extend(["", "## Mutation-level breakdown", ""])
        for c in self.controls:
            lines.extend(
                [
                    f"### `{c.control_id}` ({c.dataset})",
                    "",
                    "| Mutation | Cases | Matched | Match rate |",
                    "|---|---:|---:|---:|",
                ]
            )
            for m in c.by_mutation:
                lines.append(
                    f"| `{m.mutation}` | {m.n_cases} | {m.n_matched} | "
                    f"{m.match_rate:.1%} |"
                )
            lines.append("")
        return "\n".join(lines) + "\n"


class AmplifiedCoverageRunner:
    """Amplify seed datasets, run through controls, aggregate coverage metrics."""

    def __init__(
        self,
        dataset_dir: str | Path = "evals/datasets",
        n_per_seed: int = 20,
        rng_seed: int = 42,
        registry: ControlRegistry | None = None,
    ) -> None:
        """Configure the runner.

        Args:
            dataset_dir: directory containing seed JSONL files.
            n_per_seed: number of amplified variants per seed case.
            rng_seed: RNG seed for deterministic output.
            registry: optional pre-built ControlRegistry.
        """
        self.dataset_dir = Path(dataset_dir)
        self.n_per_seed = n_per_seed
        self.rng_seed = rng_seed
        self.registry = registry or ControlRegistry.load_default()

    def _load_seeds(self, filename: str) -> list[AttackCase]:
        path = self.dataset_dir / filename
        with path.open() as fh:
            return [
                AttackCase.from_jsonl_row(json.loads(line))
                for line in fh
                if line.strip()
            ]

    def _amplify(self, seeds: list[AttackCase]) -> list[AttackCase]:
        """Produce amplified cases deterministically given self.rng_seed."""
        generator = RedTeamGenerator(seed=self.rng_seed)
        out: list[AttackCase] = []
        for seed in seeds:
            out.extend(generator.amplify_case(seed, self.n_per_seed))
        return out

    def _eval_control(self, control_id: str, dataset: str) -> ControlCoverage:
        seeds = self._load_seeds(dataset)
        amplified = self._amplify(seeds)

        controls = self.registry.get([control_id])
        if not controls:
            raise KeyError(f"Control {control_id!r} not in registry")
        control = controls[0]

        # Aggregate per *primary* mutation (first applied). Compound combinations
        # fold into their leading mutation for readability.
        buckets: dict[str, list[bool]] = defaultdict(list)
        total_matched = 0
        for case in amplified:
            outcome = control.pre_inference(case.prompt, {})
            matched = outcome.action == case.expected_action
            total_matched += int(matched)
            primary = case.mutations[0] if case.mutations else "none"
            buckets[primary].append(matched)

        breakdowns = [
            MutationBreakdown(
                mutation=name,
                n_cases=len(results),
                n_matched=sum(results),
                match_rate=sum(results) / len(results) if results else 0.0,
            )
            for name, results in sorted(buckets.items())
        ]
        # Weakest = lowest match rate; ties broken by larger sample size (more signal).
        weakest = [
            b.mutation
            for b in sorted(
                breakdowns, key=lambda b: (b.match_rate, -b.n_cases)
            )[:3]
        ]

        return ControlCoverage(
            control_id=control_id,
            dataset=dataset,
            n_seeds=len(seeds),
            n_amplified=len(amplified),
            n_matched=total_matched,
            match_rate=(
                total_matched / len(amplified) if amplified else 0.0
            ),
            by_mutation=breakdowns,
            weakest_mutations=weakest,
        )

    def run(self) -> CoverageReport:
        """Execute the full coverage sweep and return a structured report."""
        controls = [
            self._eval_control(cid, ds)
            for cid, ds in AMPLIFIABLE_CONTROLS.items()
        ]
        total_amplified = sum(c.n_amplified for c in controls)
        total_matched = sum(c.n_matched for c in controls)
        report = CoverageReport(
            run_id=datetime.now(UTC).isoformat(timespec="seconds"),
            rng_seed=self.rng_seed,
            n_per_seed=self.n_per_seed,
            overall_match_rate=(
                total_matched / total_amplified if total_amplified else 0.0
            ),
            controls=controls,
        )
        _logger.info(
            json.dumps(
                {
                    "event": "amplified_coverage_run",
                    "overall_match_rate": report.overall_match_rate,
                    "controls": {
                        c.control_id: c.match_rate for c in controls
                    },
                }
            )
        )
        return report
