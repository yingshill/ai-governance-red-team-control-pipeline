# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-04-22

### Added
- `CTRL-006` `DriftDetector` — detective control addressing `RISK-004`.
- Structured JSON logging via `controls._log` (stdlib logging, `aigov.*` namespace).
- Bounded LRU cache in `JailbreakDetector` (default 4096 entries).
- Latency budget enforcement in `evals/test_controls.py` (P50/P95/P99).
- `expected_risk_ids` evaluation — ground truth now actually checked.
- Regression baseline at `evals/datasets/regression_baseline.json` + drift test.
- Per-control unit tests under `evals/test_unit/`.
- Console scripts `ai-safety-validate`, `ai-safety-gate`, `ai-safety-report`.
- PEP 561 `py.typed` markers for `controls` and `evals` packages.
- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`.

### Changed
- `risks.yaml` — `RISK-004` mitigation switched from `CTRL-005` (HITL) to
  `CTRL-006` (DriftDetector). Risk register version bumped to `1.1`.
- `check_thresholds.py` — now validates inputs and exits cleanly on malformed
  reports. Threshold operator semantics (`gte`/`lte`) enforced in
  `evals/test_controls.py`.
- `pyproject.toml` — removed unused `pydantic` and `structlog` dependencies;
  added `pytest-cov` and `pre-commit`; registered console scripts.

### Removed
- Dead `EvalRunner.run_all` usage paths; runner is dataset-driven per control.

## [0.1.0] — 2026-04-22

### Added
- Initial scaffold: risk register, 4 controls (PII, jailbreak, citation, HITL),
  eval datasets, threshold gate, NIST RMF mapping, threat model, runbook.
