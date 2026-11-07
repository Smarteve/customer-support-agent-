.PHONY: up down logs demo test check

up:
	docker compose up --build -d --wait

down:
	docker compose down

logs:
	docker compose logs -f api worker

demo:
	docker compose run --rm simulator

check:
	docker compose --profile test build test
	docker compose run --rm --no-deps test ruff check src tests migrations
	docker compose run --rm --no-deps test ruff format --check src tests migrations

test:
	docker compose --profile test build
	docker compose run --rm test pytest -q
	docker compose run --rm api alembic check
