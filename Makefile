.PHONY: install validate eval gate report lint typecheck cov audit baseline all clean

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
	mypy controls evals scripts

cov:
	pytest --cov=controls --cov=evals --cov-report=term-missing --cov-report=html

baseline:
	@echo "⚠  This rewrites evals/datasets/regression_baseline.json."
	@echo "   Only run after a deliberate, reviewed change. See CONTRIBUTING.md."
	@echo ""
	ai-safety-baseline

baseline-preview:
	ai-safety-baseline --dry-run

audit: lint typecheck validate eval gate
	@echo "✅ Audit pipeline green."

all: install audit report

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage reports/*.json reports/*.html
	find . -type d -name __pycache__ -exec rm -rf {} +
