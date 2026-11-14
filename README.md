# Customer Support Engine

[![CI](https://github.com/Smarteve/customer-support-agent-/actions/workflows/ci.yml/badge.svg)](https://github.com/Smarteve/customer-support-agent-/actions/workflows/ci.yml)

This is an event-driven customer support learning project. We will build the backend one step at a time. The command-line event simulator is implemented. The receiving API, database, queue, worker, and mock services remain planned.

Keep all project files in [this repository](https://github.com/Smarteve/customer-support-agent-). Run commands from the checkout root. There is no nested `repository/` folder.

## Event simulator

Install Python 3.12 or later and uv. Then run:

```bash
uv sync
cp .env.example .env
uv run python -m support_engine.simulator --help
```

When a compatible receiving API is available on port 8080, send one event:

```bash
uv run python -m support_engine.simulator --base-url http://localhost:8080
```

Change the input with `--message` and `--customer-id`. Set the network timeout with `--timeout`.

The simulator uses HTTPX to send one signed `support.message_received` event. It uses `httpx-sse` to read progress, then requests the final run status. It signs and sends the exact same request bytes. A failed request, incomplete stream, or failed run produces a nonzero exit code.

The expected API contract is:

| Request | Purpose |
| --- | --- |
| `POST /webhooks/support` | Submit the event. Return an accepted response with `run_id`. |
| `GET /runs/{run_id}/events` | Stream saved progress through SSE. |
| `GET /runs/{run_id}` | Return the final run status and response. |

These server routes are not implemented yet. Running the simulator now will report a connection error unless you supply a compatible server. The next learning step is the FastAPI webhook receiver.

The `.env` file supplies `WEBHOOK_KEY_ID`, `WEBHOOK_SECRET`, and `OPERATOR_TOKEN`. The future receiver must use matching values. Keep `.env` untracked. The script defaults to `http://localhost:8080`; `API_BASE_URL` or `--base-url` can select another address.

To run the simulator in Docker:

```bash
docker compose run --build --rm simulator
```

The container targets `http://host.docker.internal:8080`. This address points to your computer. Set `SIMULATOR_API_BASE_URL` in `.env` to select another server. No backend service starts with this command.

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

The same checks can run in Docker with `make check` and `make test`. Tests use mock HTTP responses. They need no API, database, Redis, or paid model.

## Project materials

- [System design](docs/design.md)
- [Implementation status](docs/implementation-status.md)
- [Explorer source](visualization/README.md)
- [Existing knowledge base](knowledge-base/README.md)

Update learning notes only when requested. Keep personal Obsidian edits outside generated project changes.
