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

# Task Queues and RQ

> Move slow work out of the web request and schedule it for workers.

## Understand it

RQ schedules saved run IDs for workers. A normal worker executes one job at a time. Redis also supplies Pub/Sub for live progress, but that is a separate interface. RQ jobs and Pub/Sub notices have different purposes.

## In this project

A job contains run_42. The worker loads its message and verified identity from PostgreSQL, saves running state, and executes bounded work. Approval waits release the worker.

## Common mistake

Assuming async model calls let a normal RQ worker execute many unrelated jobs at once. Add workers for job concurrency.

## Interview practice

**Why not run the model inside the webhook handler?**

Model latency would delay the HTTP response. Saving first preserves the message. The queue moves execution to workers. Separate database and queue writes still need a retry or later automatic recovery.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Event-Driven Architecture]] · [[Redis PubSub Streaming]] · [[Backpressure and Retry Budgets]] · [[Start Here]] · [[Learning Log]]

## Reference

[RQ · workers](https://python-rq.org/docs/workers/)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
