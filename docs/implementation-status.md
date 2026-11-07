# Starter implementation

Date: 7 November 2026

The Git repository is `Smarteve/customer-support-agent-`. The local application checkout is `repository/` because the parent workspace has protected Git metadata.

## Implemented

- Docker Compose services for PostgreSQL, Redis, API, worker, mock orders, and the design explorer.
- A one-time migration service that completes before API and worker startup.
- Python 3.12, a committed `uv.lock`, and separate runtime/test image targets.
- Raw-body HMAC checks, a timestamp window, body limits, and strict event schemas.
- A transaction that saves the inbound event, message, pending run, and receipt event together.
- Direct RQ submission after commit, with durable submission-error metadata.
- A real RQ worker with JSON serialization and a deterministic fake agent.
- A scoped mock order API. The worker sends trusted customer and tenant context.
- Short state/event transactions, atomic per-run sequence numbers, and duplicate-execution checks.
- Redis Pub/Sub notices after commit and an SSE endpoint that subscribes before replay.
- Bounded, coalesced wake-up buffering and saved-event replay after the browser cursor.
- Bearer-protected run reads, SSE, and manual retry.
- Local containers run the Python application as a non-root user.
- CI builds containers, checks code, runs integration tests, and checks migration consistency.

## Local validation

The initial Docker validation passed all 10 tests. Alembic reported no new upgrade operations. The services reached their Compose health checks.

Integration tests used real PostgreSQL, Redis, RQ workers, HTTP endpoints, and Pub/Sub subscriptions. A saved-only event did not update the stream until its notice was published. Reconnection recovered a saved event whose notice was not sent.

A repeated webhook and a repeated RQ delivery retained one logical run and one execution attempt. A simulated queue error retained a pending run that a sender retry could resubmit.

## Still planned

The real model adapter, full tool-use loop, refund approval flow, separate ticket/message tables, React operator UI, and automatic abandoned-work recovery remain planned.

The local tokens and single configured tenant support the demonstration. They are not production identity management.

Redis Pub/Sub is transient. PostgreSQL replay preserves event history, but live notice delivery is not guaranteed across every commit/publish failure.
