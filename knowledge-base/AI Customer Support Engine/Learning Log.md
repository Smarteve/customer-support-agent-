---
type: learning-log
tags: [support-engine, learning]
---

# Learning Log

## 2026-11-07 — Project visualization and notebook setup

- Created a map of the proposed architecture and illustrative request walkthroughs.
- Started a linked concept library covering reliability, agents, security, and operations.
- Next: implement the smallest durable webhook-to-worker path.
- Revisit: [[Transactional Outbox]], [[Idempotency]], and [[Task Queues and RQ]].

## 2026-11-07 — Design revision and component responsibilities

- Applied writing principles from [[ASD-STE100 Writing Rules]].
- Defined [[Transactional Outbox]] and the Outbox Dispatcher as separate terms.
- Defined [[Tool Gateway]] as a worker module that applies [[Policy Enforcement]].
- Recorded two failure cases: a saved message without a job, and a refund request without approval.
- Updated the design and diagram. No backend services were implemented in this session.
- Next experiment: test a dispatcher crash after publication and a tool call without approval.

## 2026-11-07 — Simple architecture and saved job lifecycle

- Reduced the initial architecture to eight main components.
- Kept argument, access, and policy checks inside the worker.
- Deferred [[Transactional Outbox]] and its dispatcher to later reliability work.
- Defined [[Job Lifecycle and Run Events]]: save pending, started, intermediate, and final records.
- Traced dashboard updates through Worker → PostgreSQL → FastAPI → Dashboard with [[Server-Sent Events]].
- Recorded the database/queue failure gap and the initial operator retry path.
- No backend services were implemented. Next: test the saved job lifecycle with a fake worker.

## 2026-11-07 — Webhook ownership and database change detection

- We own the webhook receiver. An external platform, customer backend, or local simulator acts as the sender.
- PostgreSQL writes commit before Redis submission. One HTTP request does not create a shared transaction.
- FastAPI initially polls saved run events once per second. SSE carries those updates to the browser.
- [[Polling and Database Notifications]] explains the later LISTEN/NOTIFY option and its explicit signals.
- Revisit [[Webhook Authentication]], [[Server-Sent Events]], and [[Job Lifecycle and Run Events]].
- No backend code was implemented.

## 2026-11-07 — Redis Pub/Sub selected for live updates

- Replaced routine status polling with [[Redis PubSub Streaming]].
- The worker commits state and history, then publishes a notice. FastAPI sends saved records through [[Server-Sent Events]].
- Reuse one Redis deployment for separate RQ and Pub/Sub roles.
- Confirm the subscription before replay, then use per-browser sequence cursors to prevent gaps and duplicates.
- Keep PostgreSQL as history. Pub/Sub notices are transient and require replay after reconnect.
- A crash between commit and publish can leave the dashboard stale until a later notice, refresh, or reconnect.
- No backend implementation changed. The design and HTML simulation now describe the selected Pub/Sub path.

## 2026-11-07 — Docker starter and continuous integration

- Connected the project to the requested GitHub repository in the local repository/ checkout.
- Added [[Docker Compose Services]] for PostgreSQL, Redis, API, worker, mock orders, and the design explorer.
- Added [[Database Migrations]] and a container test target with locked dependencies.
- Added [[Continuous Integration]] for builds, code checks, integration tests, and migration checks.
- Local evidence: all 10 tests passed. Alembic found no new upgrade operations.
- The stream test verified that a saved-only event waits for Pub/Sub. Reconnection replay recovered a missed notice.
- Real model calls, refunds, and the React operator interface remain planned. See [[Implementation Status]].

## Session format

- Date and build task:
- Concept encountered: [[Concept name]]
- My explanation:
- Implementation or test evidence:
- Open question:
- Next experiment:
