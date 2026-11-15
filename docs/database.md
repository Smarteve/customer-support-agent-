# Database schema

This step uses PostgreSQL to save incoming events, run state, and worker progress. SQLAlchemy maps the Python classes to database tables. Alembic applies versioned schema changes.

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

The foreign key requires a saved event. A unique constraint on `runs.event_id` permits only one logical run per saved event. A check constraint permits `pending`, `running`, `completed`, `failed`, and `escalated`. The receiver creates `pending` runs. The worker changes a claimed run to `running`, then to `completed` or `failed`.

## Run events

`run_events` records worker progress. Each row belongs to one run.

| Column | Purpose |
| --- | --- |
| `id` | PostgreSQL-generated integer primary key. Order one run's history by this value. |
| `run_id` | Foreign key to `runs.id`. Deleting a run also deletes its progress rows. |
| `event_type` | Currently `run.started`, `run.completed`, or `run.failed`. |
| `created_at` | Timestamp set by PostgreSQL. |
| `details` | Structured JSONB data. The default is an empty object. |

The index on `(run_id, id)` supports reading one run's history in order. IDs can have gaps after rollback. Across different runs, ID order does not guarantee commit order.

The worker saves a status change and its progress row in the same transaction. If either write fails, both writes roll back. Duplicate execution of a claimed or finished run adds no progress rows. A completion event records `operation: log_event_type`. A failure event records the exception class under `error_type`. It does not copy raw exception messages or customer input.

Migration `0002_run_events` creates the table. It does not invent history for existing runs. A process crash after the start transaction can leave a `running` run with only `run.started`. Recovery remains manual. The authenticated `GET /runs/{run_id}` route reads the saved status. Pub/Sub notices and SSE remain later steps.

## Save sequence

1. Verify the webhook signature and validate the event.
2. Begin a database transaction.
3. Insert the incoming event. The unique constraint also handles simultaneous deliveries.
4. Create its pending run. For a matching duplicate, read the existing run instead.
5. Commit the transaction.
6. After commit, call `enqueue_run(run_id)` to submit the saved ID to RQ.
7. Return HTTP 202 with `status: queued`, the run ID, the pending run status, and the RQ job ID.

A failure before commit rolls back both records. Different content under an existing event ID returns HTTP 409. Database or queue errors return HTTP 503. Queue errors include the saved run ID; they do not undo the database commit. Retry the same event ID and content if the outcome is uncertain. A commit can succeed even if the HTTP response is lost; the matching retry returns the saved run.

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
docker compose exec postgres psql -U support -d support -c '\d run_events'
```

Inspect the saved input and work links:

```bash
docker compose exec postgres psql -U support -d support -c "SELECT e.event_id, r.id AS run_id, r.status FROM events e JOIN runs r ON r.event_id = e.id ORDER BY r.created_at DESC LIMIT 10;"
```

Inspect recent progress. To read one run, filter by its `run_id` and order by `id`:

```bash
docker compose exec postgres psql -U support -d support -c "SELECT id, run_id, event_type, created_at, details FROM run_events ORDER BY id DESC LIMIT 20;"
```

The Docker volume `event-store-data` preserves records across restarts. It is separate from the previous starter's `postgres-data` volume. Do not use `docker compose down --volumes` when you want to retain this data.

## Checks

```bash
docker compose build test
docker compose run --rm test pytest -q
docker compose run --rm --no-deps migrate alembic check
```

Database tests use PostgreSQL after migrations. Most test rows are rolled back. The simultaneous-request test commits its own records and deletes only those records during cleanup. Host-only test runs skip database tests unless `TEST_DATABASE_URL` points to migrated PostgreSQL.

Redis and RQ now receive the run ID after commit. The worker saves progress history. The run-status route is implemented. SSE server routes remain a later step. A pending run is saved work. It does not prove queue submission. The database/queue gap requires manual retry; there is no automatic dispatcher. See [queue submission](queue.md).

References: [SQLAlchemy transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html), [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html).
