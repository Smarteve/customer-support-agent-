# Customer Support Engine

[![CI](https://github.com/Smarteve/customer-support-agent-/actions/workflows/ci.yml/badge.svg)](https://github.com/Smarteve/customer-support-agent-/actions/workflows/ci.yml)

This is an event-driven customer support learning project. We will build the backend one step at a time. The event simulator and first webhook receiver are implemented. The receiver validates input and saves the event and a pending run in PostgreSQL. Queues, workers, and mock services remain planned.

Keep all project files in [this repository](https://github.com/Smarteve/customer-support-agent-). Run commands from the checkout root. There is no nested `repository/` folder.

## Event simulator

Install Python 3.12 or later and uv. Then run:

```bash
uv sync
cp .env.example .env
uv run python -m support_engine.simulator --help
```

Start the receiver on port 8080:

```bash
docker compose up --build -d --wait
```

Open [API documentation](http://localhost:8080/docs). The request and response models appear there. The database starts first. Alembic applies the schema before the API starts. For a host API process, supply `DATABASE_URL` for reachable PostgreSQL and run `uv run alembic upgrade head` first.

Send one event from your computer:

```bash
uv run python -m support_engine.simulator --base-url http://localhost:8080
```

Change the input with `--message` and `--customer-id`. Set the network timeout with `--timeout`.

The simulator uses HTTPX to send one signed `support.message_received` event. It prints the saved receipt and stops. It signs and sends the exact same request bytes. A failed request produces a nonzero exit code.

The first receiver response is HTTP 200:

```json
{"event_id": "demo_...", "status": "saved", "run_id": "...", "run_status": "pending"}
```

This confirms the database commit. The event and pending run are saved together. The run is not queued. A matching duplicate returns the same run ID. Different content under the same sender and event ID returns HTTP 409.

The simulator retains its `httpx-sse` client for a later HTTP 202 response after queue submission. This first receiver does not expose status or SSE routes.

The expected API contract is:

| Request | Purpose |
| --- | --- |
| `POST /webhooks/support` | Implemented: save the event and pending run, then return HTTP 200. |
| `GET /runs/{run_id}/events` | Planned: stream saved progress through SSE. |
| `GET /runs/{run_id}` | Planned: return the final run status and response. |

Read the implementation in this order:

1. `src/support_engine/schemas.py`: `SupportEvent` defines the input. `WebhookReceipt` defines the reply. Unknown fields are rejected. The event timestamp must include a timezone.
2. `src/support_engine/security.py`: the signature covers the timestamp and exact request bytes. The permitted clock difference is 300 seconds.
3. `src/support_engine/database.py`: `Event` and `Run` define the persistent records.
4. `src/support_engine/repository.py`: one transaction saves the event and pending run.
5. `src/support_engine/api.py`: FastAPI checks the webhook credentials, validates and saves the event, and returns the receipt.

Invalid signatures or sender keys return HTTP 401. Invalid JSON or event fields return HTTP 422. Database errors return HTTP 503. `schema_version` must be integer 1. `event_type` must be `support.message_received`.

The `.env` file supplies `WEBHOOK_KEY_ID`, `WEBHOOK_SECRET`, and `OPERATOR_TOKEN`. The receiver and simulator must use matching webhook values. The operator token is only used by the future status/SSE client. Keep `.env` untracked. The script defaults to `http://localhost:8080`; `API_BASE_URL` or `--base-url` can select another address.

To run the simulator in Docker:

```bash
docker compose run --build --rm simulator
```

The container targets `http://api:8080`. Start the API first with the command above. Set `SIMULATOR_API_BASE_URL` in `.env` to select another server. The script runs only one event per command.

## Design explorer

Start the static explorer:

```bash
docker compose up -d --wait explorer
```

Open [localhost:8081](http://localhost:8081). The explorer shows the proposed architecture and illustrative simulations. It is not a live operator dashboard.

You can also open `visualization/project-explorer.html` directly in a browser.

## Checks

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest -q
```

The same checks can run in Docker with `make check` and `make test`. Host-only tests use mock HTTP responses and an in-process FastAPI client. Database tests run through Compose with migrated PostgreSQL. No Redis or paid model is needed.

See [the database schema and inspection commands](docs/database.md). Existing Docker data volumes are preserved.

## Project materials

- [System design](docs/design.md)
- [Implementation status](docs/implementation-status.md)
- [Explorer source](visualization/README.md)
- [Existing knowledge base](knowledge-base/README.md)

Update learning notes only when requested. Keep personal Obsidian edits outside generated project changes.
