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

# Idempotency

> Repeat the same logical operation without repeating its business effect.

## Understand it

Give each logical action a stable key and bind it to an arguments hash. Matching retries return the recorded result; reuse with different arguments is rejected. The key survives worker attempts and approval continuations. It must also be enforced by the service that owns the external effect.

## In this project

Refund action refund_42 runs twice with the same payment, amount, and currency. The mock payments API returns the original refund instead of creating another.

## Common mistake

Generating a fresh key on every retry, or treating two intentionally different refunds as the same action just because their amounts match.

## Interview practice

**What if the refund API times out?**

The outcome is unknown. Look it up by the existing operation key, then retry only under that same identity. Escalate if the provider cannot safely resolve ambiguity.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[At-Least-Once Delivery]] · [[Human-in-the-Loop Approval]] · [[Leases and Fencing Tokens]] · [[Start Here]] · [[Learning Log]]

## Reference

[AWS Builders’ Library · idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
