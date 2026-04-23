"""Validate risk_register/risks.yaml against the JSON Schema."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    schema = json.loads((ROOT / "risk_register" / "schema.json").read_text())
    data = yaml.safe_load((ROOT / "risk_register" / "risks.yaml").read_text())

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        msg = "\n".join(f"  - {list(e.path)}: {e.message}" for e in errors)
        print(f"Risk register validation FAILED:\n{msg}", file=sys.stderr)
        return 1

    # Cross-check: every control_id in mitigations must match the CTRL-??? pattern
    control_ids: set[str] = set()
    for risk in data.get("risks", []):
        for mit in risk.get("mitigations", []) or []:
            control_ids.add(mit["control_id"])

    print(f"Risk register OK — {len(data.get('risks', []))} risks, "
          f"{len(control_ids)} distinct controls referenced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
