.PHONY: all help dev up down lint format test train eval eval-detectors demo clean

VENV = .venv
PYTHON = $(VENV)/bin/python
RUFF = $(VENV)/bin/ruff
MYPY = $(VENV)/bin/mypy
PYTEST = $(VENV)/bin/pytest

all: lint test

help:
	@echo "ProofLayer Automation Makefile"
	@echo ""
	@echo "Development:"
	@echo "  make setup           Install python dependencies & setup venv"
	@echo "  make run-gateway     Run FastAPI gateway daemon on :8000"
	@echo "  make run-console     Run Next.js web console on :3000"
	@echo "  make up              Start full stack via Docker Compose"
	@echo "  make down            Stop Docker Compose services"
	@echo ""
	@echo "Quality & Testing:"
	@echo "  make lint            Run ruff and mypy checks"
	@echo "  make format          Auto-format code with ruff"
	@echo "  make test            Run pytest suite with coverage"
	@echo ""
	@echo "ML & Evaluation:"
	@echo "  make train           Build synthetic datasets & train calibrated classifier"
	@echo "  make eval-detectors  Evaluate detector ensemble on validation & test sets"
	@echo "  make eval            Full red team evaluation & generate metrics.json"
	@echo ""
	@echo "Demo & Verification:"
	@echo "  make demo            Execute automated BankDesk Shield OFF/ON demo"
	@echo "  make verify          Run offline cryptographic audit log verification"

setup:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	cd apps/console && npm install

up:
	docker compose up --build -d

down:
	docker compose down

run-gateway:
	PYTHONPATH=. $(PYTHON) -m uvicorn services.gateway.app:app --host 0.0.0.0 --port 8000

run-console:
	cd apps/console && npm run start

lint:
	$(RUFF) check .
	$(MYPY) services sdk eval tests

format:
	$(RUFF) format .
	$(RUFF) check --fix .

test:
	PYTHONPATH=. $(PYTEST) tests/

train:
	PYTHONPATH=. $(PYTHON) eval/build_datasets.py
	PYTHONPATH=. $(PYTHON) services/detectors/train.py

eval-detectors:
	PYTHONPATH=. $(PYTHON) eval/eval_detectors.py

eval:
	PYTHONPATH=. $(PYTHON) eval/run_eval.py

demo:
	PYTHONPATH=. $(PYTHON) scripts/run_demo.py

verify:
	PYTHONPATH=. $(PYTHON) services/audit/verifier.py --verify

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf .coverage htmlcov/
