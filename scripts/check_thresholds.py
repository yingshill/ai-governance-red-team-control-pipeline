"""Exit non-zero if the safety eval suite failed its thresholds.

Consumed by the CI safety gate workflow. The authoritative threshold logic
lives in ``evals/test_controls.py``; this script simply inspects the
pytest-json-report output and surfaces the outcome.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from controls._log import get_logger

_logger = get_logger("scripts.check_thresholds")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path,
                        help="pytest-json-report output file")
    parser.add_argument("--config", required=True, type=Path,
                        help="thresholds YAML (config/thresholds.yaml)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns 0 on gate pass, 1 on gate failure."""
    args = parse_args(argv)
    try:
        config: dict[str, Any] = yaml.safe_load(args.config.read_text())
        report: dict[str, Any] = json.loads(args.results.read_text())
    except FileNotFoundError as exc:
        print(f"Gate input missing: {exc}", file=sys.stderr)
        return 1
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"Gate input malformed: {exc}", file=sys.stderr)
        return 1

    summary = report.get("summary", {})
    total = int(summary.get("total", 0))
    failed = int(summary.get("failed", 0))
    passed = int(summary.get("passed", 0))

    _logger.info(json.dumps({"event": "gate_summary",
                             "total": total, "passed": passed, "failed": failed}))
    print(f"pytest: total={total} passed={passed} failed={failed}")

    if failed > 0 and config.get("blocking", True):
        print("Safety gate BLOCKED: one or more controls failed.", file=sys.stderr)
        return 1

    print("Safety gate PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
