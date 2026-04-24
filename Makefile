.PHONY: install validate eval gate report lint typecheck cov audit baseline baseline-preview amplify all clean

install:
	pip install -e ".[dev]"

validate:
	python -m risk_register.validate || python risk_register/validate.py

eval:
	mkdir -p reports
	pytest --json-report --json-report-file=reports/pytest.json

gate:
	ai-safety-gate --results reports/pytest.json --config config/thresholds.yaml

report:
	ai-safety-report --results reports/ --out reports/index.html

lint:
	ruff check .

typecheck:
	mypy controls evals scripts red_team

cov:
	pytest --cov=controls --cov=evals --cov=red_team --cov-report=term-missing --cov-report=html

baseline:
	@echo "⚠  This rewrites evals/datasets/regression_baseline.json."
	@echo "   Only run after a deliberate, reviewed change. See CONTRIBUTING.md."
	@echo ""
	ai-safety-baseline

baseline-preview:
	ai-safety-baseline --dry-run

amplify:
	@echo "Amplifying jailbreak cases (20 variants per seed)..."
	ai-safety-amplify --seed evals/datasets/jailbreak_cases.jsonl --out evals/datasets/jailbreak_amplified.jsonl --n 20
	@echo "Amplifying HITL cases..."
	ai-safety-amplify --seed evals/datasets/hitl_trigger_cases.jsonl --out evals/datasets/hitl_amplified.jsonl --n 20
	@echo "Amplifying PII cases..."
	ai-safety-amplify --seed evals/datasets/pii_cases.jsonl --out evals/datasets/pii_amplified.jsonl --n 20
	@echo "Amplifying citation cases..."
	ai-safety-amplify --seed evals/datasets/citation_cases.jsonl --out evals/datasets/citation_amplified.jsonl --n 20
	@echo "✅ All seeds amplified. Amplified datasets are deterministic given --rng-seed."

audit: lint typecheck validate eval gate
	@echo "✅ Audit pipeline green."

all: install audit report

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage reports/*.json reports/*.html
	find . -type d -name __pycache__ -exec rm -rf {} +
