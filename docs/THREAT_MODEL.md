# Threat Model (STRIDE → AI)

Applied to any user-facing LLM feature that this pipeline gates.

| STRIDE element         | AI-specific threat                                | Mitigated by                                       |
| ---------------------- | ------------------------------------------------- | -------------------------------------------------- |
| Spoofing               | Prompt injection impersonating the system prompt  | CTRL-003                                           |
| Tampering              | Training / prompt drift altering safety behavior  | Eval runner + nightly regression + CTRL-005        |
| Repudiation            | Missing audit trail for agentic actions           | Structured logs + CTRL-005 metadata                |
| Information disclosure | PII leakage in model outputs                      | CTRL-002                                           |
| Denial of service      | Runaway tool-call chains / unbounded cost         | HITL cost threshold (CTRL-005)                     |
| Elevation of privilege | Agent takes high-stakes actions autonomously      | CTRL-005                                           |
