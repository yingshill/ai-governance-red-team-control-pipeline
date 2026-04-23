# Security Policy

## Supported versions

| Version | Supported          |
|---------|--------------------|
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a vulnerability

**Do not open a public issue for security reports.** Instead:

1. Email the maintainer at `liuyings3092@students.itu.edu` with a clear
   description, reproduction steps, and potential impact.
2. Expect an initial acknowledgement within 72 hours.
3. Please allow up to 30 days for a coordinated fix before public disclosure.

## Scope

In scope:

- Bypasses of any safety control (CTRL-00x) on realistic inputs.
- Regressions in the release gate (false negatives on the threshold checker).
- Secrets committed to the repo or exposed in CI logs.
- Supply-chain issues in declared dependencies.

Out of scope:

- Denial-of-service against local pytest runs via pathological inputs.
- Issues in hypothetical downstream deployments not shipped here.

## Responsible AI disclosure

Because this repo ships safety controls, please also report:

- Prompt patterns that reliably jailbreak `JailbreakDetector`.
- PII categories `PIIFilter` fails to detect.
- HITL bypasses where irreversible actions slip past `HumanInLoopTrigger`.

Include dataset cases (JSONL lines) when possible.
