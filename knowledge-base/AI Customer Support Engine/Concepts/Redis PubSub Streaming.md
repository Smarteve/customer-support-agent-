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

# Redis PubSub Streaming

> Commit each progress event, publish a Redis notice, and stream saved records through SSE.

## Understand it

The worker commits state and history in PostgreSQL before it publishes a run ID and sequence to Redis. Subscribed FastAPI processes receive the notice. Each process reads saved events for its authorized browser connections and sends them through SSE.

## In this project

Event 13 commits. The worker publishes run_42 and sequence 13. FastAPI reads all rows after the browser cursor, then streams them in order. A reconnect uses the same saved history.

## Common mistake

Treating Redis Pub/Sub as replayable history. It provides at-most-once delivery. A disconnected subscriber misses notices. A crash between database commit and publish can also leave a saved step without a live notice.

## Interview practice

**How do we prevent missing a step during stream connection?**

Attach a bounded local buffer and confirm the Redis subscription before reading saved history. Replay after the last SSE event ID, then process buffered notices. Ignore duplicate sequences. No routine database polling is needed.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Server-Sent Events]] · [[Job Lifecycle and Run Events]] · [[Task Queues and RQ]] · [[Transactional Outbox]] · [[Start Here]] · [[Learning Log]]

## Reference

[Redis · Pub/Sub channels and delivery semantics](https://redis.io/docs/latest/develop/pubsub/)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
