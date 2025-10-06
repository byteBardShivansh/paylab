PY=python
PIP=pip

.PHONY: venv install run test lint fmt

venv:
	$(PY) -m venv .venv
	. .venv/Scripts/activate && $(PIP) install -e .[dev]

install:
	$(PIP) install -e .[dev]

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

lint:
	ruff check .
	mypy app

fmt:
	ruff check . --fix

pytest:
	pytest

test: pytest
