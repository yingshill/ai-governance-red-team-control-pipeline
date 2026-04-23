# Contributing

Thanks for your interest. This project gates AI safety releases, so correctness
and traceability matter more than velocity.

## Dev setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Quality gates

Every PR must pass:

```bash
make lint        # ruff check
make typecheck   # mypy --strict
make validate    # risk register schema validation
make eval        # pytest (controls, thresholds, latency, drift, risk-ids)
```

## PR checklist

- [ ] New risks added to `risk_register/risks.yaml` with an owner and test
      file reference.
- [ ] New controls implement `BaseControl` and are registered in
      `controls/registry.py` + exported from `controls/__init__.py`.
- [ ] Dataset cases include `expected_risk_ids` for every non-`allow` case.
- [ ] `config/thresholds.yaml` updated if the control needs a release gate.
- [ ] `CHANGELOG.md` entry under `## [Unreleased]`.
- [ ] Unit tests in `evals/test_unit/` cover happy path + at least one
      failure mode.

## Commit style

`<type>(<scope>): <imperative summary>` — e.g.
`feat(controls): add refusal rule library`.

Types: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `perf`.

## Code style

- Python 3.11+.
- `from __future__ import annotations` at the top of every module.
- Google-style docstrings on every public class and method.
- Fail closed: controls must never raise on production inputs; wrap fallible
  logic and return `action="block"` with a descriptive reason.
