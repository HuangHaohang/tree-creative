.DEFAULT_GOAL := help

.PHONY: help setup setup-browser dev-frontend dev-backend worker lint typecheck test build format format-check compose-config uat-up uat-down uat-logs

help:
	@awk 'BEGIN {FS = ":.*## "; printf "Usage: make <target>\n\n"} /^[a-zA-Z_-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Install frontend and backend dependencies
	pnpm install --frozen-lockfile
	uv sync --project backend --frozen

setup-browser: ## Install the optional Playwright worker dependency
	uv sync --project backend --frozen --extra browser

dev-frontend: ## Start the Umi Max development server
	pnpm --dir frontend dev

dev-backend: ## Start the FastAPI development server
	uv run --project backend uvicorn tree_creative_api.main:app --reload --host 0.0.0.0 --port 8000

worker: ## Start the default Celery worker
	uv run --project backend celery -A tree_creative_api.tasks.celery_app:celery_app worker -Q default,langgraph --loglevel INFO

lint: ## Run frontend and backend linters
	pnpm --dir frontend lint
	cd backend && uv run ruff check .

typecheck: ## Run frontend and backend type checking
	pnpm --dir frontend typecheck
	cd backend && uv run mypy

test: ## Run frontend and backend tests
	pnpm --dir frontend test
	cd backend && uv run pytest

build: ## Build the frontend and backend package
	pnpm --dir frontend build
	uv build --project backend

format: ## Format frontend and backend source
	pnpm --dir frontend format
	cd backend && uv run ruff format .

format-check: ## Verify formatting without changing files
	pnpm --dir frontend format:check
	cd backend && uv run ruff format --check .

compose-config: ## Validate the Docker Compose configuration
	docker compose --env-file .env.example -f deploy/compose.yaml config --quiet

uat-up: ## Build and start the local UAT stack
	docker compose --env-file .env -f deploy/compose.yaml up --build -d

uat-down: ## Stop the local UAT stack
	docker compose --env-file .env -f deploy/compose.yaml down

uat-logs: ## Follow local UAT logs
	docker compose --env-file .env -f deploy/compose.yaml logs -f
