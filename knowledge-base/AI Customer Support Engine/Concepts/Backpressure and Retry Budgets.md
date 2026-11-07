---
type: concept
project: ai-customer-support-engine
category: Operations
created: 2026-11-07
status: to-review
tags:
  - support-engine
  - learning
---

# Backpressure and Retry Budgets

> Bound incoming work and retries so overload does not amplify itself.

## Understand it

Queueing absorbs bursts but cannot create sustained processing capacity. Apply tenant quotas, queue-age limits, provider concurrency controls, and bounded retry budgets. Retry transient failures with capped backoff and jitter; avoid retries at every layer multiplying the load.

## In this project

Four workers taking 20 seconds per run provide roughly 0.2 runs per second before overhead. Accepting 10 per second indefinitely would grow the backlog.

## Common mistake

Reporting fast webhook acknowledgment as proof that the system can resolve requests at the same sustained rate.

## Interview practice

**What should happen during overload?**

Reject work before durable acknowledgment when admission limits are reached, preserve accepted work, and show queue age and recovery progress.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Task Queues and RQ]] · [[Traces and Observability]] · [[At-Least-Once Delivery]] · [[Start Here]] · [[Learning Log]]

## Reference

[AWS Builders’ Library · retry budgets](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
