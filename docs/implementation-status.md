# Implementation status

Updated: 14 November 2026

The project is being rebuilt step by step for learning. The previous backend implementation was removed from the working tree. Its code remains available in Git history.

## Implemented

- A FastAPI `POST /webhooks/support` route with Pydantic input and response schemas.
- Raw-body signature checks, sender-key validation, and a 300-second timestamp window.
- HTTP 200 receipts with `event_id` and `status: received`. The event is not saved or queued.
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

Status routes, the SSE server, worker, PostgreSQL records, migrations, Redis scheduling, Pub/Sub publication, and mock enterprise APIs are not present. They will be built in later learning steps. LangChain, LangGraph, live models, refunds, and the React dashboard also remain planned.

The simulator can submit an event to the receiver and print its receipt. No run is created. Repeated events are acknowledged again because there is no storage or duplicate detection yet. The API port is 8080. The explorer uses host port 8081.

The proposed architecture remains in `docs/design.md`. Existing knowledge-base notes have not been regenerated or synchronized. Older implementation claims in those notes refer to the previous starter, not this working tree.

Removing the backend source does not delete existing Docker database volumes.
