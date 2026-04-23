## What changed

<!-- Short summary. -->

## Why

<!-- Link to issue or risk ID. -->

## Type

- [ ] feat
- [ ] fix
- [ ] docs
- [ ] test
- [ ] chore / refactor
- [ ] safety regression fix

## Safety checklist

- [ ] `make lint` clean
- [ ] `make typecheck` clean
- [ ] `make validate` passes
- [ ] `make eval` passes (thresholds + latency + drift + risk-ids)
- [ ] New/changed controls have unit tests in `evals/test_unit/`
- [ ] New dataset cases include `expected_risk_ids`
- [ ] `CHANGELOG.md` updated
- [ ] If this is a safety-relevant change, `regression_baseline.json` is NOT
      updated in the same PR as the change itself (update separately after
      merge, via release process).

## Deployment notes

<!-- Anything CI / rollout / runbook-relevant. -->
