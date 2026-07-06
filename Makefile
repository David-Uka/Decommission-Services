.PHONY: install lint test run-example

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests

test:
	pytest -v --cov=decommission --cov-report=term-missing

run-example:
	python -m decommission.cli --inventory examples/services.example.yaml list
