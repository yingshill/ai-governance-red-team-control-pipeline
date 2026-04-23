.PHONY: validate eval gate report lint typecheck all

validate:
	python risk_register/validate.py

eval:
	pytest evals/test_controls.py -v --json-report --json-report-file=eval_results.json

gate:
	python scripts/check_thresholds.py --results eval_results.json --config config/thresholds.yaml

report:
	python scripts/generate_report.py --results eval_results.json --out reports/

lint:
	ruff check . && ruff format --check .

typecheck:
	mypy controls/ evals/

all: validate lint typecheck eval gate
