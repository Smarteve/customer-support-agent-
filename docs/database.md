# First database schema

This step uses PostgreSQL to save incoming events and pending runs. SQLAlchemy maps the Python classes to database tables. Alembic applies versioned schema changes.

## Events

`events` records what arrived. Its payload is the validated customer event.

| Column | Purpose |
| --- | --- |
| `id` | Internal UUID primary key. The database uses this key for links. |
| `sender_key_id` | The sender key ID that passed the webhook check. |
| `event_id` | The event ID supplied by that sender. |
| `event_type` | The incoming event type, currently `support.message_received`. |
| `occurred_at` | The event timestamp supplied by the sender. |
| `received_at` | The timestamp set by PostgreSQL when the record is created. |
| `payload` | The complete validated event, stored as JSONB. JSONB is PostgreSQL's binary JSON type. |

The pair `(sender_key_id, event_id)` must be unique. A sender cannot reuse an event ID for different content. The sender identity comes from the verified key, not the payload's `source` field. This version configures one sender key. Key rotation and tenant mapping remain later design work.

## Runs

`runs` records the processing work for an event.

| Column | Purpose |
| --- | --- |
| `id` | Internal UUID primary key, returned as `run_id`. |
| `event_id` | Foreign key to `events.id`. This is the internal UUID, not the sender's text event ID. |
| `status` | Current run status. The receiver creates `pending` runs. |
| `created_at` | The timestamp set by PostgreSQL when the record is created. |

The foreign key requires a saved event. A unique constraint on `runs.event_id` permits only one logical run per saved event. A check constraint permits `pending`, `running`, `completed`, `failed`, and `escalated`. This step only creates `pending` runs. No worker changes their status yet.

## Save sequence

1. Verify the webhook signature and validate the event.
2. Begin a database transaction.
3. Insert the incoming event. The unique constraint also handles simultaneous deliveries.
4. Create its pending run. For a matching duplicate, read the existing run instead.
5. Commit the transaction.
6. Return HTTP 200 with `status: saved`, `run_id`, and `run_status`.

A failure before commit rolls back both records. Different content under an existing event ID returns HTTP 409. Database errors return HTTP 503. Retry the same event ID and content if the outcome is uncertain. A commit can succeed even if the HTTP response is lost; the matching retry returns the saved run.

Pydantic normalizes the event before comparison. JSON spacing and field order do not create another event.

## Run and inspect

```bash
docker compose up --build -d --wait
docker compose run --rm simulator
```

Compose starts PostgreSQL, runs `alembic upgrade head`, and then starts FastAPI. PostgreSQL has no published host port.

Inspect the table definitions:

```bash
docker compose exec postgres psql -U support -d support -c '\d events'
docker compose exec postgres psql -U support -d support -c '\d runs'
```

Inspect the saved input and work links:

```bash
docker compose exec postgres psql -U support -d support -c "SELECT e.event_id, r.id AS run_id, r.status FROM events e JOIN runs r ON r.event_id = e.id ORDER BY r.created_at DESC LIMIT 10;"
```

The Docker volume `event-store-data` preserves records across restarts. It is separate from the previous starter's `postgres-data` volume. Do not use `docker compose down --volumes` when you want to retain this data.

## Checks

```bash
docker compose build test
docker compose run --rm test pytest -q
docker compose run --rm --no-deps migrate alembic check
```

Database tests use PostgreSQL after migrations. Most test rows are rolled back. The simultaneous-request test commits its own records and deletes only those records during cleanup. Host-only test runs skip database tests unless `TEST_DATABASE_URL` points to migrated PostgreSQL.

Redis, RQ, workers, progress history, status routes, and SSE server routes remain later steps. A pending run is saved work. It does not prove queue submission. The later database/queue gap will require manual retry until automatic recovery is implemented.

References: [SQLAlchemy transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html), [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html).
