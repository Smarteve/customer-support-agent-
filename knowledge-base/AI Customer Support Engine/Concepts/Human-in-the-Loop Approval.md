---
type: concept
project: ai-customer-support-engine
category: Agents
created: 2026-11-07
status: to-review
tags:
  - support-engine
  - learning
---

# Human-in-the-Loop Approval

> Pause consequential work until an authorized person approves the exact action.

## Understand it

Persist a proposed action and release the worker. Bind approval to its customer, payment, amount, currency, policy version, and arguments hash. An authorized decision creates continuation work. On resumption, recheck policy and current payment state.

## In this project

A synthetic £25 refund enters waiting_approval. Approval schedules a continuation; changing the amount requires a new proposal and decision.

## Common mistake

Leaving a worker blocked while a person decides, or treating approval as permission for any later action on the ticket.

## Interview practice

**Why recheck eligibility after approval?**

Payment or policy state may have changed while the run was paused. Approval applies to a specific proposed action, not stale assumptions.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Policy Enforcement]] · [[Checkpointing and Recovery]] · [[Idempotency]] · [[Start Here]] · [[Learning Log]]

## Reference

[OWASP · transaction authorization](https://cheatsheetseries.owasp.org/cheatsheets/Transaction_Authorization_Cheat_Sheet.html)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
