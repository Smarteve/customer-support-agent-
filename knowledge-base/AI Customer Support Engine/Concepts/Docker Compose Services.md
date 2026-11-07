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

# Docker Compose Services

> Run the API, worker, storage, and mock services on one local network.

## Understand it

Compose defines containers, environment settings, networks, volumes, and startup dependencies. A running container is not necessarily ready. Our API and worker wait for healthy storage and successful migrations.

## In this project

compose.yaml starts PostgreSQL and Redis. The migration service runs once. The API and worker start after migration completion. Redis and PostgreSQL have no published host ports.

## Common mistake

Assuming depends_on without a readiness condition waits for the database schema. Another mistake is using localhost for another container; use the service name.

## Interview practice

**Why are RQ and the API separate containers?**

They run separate processes with different responsibilities. They share an application image and network. Each can restart or scale without running slow jobs inside HTTP requests.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Task Queues and RQ]] · [[Redis PubSub Streaming]] · [[Database Migrations]] · [[Start Here]] · [[Learning Log]]

## Reference

[Docker · startup order and readiness](https://docs.docker.com/compose/how-tos/startup-order/)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
