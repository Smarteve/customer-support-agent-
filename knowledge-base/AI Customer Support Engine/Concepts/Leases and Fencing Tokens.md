---
type: concept
project: ai-customer-support-engine
category: Reliability
created: 2026-11-07
status: to-review
tags:
  - support-engine
  - learning
---

# Leases and Fencing Tokens

> Give a worker temporary ownership and reject writes from stale owners.

## Understand it

A lease expires unless its owner renews it. A new owner increments a monotonic fencing token. Every state write checks the current token, so an old worker cannot commit after a replacement takes over. External services also need idempotency because a fence cannot cancel a request already sent.

## In this project

Worker A stalls with token 7. Worker B acquires token 8 after expiry. PostgreSQL rejects A’s checkpoint with token 7.

## Common mistake

Relying on a lock timeout alone. The old process may wake up after its lock expires and still believe it owns the work.

## Interview practice

**Does fencing prevent duplicate external refunds?**

Only if the external resource enforces the token or another equivalent constraint. Our mock payments API uses stable action idempotency in addition to application fencing.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Checkpointing and Recovery]] · [[Idempotency]] · [[At-Least-Once Delivery]] · [[Start Here]] · [[Learning Log]]

## Reference

[Martin Kleppmann · distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
