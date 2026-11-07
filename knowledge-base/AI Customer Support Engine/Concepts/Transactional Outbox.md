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

# Transactional Outbox

> A later option for reliable publication of saved work.

## Understand it

The simple design saves a pending run, then submits its ID directly to RQ. A crash between these writes can leave unscheduled work. An outbox is a later option: save a publication request in the same transaction, then let a dispatcher publish it.

## In this project

In a later revision, PostgreSQL could commit a customer message and outbox row together. A dispatcher would publish the saved job after Redis recovers. This process is not part of the initial component diagram.

## Common mistake

Assuming that saving first makes the Redis write atomic. A manual retry handles the initial gap; automatic recovery requires additional design and implementation.

## Interview practice

**Do we need an outbox to start the project?**

No. Start with database-first submission and an explicit retry path. The initial version does not guarantee automatic scheduling recovery. Add an outbox or a pending-run scanner at the reliability milestone.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Job Lifecycle and Run Events]] · [[At-Least-Once Delivery]] · [[Checkpointing and Recovery]] · [[Start Here]] · [[Learning Log]]

## Reference

[Chris Richardson · transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
