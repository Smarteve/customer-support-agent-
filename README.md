# Customer Support Engine

[![CI](https://github.com/Smarteve/customer-support-agent-/actions/workflows/ci.yml/badge.svg)](https://github.com/Smarteve/customer-support-agent-/actions/workflows/ci.yml)

An event-driven support engine with a Docker-first development setup. The first working slice uses a deterministic fake agent and a mock order API. It needs no paid model credentials.

This project uses one GitHub repository: [Smarteve/customer-support-agent-](https://github.com/Smarteve/customer-support-agent-). Keep application code, the visualization, design files, learning notes, and CI here. The separate `Smarteve/visualization` repository is an earlier copy. Do not use it for new work.

```text
Webhook → FastAPI → PostgreSQL commit → Redis/RQ → Worker → Mock order API
                                                        │
                                       save progress ←──┤
                                                        └─→ Redis Pub/Sub
                                                               │
                                                    FastAPI SSE → Client
```

PostgreSQL stores state and ordered run history. Redis has separate RQ and Pub/Sub roles. FastAPI subscribes before replay and sends saved records through SSE. The stream does not poll the database.

## Start with Docker

Install Docker Engine with Compose v2. No host Python installation is required for the application.

```bash
git clone https://github.com/Smarteve/customer-support-agent-.git
cd customer-support-agent-
cp .env.example .env
docker compose up --build -d --wait
```

The local workspace checkout is `repository/`. Run these commands there if you already have that checkout.

| Service | Purpose | Local access |
| --- | --- | --- |
| `api` | Webhooks, run status, retry, and SSE | [API documentation](http://localhost:8001/docs) |
| `worker` | Real RQ worker running the fake agent | Internal network |
| `postgres` | Persistent run state and event history | Internal network |
| `redis` | RQ job queue and Pub/Sub notifications | Internal network |
| `mock-api` | Customer-scoped synthetic order lookup | Internal network |
| `explorer` | Existing interactive design reference | [Project explorer](http://localhost:8080) |
| `migrate` | One-time database migrations | Runs before API and worker |

The explorer describes the design. It is not the future React operator dashboard. OpenAPI and the simulator exercise the actual backend.

Only the API and explorer publish ports, on `127.0.0.1`. PostgreSQL and Redis remain inside the Compose network. Named volumes preserve their data between container restarts.

Port 8001 avoids another local project using port 8000. Set `API_PORT` and `EXPLORER_PORT` in `.env` if needed.

## Run one request

```bash
docker compose run --rm simulator
```

The simulator signs a customer webhook, submits an order question, and prints the saved execution timeline from SSE. It then prints the final run state and response.

The seeded record is `ORD-1001`, owned by `customer_17`. Try the ownership-denial path:

```bash
docker compose run --rm simulator python -m support_engine.simulator --customer-id customer_unrelated
```

Run status and SSE require `Authorization: Bearer <OPERATOR_TOKEN>`. The simulator uses the configured local token. In OpenAPI, supply the full Bearer header where requested.

## Test and validate

CI uses these same containers and checks:

```bash
docker compose --profile test build
docker compose run --rm --no-deps test ruff check src tests migrations
docker compose run --rm --no-deps test ruff format --check src tests migrations
docker compose run --rm test pytest -q
docker compose run --rm api alembic check
```

Tests cover signatures, changed-event conflicts, duplicate webhook and RQ delivery, queue failure recovery, customer ownership, tenant-scoped reads, Pub/Sub-triggered SSE, and reconnect replay. Tests use unique synthetic records and do not erase existing demonstration data.

GitHub Actions runs on pushes, pull requests, and manual dispatch. It builds the runtime and test images, runs checks and tests, verifies migrations, and removes its own CI containers and volumes.

## Daily commands

```bash
docker compose ps
docker compose logs -f api worker
docker compose run --rm api alembic upgrade head
docker compose down
```

After source changes, rebuild and recreate services with `docker compose up --build -d --wait`.

`.env.example` contains local demonstration credentials. Keep your `.env` untracked. If you change the database password, also update its encoded value in `DATABASE_URL`.

## Current limits

- One configured demonstration tenant and static local service/operator tokens.
- The fake agent supports an order lookup. Real model calls, refunds, approvals, and a React operator dashboard remain planned.
- The initial schema stores the event and message inside the run record. Separate ticket/message tables remain a later migration.
- An operator can retry a pending or failed run. An active run must finish or lose its lease before another attempt can claim it.
- Database commit and queue submission are separate. Incomplete submissions need retry; automatic scheduling recovery remains planned.
- Commit and Pub/Sub publication are also separate. Reconnect replays saved history; a missed final notice can leave an open client stale until reconnect.

## Project materials

- [System design](docs/design.md)
- [Implemented scope and validation](docs/implementation-status.md)
- [Interactive explorer source](visualization/README.md)
- [Obsidian notebook](knowledge-base/AI%20Customer%20Support%20Engine/Start%20Here.md)
- [Knowledge-base workflow](knowledge-base/README.md)

Use the notebook to capture a concept, its failure mode, and evidence from a real test. Preserve personal vault edits when updating seed notes.
