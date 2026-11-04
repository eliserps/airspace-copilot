.PHONY: install dev-api dev-web test lint typecheck check e2e eval api-types

install:
	cd backend && uv sync
	cd frontend && npm ci

dev-api:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-web:
	cd frontend && npm run dev

test:
	cd backend && uv run pytest --cov
	cd frontend && npm test

lint:
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint

typecheck:
	cd backend && uv run mypy app tests scripts
	cd frontend && npm run typecheck

check: lint typecheck test

e2e:
	cd frontend && npm run test:e2e

eval:
	cd backend && uv run python -m evals.evaluate --repeat 3

api-types:
	cd backend && uv run python -m scripts.export_openapi ../frontend/openapi.json
	cd frontend && npm run api:types
