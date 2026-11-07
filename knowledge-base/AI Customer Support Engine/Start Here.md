---
type: project-index
created: 2026-11-07
tags: [support-engine]
---

# AI Customer Support Engine — Start Here

A linked notebook for an event-driven support agent. The Docker starter now runs a fake-agent order inquiry with saved history and Pub/Sub-to-SSE updates. The full agent, refunds, and React dashboard remain planned.

## Project materials

- [[System Design]] — complete design document, with local diagrams.
- [[Implementation Status]] — current executable scope and test evidence.
- [[Learning Log]] — capture discoveries, questions, and implementation evidence.
- [[Templates/Concept Note|Concept Note template]] — use for new concepts.
- [[Templates/Learning Session|Learning Session template]] — use after a build session.

## Suggested learning route

1. [[Event-Driven Architecture]] → [[Webhook Authentication]] → [[Task Queues and RQ]]
2. [[Job Lifecycle and Run Events]] → [[Redis PubSub Streaming]] → [[Server-Sent Events]] → [[Traces and Observability]]
3. [[Agent Tool-Use Loop]] → [[Policy Enforcement]] → [[Human-in-the-Loop Approval]]
4. [[Checkpointing and Recovery]] → [[Leases and Fencing Tokens]]
5. [[Server-Sent Events]] → [[Tenant Isolation]] → [[Traces and Observability]]
6. [[Agent Evaluation]] → [[Backpressure and Retry Budgets]]
7. [[Docker Compose Services]] → [[Database Migrations]] → [[Continuous Integration]]
8. [[ASD-STE100 Writing Rules]] — write clear design notes and project answers.

[[Transactional Outbox]] and [[Tool Gateway]] describe later reliability or code-organization options. Neither is a separate component in the initial architecture.

## Concept index

### Foundations

- [[Event-Driven Architecture]] — Describe what happened, then let background components react to it.
- [[Webhook Authentication]] — Verify who sent the event before treating it as trusted input.
- [[Task Queues and RQ]] — Move slow work out of the web request and schedule it for workers.
- [[Server-Sent Events]] — Stream saved run events from FastAPI to the browser after Redis notices.
- [[ASD-STE100 Writing Rules]] — Use short, direct sentences and fixed technical terms.
- [[Job Lifecycle and Run Events]] — Save current state and a separate ordered history throughout execution.
- [[Polling and Database Notifications]] — Alternative ways to detect changes; the current design uses Redis Pub/Sub.
- [[Redis PubSub Streaming]] — Commit each progress event, publish a Redis notice, and stream saved records through SSE.
- [[Database Migrations]] — Apply versioned schema changes before services use the database.

### Reliability

- [[Transactional Outbox]] — A later option for reliable publication of saved work.
- [[At-Least-Once Delivery]] — Expect the same work to be attempted more than once.
- [[Idempotency]] — Repeat the same logical operation without repeating its business effect.
- [[Checkpointing and Recovery]] — Resume from recorded progress and reconcile anything with an uncertain outcome.
- [[Leases and Fencing Tokens]] — Give a worker temporary ownership and reject writes from stale owners.

### Agents

- [[Agent Tool-Use Loop]] — Let the model propose a next step, then execute it through controlled code.
- [[Policy Enforcement]] — Apply access and business rules in code before a tool runs.
- [[Human-in-the-Loop Approval]] — Pause consequential work until an authorized person approves the exact action.
- [[Agent Evaluation]] — Test whether the agent achieves the right outcome within policy and resource limits.
- [[Tool Gateway]] — An optional code organization, omitted from the simple architecture.

### Security

- [[Tenant Isolation]] — Constrain every read, write, tool call, and subscription to its authorized tenant.

### Operations

- [[Traces and Observability]] — Connect an accepted message to model calls, tool effects, and its final delivery.
- [[Backpressure and Retry Budgets]] — Bound incoming work and retries so overload does not amplify itself.
- [[Docker Compose Services]] — Run the API, worker, storage, and mock services on one local network.
- [[Continuous Integration]] — Check each repository change through a repeatable container build and test workflow.

## How this notebook stays useful

After a session, add a dated entry to the learning log, connect the concepts you encountered, and record one piece of implementation evidence. Change a note's status from `to-review` to `understood` only when you can explain it and demonstrate it.

These are normal Markdown notes with wiki links. No Obsidian plugin, API key, or network sync service is required. The HTML explorer opens them using Obsidian's registered URI handler. It cannot read your vault or detect edits. Browser review marks are local to that browser and do not change your note status.

The project contains a portable seed copy. Re-running the provided sync script preserves notes edited inside Obsidian and reports conflicts. It is a manual update operation, not background or two-way synchronization.
