"""CLI: amplify seed datasets, run through controls, emit coverage report.

Always exits 0 unless an underlying exception is raised. Coverage gaps are
surfaced as data artifacts, not CI failures — use the generated report to
triage weak mutation classes and plan control hardening.

When run in GitHub Actions, the markdown report is also appended to
``$GITHUB_STEP_SUMMARY`` so it renders in the job summary UI.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from evals.runners.amplified_coverage import AmplifiedCoverageRunner


def _maybe_write_github_summary(markdown: str) -> None:
    """Append the report to $GITHUB_STEP_SUMMARY when running in GitHub Actions."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write(markdown)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the amplified red-team coverage sweep and emit a report. "
            "Non-blocking: always exits 0."
        )
    )
    parser.add_argument(
        "--dataset-dir",
        default="evals/datasets",
        help="Directory containing seed JSONL files (default: %(default)s)",
    )
    parser.add_argument(
        "--out",
        default="reports",
        help=(
            "Output directory for amplified_coverage.{json,md} "
            "(default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--n-per-seed",
        type=int,
        default=20,
        help="Variants to generate per seed (default: %(default)s)",
    )
    parser.add_argument(
        "--rng-seed",
        type=int,
        default=42,
        help="RNG seed for deterministic output (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    runner = AmplifiedCoverageRunner(
        dataset_dir=args.dataset_dir,
        n_per_seed=args.n_per_seed,
        rng_seed=args.rng_seed,
    )
    report = runner.run()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "amplified_coverage.json"
    md_path = out_dir / "amplified_coverage.md"
    json_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n")
    markdown = report.to_markdown()
    md_path.write_text(markdown)

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print()
    print(markdown)

    _maybe_write_github_summary(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
