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

# Checkpointing and Recovery

> Resume from recorded progress and reconcile anything with an uncertain outcome.

## Understand it

Save message references, tool results, pending actions, and run progress between steps. The initial version provides an authorized retry path. A later recovery process can detect old pending runs and expired worker ownership automatically.

## In this project

After a worker restart, the runtime sees a completed order lookup and an uncertain refund. It reuses the lookup and reconciles the refund by operation key.

## Common mistake

Assuming the database detects and retries a crashed worker by itself. A crash can leave running state until a person or recovery process checks ownership.

## Interview practice

**Which state is required to resume safely?**

The logical action identities, durable results, input watermark, policy/model versions, current run state, and ownership token—not just the latest chat transcript.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Job Lifecycle and Run Events]] · [[Leases and Fencing Tokens]] · [[Idempotency]] · [[Start Here]] · [[Learning Log]]

## Reference

[RQ · exceptions and retries](https://python-rq.org/docs/exceptions/)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
