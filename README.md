# AI Governance: Red Team → Control Pipeline

[![Release](https://img.shields.io/github/v/release/yingshill/ai-governance-red-team-control-pipeline?sort=semver)](https://github.com/yingshill/ai-governance-red-team-control-pipeline/releases)
[![Nightly safety eval](https://github.com/yingshill/ai-governance-red-team-control-pipeline/actions/workflows/eval_nightly.yml/badge.svg)](https://github.com/yingshill/ai-governance-red-team-control-pipeline/actions/workflows/eval_nightly.yml)
[![Safety gate](https://github.com/yingshill/ai-governance-red-team-control-pipeline/actions/workflows/safety_gate.yml/badge.svg)](https://github.com/yingshill/ai-governance-red-team-control-pipeline/actions/workflows/safety_gate.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/github/license/yingshill/ai-governance-red-team-control-pipeline)](./LICENSE)

> Operationalize **NIST AI RMF** into shippable code: **threat modeling → test cases → controls → CI release gate → monitoring**.

## Why
Most AI safety work lives in slide decks. This repo turns governance policy into **code artifacts you can diff, review, and ship**:

- A **risk register** (YAML) that is schema-validated in CI.
- A **control library** with a shared interface (`BaseControl`) and pluggable detectors.
- An **eval runner** with JSONL datasets for regression testing.
- A **GitHub Actions safety gate** that blocks PRs when safety metrics regress.

## Status
- **Latest release:** [`v0.2.1`](https://github.com/yingshill/ai-governance-red-team-control-pipeline/releases/tag/v0.2.1) — first green CI run
- **Controls live:** CTRL-002 (PII) · CTRL-003 (Jailbreak) · CTRL-004 (Citation) · CTRL-005 (HITL) · CTRL-006 (Drift)
- **Baseline:** 100% measured pass rate across all controls

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
├── controls/                 # Control library (PII, jailbreak, HITL, citations, drift)
├── evals/                    # Datasets, runner, pytest suite, unit tests
├── config/                   # Release thresholds
├── scripts/                  # Gate check, report generator, baseline refresh
├── docs/                     # NIST RMF mapping, threat model, runbook, audit report
├── pyproject.toml
└── Makefile
```

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"

make validate     # risk register schema check
make eval         # run the full eval suite
make gate         # enforce thresholds
make audit        # lint + typecheck + validate + eval + gate
```

## Updating the regression baseline
Baselines are **human-reviewed** and **never** updated in CI. After a deliberate change:
```bash
make baseline-preview    # see old vs. new pass rates per control
make baseline            # write evals/datasets/regression_baseline.json
```
Commit the updated baseline in a **separate PR** from the behavior change — see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Roadmap
- Red team generator: attack taxonomy + prompt mutation + dataset amplification
- Real model target integration (OpenAI / Anthropic / HF)
- Observability dashboard (pass rate over time)
- Production middleware deployment example

## License
MIT
