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

# Server-Sent Events

> Stream saved run events from FastAPI to the browser after Redis notices.

## Understand it

The worker commits state and run events in PostgreSQL, then publishes a Redis Pub/Sub notice. FastAPI receives the notice and reads saved events after each browser cursor. It sends those records through SSE. The normal live path uses no database polling.

## In this project

The worker saves event 13 and publishes its run ID and sequence. FastAPI receives the notice, reads event 13 from PostgreSQL, and streams it to React. After reconnection, the API replays any missing saved events.

## Common mistake

Treating a live notification channel as durable storage, or putting authentication tokens in stream query strings.

## Interview practice

**How does SSE differ from Redis Pub/Sub?**

Redis Pub/Sub signals subscribed FastAPI processes. SSE carries event records from FastAPI to a connected browser. PostgreSQL stores the history for replay. The browser never connects directly to Redis.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Redis PubSub Streaming]] · [[Job Lifecycle and Run Events]] · [[Traces and Observability]] · [[Start Here]] · [[Learning Log]]

## Reference

[MDN · using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
