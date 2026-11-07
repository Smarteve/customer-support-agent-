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

# Event-Driven Architecture

> Describe what happened, then let background components react to it.

## Understand it

An event is a record of a fact, such as a customer message being received. A task is a command to do work. Our durable event records and task queue serve different purposes: the database preserves what happened, while RQ schedules what should run next.

## In this project

FastAPI saves the customer event and a pending run. It then sends the run ID to RQ. A worker loads the saved message and records its progress.

## Common mistake

Calling a queue an event log. A consumed task is not a durable history of every business event.

## Interview practice

**Why put processing behind a queue?**

To separate HTTP acceptance from slow model work, absorb bounded bursts, and scale workers independently. This introduces eventual consistency, retries, and ordering decisions.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Transactional Outbox]] · [[Task Queues and RQ]] · [[At-Least-Once Delivery]] · [[Start Here]] · [[Learning Log]]

## Reference

[Transactional messaging pattern](https://microservices.io/patterns/data/transactional-outbox.html)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
