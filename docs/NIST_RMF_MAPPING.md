# NIST AI RMF Mapping

Each control in this repo maps back to a NIST AI RMF function and category.

| Control ID | Control name          | NIST function | NIST category                    | Linked risks |
| ---------- | --------------------- | ------------- | -------------------------------- | ------------ |
| CTRL-002   | PII Filter            | MANAGE        | MG-2.2 Risk Treatment            | RISK-002     |
| CTRL-003   | Jailbreak Detector    | MEASURE       | MS-2.5 Adversarial Testing       | RISK-001     |
| CTRL-004   | Citation Enforcer     | MEASURE       | MS-2.6 Explainability            | RISK-003     |
| CTRL-005   | Human-in-Loop Trigger | GOVERN        | GV-6.1 Policies for AI Oversight | RISK-005     |
| Eval Runner      | Continuous Eval | MEASURE       | MS-1.1 AI Risk Metrics           | All          |
| Safety Gate (CI) | Release Gate    | MANAGE        | MG-3.1 Risk Response             | All          |
