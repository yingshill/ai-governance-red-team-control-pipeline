"""Recompute ``evals/datasets/regression_baseline.json`` from a fresh run.

Run manually after a **reviewed** change to controls, datasets, or models.
Never invoke this from CI — baselines must be updated by a human in a
separate PR from the behavior change that caused the drift.

Usage:
    python scripts/update_baseline.py              # write in place
    python scripts/update_baseline.py --dry-run    # preview only
    python scripts/update_baseline.py --out other.json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

from controls._log import get_logger
from evals.runners.eval_runner import EvalRunner
from evals.runners.metrics import compute_metrics

DEFAULT_OUT = Path("evals/datasets/regression_baseline.json")
_logger = get_logger("scripts.update_baseline")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="Baseline file to write (default: %(default)s)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print new baseline but do not write")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns 0 on success, 1 on failure."""
    args = parse_args(argv)
    runner = EvalRunner()

    old: dict[str, Any] = {}
    if args.out.exists():
        try:
            old = json.loads(args.out.read_text())
        except json.JSONDecodeError as exc:
            print(f"Existing baseline is malformed: {exc}", file=sys.stderr)
            return 1

    today = _dt.date.today().isoformat()
    new: dict[str, dict[str, Any]] = {}

    print(f"{'Control':<10} {'Old':>8} {'New':>8} {'Delta':>8}")
    print("-" * 40)

    for control_id in sorted(EvalRunner.DATASET_MAP.keys()):
        results = runner.run_for_control(control_id)
        metrics = compute_metrics(results)
        new[control_id] = {
            "pass_rate": round(metrics.pass_rate, 4),
            "updated": today,
        }
        old_val = float(old.get(control_id, {}).get("pass_rate", 0.0))
        delta = metrics.pass_rate - old_val
        marker = ""
        if delta < -0.01:
            marker = "  ⚠ regression"
        elif delta > 0.01:
            marker = "  ↑ improved"
        print(
            f"{control_id:<10} {old_val:>8.2%} {metrics.pass_rate:>8.2%} "
            f"{delta:>+8.2%}{marker}"
        )

    if args.dry_run:
        print("\n(dry-run) Not writing. Re-run without --dry-run to persist.")
        return 0

    args.out.write_text(json.dumps(new, indent=2, sort_keys=True) + "\n")
    _logger.info(json.dumps({"event": "baseline_updated",
                             "path": str(args.out), "date": today}))
    print(f"\n✅ Wrote {args.out}")
    print("Next: review the diff, commit in a separate PR, and explain the\n"
          "behavior change that justifies the update.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
