.PHONY: help run sync fetch seed build db-up db-down db-prune docker-dev

help:
	@printf "  make run        Run local FastAPI backend server\n"
	@printf "  make sync       Sync dependencies using uv\n"
	@printf "  make fetch      Download TMDB 5000 movies CSV from Kaggle into back/raw/\n"
	@printf "  make seed       Populate PostgreSQL database with TMDB dataset (idempotent)\n"
	@printf "  make db-up      Start PostgreSQL (pgvector) in Docker\n"
	@printf "  make db-down    Stop Docker Compose containers\n"
	@printf "  make db-prune   Stop Docker Compose containers and remove volumes\n"
	@printf "  make docker-dev Start full API and PostgreSQL stack with Docker Compose\n"

run: db-up
	cd back && uv run uvicorn app.main:app --app-dir src --reload --port 8000

sync:
	cd back && uv sync

fetch:
	cd back && PYTHONPATH=src uv run python -m app.scripts.fetch_dataset

seed:
	cd back && PYTHONPATH=src uv run python -m app.scripts.seed

db-up:
	docker compose up -d db

db-down:
	docker compose down

db-prune:
	docker compose down -v

docker-dev:
	docker compose up --build
