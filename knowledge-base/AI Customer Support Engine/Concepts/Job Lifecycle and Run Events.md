---
type: concept
project: ai-customer-support-engine
category: Foundations
created: 2026-11-07
status: to-review
tags:
  - support-engine
  - learning
---

# Job Lifecycle and Run Events

> Save current state and a separate ordered history throughout execution.

## Understand it

FastAPI saves input before RQ submission. The worker saves its start, progress, and final outcome in short PostgreSQL transactions. After each commit, it publishes a Redis notice. FastAPI reads saved events on notice or reconnect and streams them through SSE.

## In this project

runs.status is running while run_events contains run.started and tool.completed. A Redis Pub/Sub notice identifies the latest saved sequence. FastAPI sends all missing saved records to the browser.

## Common mistake

Storing only the latest status, or assuming dashboard updates happen only when a webhook arrives. A timeline needs saved intermediate events and an independent status subscription.

## Interview practice

**Why write to PostgreSQL at both the start and end of a job?**

The start record shows active ownership and attempt time. The final record preserves the outcome. Intermediate events explain what happened between them. RQ coordinates execution; PostgreSQL stores application status and history.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Task Queues and RQ]] · [[Redis PubSub Streaming]] · [[Server-Sent Events]] · [[Traces and Observability]] · [[Start Here]] · [[Learning Log]]

## Reference

[MDN · stream saved application events with SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
