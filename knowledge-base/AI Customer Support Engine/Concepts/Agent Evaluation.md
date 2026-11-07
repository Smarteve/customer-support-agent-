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

# Agent Evaluation

> Test whether the agent achieves the right outcome within policy and resource limits.

## Understand it

Use deterministic fake-model integration tests for orchestration and faults, plus a separate live-model scenario suite for behavior. Assert concrete effects, evidence, ownership, approval requirements, and budgets. Record dataset, model, prompt, tool, and policy versions.

## In this project

A refund scenario passes only if the right customer and amount were approved and one refund was created. Fluent wording alone cannot make it pass.

## Common mistake

Using exact response text as the only assertion, or letting a model judge replace deterministic checks for financial effects.

## Interview practice

**How do you compare two prompts?**

Run the same versioned scenarios, compare task success and prohibited actions alongside latency and cost, inspect regressions, and publish sample size and failure cases.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Agent Tool-Use Loop]] · [[Policy Enforcement]] · [[Traces and Observability]] · [[Start Here]] · [[Learning Log]]

## Reference

[ReAct · example of evaluating agent behavior](https://arxiv.org/abs/2210.03629)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
