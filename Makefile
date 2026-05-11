.PHONY: install test lint format check precommit run-api run-dashboard compose-up compose-down migrate-up migrate-down backup-data verify-restore monitor-check monitor-loop smoke-post-restart setup-branch-protection

PYTHON := ./venv/bin/python
PIP := ./venv/bin/pip
UVICORN := ./venv/bin/uvicorn
STREAMLIT := ./venv/bin/streamlit
PRECOMMIT := ./venv/bin/pre-commit
RETENTION_DAYS ?= 14

install:
	$(PIP) install -r requirements.txt

migrate-up:
	$(PYTHON) -m alembic upgrade head

migrate-down:
	$(PYTHON) -m alembic downgrade -1

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check app dashboard tests
	$(PYTHON) -m black --check app dashboard tests
	$(PYTHON) -m isort --check-only app dashboard tests

format:
	$(PYTHON) -m ruff check --fix app dashboard tests
	$(PYTHON) -m ruff format app dashboard tests
	$(PYTHON) -m isort app dashboard tests
	$(PYTHON) -m black app dashboard tests

check:
	$(PYTHON) -m compileall app dashboard tests
	$(MAKE) lint
	$(MAKE) test

precommit:
	$(PRECOMMIT) install
	$(PRECOMMIT) run --all-files

run-api:
	$(UVICORN) app.main:app --reload

run-dashboard:
	$(STREAMLIT) run dashboard/streamlit_app.py

compose-up:
	docker compose up --build

compose-down:
	docker compose down

backup-data:
	RETENTION_DAYS=$(RETENTION_DAYS) ./scripts/backup_data.sh

verify-restore:
	./scripts/verify_restore.sh

monitor-check:
	./scripts/monitor_services.sh

monitor-loop:
	INTERVAL_SECONDS=60 ./scripts/monitor_loop.sh

smoke-post-restart:
	./scripts/smoke_post_restart.sh

setup-branch-protection:
	./scripts/setup_branch_protection.sh
