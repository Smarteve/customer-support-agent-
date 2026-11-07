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

# Webhook Authentication

> Verify who sent the event before treating it as trusted input.

## Understand it

We own the receiving FastAPI endpoint. A source platform or customer backend sends an HTTP POST to it. During that request, the source is the HTTP client and FastAPI is the HTTP server. Our simulator acts as the source in local development. The receiver checks the signature, timestamp, identity, and event ID.

## In this project

An external support platform sends a customer-message event to our POST /webhooks/support URL. We save the event and pending run in PostgreSQL, commit, then submit its run ID to Redis. These are separate storage operations.

## Common mistake

Verifying a reserialized body rather than the exact signed bytes, or trusting a customer identity asserted by an unauthorized sender.

## Interview practice

**Does one webhook request make the PostgreSQL and Redis writes one transaction?**

No. One HTTP handler can call both systems, but the PostgreSQL transaction covers only database writes. Enqueueing happens after commit. The database and queue can therefore fail independently.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Idempotency]] · [[Tenant Isolation]] · [[Event-Driven Architecture]] · [[Start Here]] · [[Learning Log]]

## Reference

[GitHub Docs · webhook sender and receiver](https://docs.github.com/en/webhooks/about-webhooks)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
