---
type: concept
project: ai-customer-support-engine
category: Security
created: 2026-11-07
status: to-review
tags:
  - support-engine
  - learning
---

# Tenant Isolation

> Constrain every read, write, tool call, and subscription to its authorized tenant.

## Understand it

Derive tenant identity from verified credentials. Apply tenant predicates in repositories and enforce relationship constraints. PostgreSQL row-level security adds defense in depth when configured for the actual API and worker roles; privileged and owner bypass rules must be understood and tested.

## In this project

A ticket ID from tenant B is pasted into tenant A’s dashboard. The REST route, SSE subscription, and order tool all reject access.

## Common mistake

Protecting the UI while background workers or direct ID lookups can still cross tenant boundaries.

## Interview practice

**Is a tenant_id column sufficient?**

No. Queries, relationships, authorization, database roles, streams, and tests must all enforce the boundary.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Webhook Authentication]] · [[Policy Enforcement]] · [[Server-Sent Events]] · [[Start Here]] · [[Learning Log]]

## Reference

[PostgreSQL · row security policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
