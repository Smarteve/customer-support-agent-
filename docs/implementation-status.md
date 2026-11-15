# Implementation status

Updated: 15 November 2026

The project is being rebuilt step by step for learning. The previous backend implementation was removed from the working tree. Its code remains available in Git history.

## Implemented

- A FastAPI `POST /webhooks/support` route with Pydantic input and response schemas.
- Raw-body signature checks, sender-key validation, and a 300-second timestamp window.
- PostgreSQL `events` and `runs` tables, applied by an Alembic migration.
- One transaction saves the input and its pending run. The receiver then submits the run ID to RQ in Redis.
- HTTP 202 confirms submission and includes `status: queued`, `run_id`, `run_status`, and `job_id`.
- Stable RQ job IDs and `unique=True` reuse an existing matching queued job.
- Duplicate input returns the existing run. Changed content under the same sender and event ID returns HTTP 409.
- Database failures return HTTP 503. No success receipt is returned before commit. Queue errors return HTTP 503 with the saved run ID. Manual retry reuses the original event and run.
- HTTP 401 for invalid webhook credentials and HTTP 422 for invalid event data.
- A command-line simulator in `src/support_engine/simulator.py`.
- One signed customer-message event per command.
- HTTPX for HTTP requests and `httpx-sse` for complete SSE events.
- Options for the message, customer ID, server address, and network timeout.
- Receipt handling for the first receiver step. The simulator stops after the receipt.
- Future status/SSE handling remains in the simulator. Failed requests or runs produce nonzero exits.
- Tests with mock HTTP responses, including multiline SSE, heartbeat comments, invalid stream content types, HTTP errors, and final outcomes.
- A static architecture explorer with a vertical main path and horizontal calls.
- Docker targets and CI for the receiver, simulator, tests, and code checks.

## Not implemented

Status routes, the SSE server, worker, Pub/Sub publication, progress history, and mock enterprise APIs are not present. They will be built in later learning steps. LangChain, LangGraph, live models, refunds, and the React dashboard also remain planned.

The simulator submits an event and prints its saved run ID. Matching duplicates reuse that run. The run remains pending until a future worker starts it. The simulator prints the queue receipt and stops. The API port is 8080. The explorer uses host port 8081.

The proposed architecture remains in `docs/design.md`. Existing knowledge-base notes have not been regenerated or synchronized. Older implementation claims in those notes refer to the previous starter, not this working tree.

Removing the backend source does not delete existing Docker database volumes.

The new PostgreSQL service uses the `event-store-data` volume. Previous starter volumes are not modified. See [database schema](database.md) for fields, constraints, and inspection commands.

Queue submission is implemented in `messaging.enqueue_run`. The job entry point is reserved but execution is not implemented. No worker starts. See [queue submission and manual retry](queue.md).
