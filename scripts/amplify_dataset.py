"""Amplify a seed eval dataset using the red team generator.

Example:
    python scripts/amplify_dataset.py \\
        --seed evals/datasets/jailbreak_cases.jsonl \\
        --out evals/datasets/jailbreak_amplified.jsonl \\
        --n 20
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from red_team import RedTeamGenerator


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, required=True, help="Seed JSONL file")
    parser.add_argument("--out", type=Path, required=True, help="Output JSONL file")
    parser.add_argument("--n", type=int, default=20, help="Variants per seed")
    parser.add_argument(
        "--rng-seed", type=int, default=42, help="RNG seed for determinism"
    )
    parser.add_argument(
        "--max-compound",
        type=int,
        default=2,
        help="Maximum number of mutations stacked per variant",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns 0 on success, 1 on failure."""
    args = parse_args(argv)
    if not args.seed.exists():
        print(f"Seed file not found: {args.seed}", file=sys.stderr)
        return 1

    gen = RedTeamGenerator(seed=args.rng_seed, max_compound=args.max_compound)
    total = gen.amplify_file(args.seed, args.out, args.n)
    print(f"✅ Wrote {total} amplified cases to {args.out}")
    print(
        f"   source={args.seed.name}, "
        f"n_per_seed={args.n}, max_compound={args.max_compound}, "
        f"rng_seed={args.rng_seed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
