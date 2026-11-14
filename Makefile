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
	docker compose run --rm test ruff check src tests
	docker compose run --rm test ruff format --check src tests

test:
	docker compose build test
	docker compose run --rm test pytest -q
