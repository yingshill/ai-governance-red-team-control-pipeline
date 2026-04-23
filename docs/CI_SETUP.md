# CI setup

The workflow files (`.github/workflows/*.yml`) could not be pushed via the MCP
integration because the connection lacks the `workflow` scope. Add them
manually by copying the YAML below into your repo (or re-authorize the GitHub
connection with `workflow` scope and re-run the push).

## `.github/workflows/safety_gate.yml`

```yaml
name: AI Safety Gate

on:
  pull_request:
    paths:
      - "controls/**"
      - "evals/**"
      - "risk_register/**"
      - "config/**"
      - "pyproject.toml"
  push:
    branches: [main]

jobs:
  validate-risk-register:
    name: Validate risk register schema
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install pyyaml jsonschema
      - run: python risk_register/validate.py

  safety-eval:
    name: Safety regression eval
    runs-on: ubuntu-latest
    needs: validate-risk-register
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]
      - name: Run safety eval suite
        run: |
          pytest evals/test_controls.py \
            --tb=short \
            --json-report \
            --json-report-file=eval_results.json \
            -v
      - name: Check release gate thresholds
        run: python scripts/check_thresholds.py --results eval_results.json --config config/thresholds.yaml
      - name: Upload eval report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: safety-eval-report
          path: |
            eval_results.json
            reports/
          retention-days: 90
```

## `.github/workflows/eval_nightly.yml`

```yaml
name: Nightly safety eval

on:
  schedule:
    - cron: "0 8 * * *"
  workflow_dispatch:

jobs:
  nightly-eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e .[dev]
      - run: pytest evals/test_controls.py -v --json-report --json-report-file=eval_results.json
      - run: python scripts/generate_report.py --results eval_results.json --out reports/
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: nightly-safety-report
          path: reports/
          retention-days: 30
```
