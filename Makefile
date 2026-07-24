.PHONY: help dev test build clean db-up db-down docker-dev

help:
	@printf "  make build  Clean and build the project\n"
	@printf "  make clean  Remove build outputs\n"
	@printf "  make db-up  Start PostgreSQL in Docker\n"
	@printf "  make db-down Stop PostgreSQL in Docker\n"
	@printf "  make db-prune   Stop PostgreSQL and remove its Docker volume\n"
	@printf "  make docker-dev Start the API and PostgreSQL with Docker Compose\n"

dev: db-up
	JWT_SECRET=$(JWT_SECRET) $(GRADLEW) bootRun -t

test: db-up
	JWT_SECRET=$(JWT_SECRET) $(GRADLEW) test

build:
	cd back && rm -rf .venv && uv sync

clean:
	$(GRADLEW) clean

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

db-prune:
	docker compose down -v

docker-dev:
	docker compose up --build
