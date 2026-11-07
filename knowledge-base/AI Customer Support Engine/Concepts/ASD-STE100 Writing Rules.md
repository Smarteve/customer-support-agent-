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

# ASD-STE100 Writing Rules

> Use short, direct sentences and fixed technical terms.

## Understand it

ASD-STE100 includes writing rules and a controlled dictionary. Our design uses short sentences, active voice, and one topic per paragraph. A technical glossary defines the software terms. A complete dictionary review remains open.

## In this project

Before: The policy gateway facilitates deterministic authorization enforcement. After: The worker checks whether the action is permitted.

## Common mistake

Calling plain English fully STE-compliant without a vocabulary and rules review. Clear text alone does not establish compliance.

## Interview practice

**How does controlled language improve a system design?**

It makes responsibilities and conditions explicit. Use one component name throughout the document. State who does each action. Describe the failure case separately from the normal sequence.

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

[[Transactional Outbox]] · [[Tool Gateway]] · [[Traces and Observability]] · [[Start Here]] · [[Learning Log]]

## Reference

[ASD-STE100 · official questions and answers](https://www.asd-ste100.org/STE_faq.html)

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
