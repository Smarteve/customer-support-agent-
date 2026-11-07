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

# Continuous Integration

> Check each repository change through a repeatable container build and test workflow.

## Understand it

GitHub Actions runs the CI workflow after a push or pull request. Our job builds the runtime and test images, checks Python code, runs tests against real services, and verifies migration consistency.

## In this project

.github/workflows/ci.yml runs the same Compose tests used locally. The tests exercise signed webhook acceptance, RQ execution, Pub/Sub wake-ups, and SSE replay.

## Common mistake

Passing unit tests while never building the Docker image or exercising the database and queue. CI must verify the way the application actually runs.

## Interview practice

**Why use the same containers locally and in CI?**

It reduces differences in Python packages, service versions, and networking. A committed lockfile and Dockerfile make dependency installation repeatable. Real integration tests still need isolated service data.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Docker Compose Services]] · [[Agent Evaluation]] · [[Database Migrations]] · [[Start Here]] · [[Learning Log]]

## Reference

[GitHub · workflow, job, and step concepts](https://docs.github.com/en/actions/about-github-actions/understanding-github-actions)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
