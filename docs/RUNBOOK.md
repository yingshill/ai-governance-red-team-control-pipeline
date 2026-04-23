# On-call runbook

## Symptom: safety gate failing on `main`
1. Pull the workflow artifact `safety-eval-report` from the failing run.
2. Inspect `reports/CTRL-*.json` to find which control regressed.
3. Reproduce locally:
   ```bash
   pip install -e .[dev]
   pytest evals/test_controls.py -k CTRL-XXX -v
   ```
4. If the regression is **legitimate** (intended policy change):
   - Update `config/thresholds.yaml` with justification in the PR description.
   - Add / update cases in `evals/datasets/*.jsonl`.
5. If the regression is a **real bug**, do NOT raise the threshold; fix the control.

## Symptom: risk register validation failing
- Run `python risk_register/validate.py` locally for the exact JSON Schema error path.
- Most common cause: an ID that does not match `^RISK-[0-9]{3}$` or `^CTRL-[0-9]{3}$`.
