.PHONY: up down logs demo test check

up:
	docker compose up --build -d --wait api explorer

down:
	docker compose down

logs:
	docker compose logs -f api explorer

demo:
	docker compose run --build --rm simulator

check:
	docker compose build test
	docker compose run --rm --no-deps test ruff check src tests migrations
	docker compose run --rm --no-deps test ruff format --check src tests migrations

test:
	docker compose build test
	docker compose run --rm test pytest -q
	docker compose run --rm --no-deps migrate alembic check
