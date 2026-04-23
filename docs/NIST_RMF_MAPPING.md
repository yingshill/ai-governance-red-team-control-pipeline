# NIST AI RMF 1.0 Mapping

How each control maps to NIST AI Risk Management Framework subcategories.
This file is kept in sync with `risk_register/risks.yaml` and is validated by
the release gate.

## Controls ↔ NIST subcategories

| Control | Name | NIST subcategory | Risks addressed |
|---------|------|------------------|-----------------|
| CTRL-002 | PII Filter | MANAGE 2.1, MANAGE 4.1 | RISK-002 |
| CTRL-003 | Jailbreak Detector | MEASURE 2.7, MEASURE 2.6 | RISK-001 |
| CTRL-004 | Citation Enforcer | MEASURE 2.9, MANAGE 4.1 | RISK-003 |
| CTRL-005 | Human-in-the-Loop Trigger | GOVERN 1.5, GOVERN 5.1 | RISK-005 |
| CTRL-006 | Drift Detector | MEASURE 2.4, MEASURE 4.2, MANAGE 4.3 | RISK-004 |

## NIST functions covered

- **GOVERN** — CTRL-005 enforces policy on autonomy / irreversible actions.
- **MAP** — Risk register (`risks.yaml`) enumerates the context and tracks
  owners and review cadence per risk.
- **MEASURE** — CTRL-003, CTRL-004, CTRL-006 produce metrics consumed by
  the release gate (`scripts/check_thresholds.py` + `evals/test_controls.py`).
- **MANAGE** — CTRL-002, CTRL-004, CTRL-006 reduce residual risk at serve
  time and at release time.

## Evidence pointers

| Audit question | Evidence |
|----------------|----------|
| “What risks have you considered?” | `risk_register/risks.yaml` |
| “How do you know the controls work?” | `evals/datasets/*.jsonl`, `reports/sample/` |
| “How do you detect regressions?” | `controls/drift_detector.py`, `evals/datasets/regression_baseline.json`, `test_no_drift_regression` |
| “What enforces the release gate?” | `evals/test_controls.py`, `scripts/check_thresholds.py`, `config/thresholds.yaml` |
| “Where are the logs?” | `controls/_log.py` (stdlib logging, `aigov.*` namespace) — JSON lines to stderr. |
