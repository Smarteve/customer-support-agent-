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

# Database Migrations

> Apply versioned schema changes before services use the database.

## Understand it

Alembic records schema revisions and applies them in order. The first migration creates tenant-scoped runs and ordered run events. Compose runs alembic upgrade head before API and worker startup.

## In this project

migrations/versions/0001_run_history.py creates the tables, unique constraints, and foreign keys. The alembic check command reports whether model changes need another revision.

## Common mistake

Relying on create_all at application startup. That does not provide an explicit history of schema changes or a controlled upgrade path.

## Interview practice

**Does an empty alembic check prove a migration is safe?**

No. It checks model/schema consistency. Review changes for data loss, locking, compatibility, and required data conversion. Our initial validation reported no new upgrade operations.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Docker Compose Services]] · [[Job Lifecycle and Run Events]] · [[Continuous Integration]] · [[Start Here]] · [[Learning Log]]

## Reference

[Alembic · migration environment and revisions](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
