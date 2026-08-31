# NABD AI Decision Review - isolated synthetic prototype.
#
# Every target runs against the local Docker workbench by default. Set LOCAL=1 to run the
# Python targets against a native interpreter and database instead, which is what the
# repository's own development loop uses.

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE ?= docker compose
VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip
API_DIR := apps/api
WEB_DIR := apps/web

# Native (LOCAL=1) database endpoints. The Compose stack supplies its own.
LOCAL_OWNER_DSN ?= postgresql+psycopg://nabd_owner:nabd_owner_demo@127.0.0.1:5432/nabd_prototype
LOCAL_APP_DSN   ?= postgresql+psycopg://nabd_app:nabd_app_demo@127.0.0.1:5432/nabd_prototype
TEST_DSN        ?= postgresql+psycopg://nabd_owner:nabd_owner_demo@127.0.0.1:5432/nabd_prototype_test

ifdef LOCAL
RUN_API := cd $(API_DIR) && DATABASE_URL=$(LOCAL_OWNER_DSN) ../../$(PY)
RUN_ROOT := DATABASE_URL=$(LOCAL_OWNER_DSN) $(PY)
RUN_ALEMBIC := cd $(API_DIR) && DATABASE_URL=$(LOCAL_OWNER_DSN) ../../$(VENV)/bin/alembic
else
RUN_API := $(COMPOSE) exec -T api python
RUN_ROOT := $(COMPOSE) exec -T api python
RUN_ALEMBIC := $(COMPOSE) exec -T -e DATABASE_URL=$$OWNER_DATABASE_URL api alembic
endif

CASE_ID ?=

.PHONY: help
help: ## Show the available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[1m%-22s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------------------
# Workbench lifecycle
# ---------------------------------------------------------------------------------------
.PHONY: up
up: ## Start db, api and web
	$(COMPOSE) up -d --build
	@echo "api: http://localhost:8000/api/docs   web: http://localhost:5173"

.PHONY: down
down: ## Stop the workbench and remove its containers
	$(COMPOSE) down

.PHONY: clean
clean: ## Stop the workbench and delete its volumes
	$(COMPOSE) down -v

.PHONY: logs
logs: ## Follow service logs
	$(COMPOSE) logs -f

.PHONY: ps
ps: ## Show service status
	$(COMPOSE) ps

# ---------------------------------------------------------------------------------------
# Database and corpus
# ---------------------------------------------------------------------------------------
.PHONY: migrate
migrate: ## Apply database migrations
	$(RUN_ALEMBIC) upgrade head

.PHONY: migrate-down
migrate-down: ## Roll back one migration
	$(RUN_ALEMBIC) downgrade -1

.PHONY: seed
seed: ## Seed the frozen synthetic corpus and control-plane fixtures
	$(RUN_ROOT) scripts/seed_synthetic_corpus.py --reset

.PHONY: manifest
manifest: ## Regenerate the frozen corpus manifest
	$(PY) scripts/build_corpus_manifest.py

.PHONY: manifest-check
manifest-check: ## Fail if the committed corpus manifest is out of date
	$(PY) scripts/build_corpus_manifest.py --check

.PHONY: expected-excerpts
expected-excerpts: ## Regenerate the frozen expected citations for the benign scenarios
	$(RUN_ROOT) scripts/build_expected_excerpts.py

.PHONY: expected-excerpts-check
expected-excerpts-check: ## Fail if the frozen expected citations are out of date
	$(RUN_ROOT) scripts/build_expected_excerpts.py --check

.PHONY: schemas
schemas: ## Regenerate the JSON Schema contracts
	$(PY) scripts/export_json_schemas.py

.PHONY: schemas-check
schemas-check: ## Fail if a committed JSON Schema is out of date
	$(PY) scripts/export_json_schemas.py --check

# ---------------------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------------------
.PHONY: install
install: ## Create the local virtualenv and install API dependencies
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e "$(API_DIR)[dev,seed]"

.PHONY: lint
lint: ## Ruff and ESLint
	$(VENV)/bin/ruff check $(API_DIR) scripts
	$(VENV)/bin/ruff format --check $(API_DIR) scripts
	cd $(WEB_DIR) && npm run lint

.PHONY: format
format: ## Apply Ruff formatting
	$(VENV)/bin/ruff format $(API_DIR) scripts
	$(VENV)/bin/ruff check --fix $(API_DIR) scripts

.PHONY: typecheck
typecheck: ## mypy and tsc
	cd $(API_DIR) && ../../$(VENV)/bin/mypy app
	cd $(WEB_DIR) && npx tsc --noEmit

.PHONY: test
test: test-api test-web ## Run every automated test

.PHONY: test-api
test-api: ## Backend unit, integration and security tests
	cd $(API_DIR) && TEST_DATABASE_URL=$(TEST_DSN) ../../$(VENV)/bin/python -m pytest -q

.PHONY: test-api-cov
test-api-cov: ## Backend tests with a coverage report
	cd $(API_DIR) && TEST_DATABASE_URL=$(TEST_DSN) ../../$(VENV)/bin/python -m pytest \
		--cov=app --cov-report=term-missing --cov-report=html:../../artifacts/coverage

.PHONY: test-web
test-web: ## Frontend component tests
	cd $(WEB_DIR) && npm run test -- --run

.PHONY: test-e2e
test-e2e: ## Playwright end-to-end tests against a running workbench
	cd tests/e2e && npm run test

.PHONY: tevv
tevv: ## Execute the frozen TEVV suite and write a raw report
	$(RUN_ROOT) scripts/run_tevv.py

.PHONY: audit-verify
audit-verify: ## Verify an audit chain: make audit-verify CASE_ID=<case-id>
ifeq ($(strip $(CASE_ID)),)
	$(RUN_ROOT) scripts/verify_audit_chain.py --all
else
	$(RUN_ROOT) scripts/verify_audit_chain.py --case-id $(CASE_ID)
endif

.PHONY: deployment-validate
deployment-validate: ## Run the automatable deployment-validation checks
	$(RUN_ROOT) scripts/run_deployment_validation.py

.PHONY: evidence-bundle
evidence-bundle: ## Export a timestamped evidence bundle with a manifest and checksums
	$(RUN_ROOT) scripts/export_evidence_bundle.py

.PHONY: verify
verify: manifest-check schemas-check expected-excerpts-check lint typecheck test tevv deployment-validate ## Full developer verification
	@echo
	@echo "Developer verification complete (gate G-A)."
	@echo "Built: NOT_EVIDENCED | Integration: NOT_EVIDENCED | Operational: NOT_EVIDENCED | Authorization: NOT_GRANTED"
