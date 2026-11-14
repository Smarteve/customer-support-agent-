# Implementation status

Updated: 14 November 2026

The project is being rebuilt step by step for learning. The previous backend implementation was removed from the working tree. Its code remains available in Git history.

## Implemented

- A command-line simulator in `src/support_engine/simulator.py`.
- One signed customer-message event per command.
- HTTPX for HTTP requests and `httpx-sse` for complete SSE events.
- Options for the message, customer ID, server address, and network timeout.
- Final-status checks and nonzero exit codes for failed requests or runs.
- Tests with mock HTTP responses, including multiline SSE, heartbeat comments, invalid stream content types, HTTP errors, and final outcomes.
- A static architecture explorer with a vertical main path and horizontal calls.
- Docker targets and CI for the simulator tests and code checks.

## Not implemented

The FastAPI receiver, status routes, SSE server, worker, PostgreSQL records, migrations, Redis scheduling, Pub/Sub publication, and mock enterprise APIs are not present. They will be built in later learning steps. LangChain, LangGraph, live models, refunds, and the React dashboard also remain planned.

The simulator expects the planned webhook, SSE, and run-status routes. Without a compatible server, it reports a connection error. The planned API port is 8080. The explorer uses host port 8081.

The proposed architecture remains in `docs/design.md`. Existing knowledge-base notes have not been regenerated or synchronized. Older implementation claims in those notes refer to the previous starter, not this working tree.

Removing the backend source does not delete existing Docker database volumes.
