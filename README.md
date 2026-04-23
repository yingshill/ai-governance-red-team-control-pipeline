# AI Governance: Red Team → Control Pipeline

> Operationalize **NIST AI RMF** into shippable code: **threat modeling → test cases → controls → CI release gate → monitoring**.

## Why
Most AI safety work lives in slide decks. This repo turns governance policy into **code artifacts you can diff, review, and ship**:

- A **risk register** (YAML) that is schema-validated in CI.
- A **control library** with a shared interface (`BaseControl`) and pluggable detectors.
- An **eval runner** with JSONL datasets for regression testing.
- A **GitHub Actions safety gate** that blocks PRs when safety metrics regress.

## Design principles
- **Risk-first** — every control traces back to a quantified risk in `risk_register/risks.yaml`.
- **Fail-closed** — controls that error out default to `block`, never silent pass.
- **Layered defense** — pattern matching + heuristics + (optional) ML classifier, each independently testable.
- **Shippable governance** — every policy decision is a PR diff, reviewed and versioned.

## Repo layout
```
.
├── .github/workflows/        # CI: safety gate + nightly eval
├── risk_register/            # YAML risks + JSON Schema + validator
├── controls/                 # Control library (PII, jailbreak, HITL, citations)
├── evals/                    # Datasets, runner, pytest suite
├── config/                   # Release thresholds
├── scripts/                  # Gate check + report generator
├── docs/                     # NIST RMF mapping, threat model, runbook
├── pyproject.toml
└── Makefile
```

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"

python risk_register/validate.py
make eval
make gate
```

## License
MIT
