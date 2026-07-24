.PHONY: help run sync seed build db-up db-down db-prune docker-dev

help:
	@printf "  make run        Run local FastAPI backend server\n"
	@printf "  make sync       Sync dependencies using uv\n"
	@printf "  make seed       Populate PostgreSQL database with TMDB dataset (idempotent)\n"
	@printf "  make db-up      Start PostgreSQL (pgvector) in Docker\n"
	@printf "  make db-down    Stop Docker Compose containers\n"
	@printf "  make db-prune   Stop Docker Compose containers and remove volumes\n"
	@printf "  make docker-dev Start full API and PostgreSQL stack with Docker Compose\n"

run:
	cd back && uv run uvicorn main:app --reload --port 8000

sync:
	cd back && uv sync

seed:
	cd back && uv run python seed.py

db-up:
	docker compose up -d db

db-down:
	docker compose down

db-prune:
	docker compose down -v

docker-dev:
	docker compose up --build
