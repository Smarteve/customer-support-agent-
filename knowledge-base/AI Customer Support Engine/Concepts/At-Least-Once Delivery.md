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

# At-Least-Once Delivery

> Expect the same work to be attempted more than once.

## Understand it

The design deliberately tolerates repeated enqueueing and recovery attempts. A worker may finish an external action and die before acknowledging it. Repeated execution is therefore a normal case to handle. Durable state and reconciliation provide recovery within configured retry budgets.

## In this project

A worker crashes after issuing a mock refund. Recovery receives the same logical action and checks the provider result before proceeding.

## Common mistake

Promising end-to-end exactly-once behavior because the queue assigned a unique job ID.

## Interview practice

**How can repeated delivery still produce one refund?**

Separate delivery from effect semantics. Persist a stable logical action ID, pass it as the provider idempotency key, and reconcile uncertain outcomes.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Idempotency]] · [[Transactional Outbox]] · [[Checkpointing and Recovery]] · [[Start Here]] · [[Learning Log]]

## Reference

[AWS Builders’ Library · safe retries](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
