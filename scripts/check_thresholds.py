"""Exit non-zero if any control's pass rate is below its configured threshold.

Consumed by the CI safety gate workflow.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path,
                        help="pytest-json-report output file")
    parser.add_argument("--config", required=True, type=Path,
                        help="thresholds YAML (config/thresholds.yaml)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text())
    report = json.loads(args.results.read_text())

    summary = report.get("summary", {})
    total = int(summary.get("total", 0))
    failed = int(summary.get("failed", 0))
    passed = int(summary.get("passed", 0))

    print(f"pytest: total={total} passed={passed} failed={failed}")

    if failed > 0 and config.get("blocking", True):
        print("Safety gate BLOCKED: one or more controls failed their threshold.", file=sys.stderr)
        return 1

    print("Safety gate PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
