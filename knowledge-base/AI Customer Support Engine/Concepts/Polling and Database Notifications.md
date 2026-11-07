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

# Polling and Database Notifications

> Alternative ways to detect changes; the current design uses Redis Pub/Sub.

## Understand it

Polling queries repeatedly to detect changes. PostgreSQL LISTEN/NOTIFY uses an explicit database signal. Both are useful alternatives. Our current live path uses worker-published Redis notices after commit, followed by an event read and SSE delivery.

## In this project

A polling design queries for event sequences above 12 once per second. A Redis Pub/Sub design waits for a published notice, then reads those saved events. We selected the Redis design.

## Common mistake

Assuming a database update automatically sends an HTTP webhook, SSE event, or Redis notice. A component must explicitly publish a signal or query for changes.

## Interview practice

**Do we still poll PostgreSQL in the current design?**

No. Read PostgreSQL on connection, reconnection, or a Redis progress notice. Subscribe before replay so that work completed during the replay remains discoverable.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Redis PubSub Streaming]] · [[Server-Sent Events]] · [[Job Lifecycle and Run Events]] · [[Start Here]] · [[Learning Log]]

## Reference

[PostgreSQL · NOTIFY behavior and transaction timing](https://www.postgresql.org/docs/current/sql-notify.html)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
