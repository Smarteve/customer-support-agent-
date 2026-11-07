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

# Traces and Observability

> Connect an accepted message to model calls, tool effects, and its final delivery.

## Understand it

Pass a trace ID through FastAPI, RQ submission, worker execution, model calls, tools, and delivery. Save progress events in PostgreSQL. Redis Pub/Sub triggers live SSE delivery. Saved events describe progress; metrics and optional spans describe aggregate behavior and timing.

## In this project

A slow ticket shows 20 seconds of queue wait and 2 seconds of model work. The useful fix is worker capacity or admission control, not a different prompt.

## Common mistake

Logging raw customer and payment data, storing private model reasoning, or using run IDs as high-cardinality metric labels.

## Interview practice

**Which latency should the dashboard report?**

Separate webhook acceptance, queue wait, active execution, human wait, and outbound delivery. A single total hides the bottleneck.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Server-Sent Events]] · [[Agent Evaluation]] · [[Backpressure and Retry Budgets]] · [[Start Here]] · [[Learning Log]]

## Reference

[OpenTelemetry · signals](https://opentelemetry.io/docs/concepts/signals/)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
