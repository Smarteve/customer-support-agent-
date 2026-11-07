"""Build portable Obsidian notes and browser data from the curated concept set."""

import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "knowledge-base"
OUT = KB / "AI Customer Support Engine"
DIST = ROOT / "visualization" / "dist"
concepts = json.loads((KB / "concepts.json").read_text())
by_id = {c["id"]: c for c in concepts}
(OUT / "Concepts").mkdir(parents=True, exist_ok=True)
(OUT / "Templates").mkdir(exist_ok=True)
for c in concepts:
    related = " · ".join(f'[[{by_id[r]["title"]}]]' for r in c["related"])
    note = f'''---
type: concept
project: ai-customer-support-engine
category: {c['category']}
created: 2026-11-07
status: to-review
tags:
  - support-engine
  - learning
---

# {c['title']}

> {c['summary']}

## Understand it

{c['explanation']}

## In this project

{c['example']}

## Common mistake

{c['pitfall']}

## Interview practice

**{c['question']}**

{c['answer']}

## Try it

Explain this concept in your own words. Identify where it belongs in the design, then write a small test or failure scenario that would expose an incorrect implementation.

## My notes

- What I learned:
- Evidence from implementation:
- Questions to revisit:

## Connections

{related} · [[Start Here]] · [[Learning Log]]

## Reference

[{c['sourceLabel']}]({c['source']})

The application example and interview answer describe our proposed design. The reference provides background rather than a guarantee about the implementation.
'''
    (OUT / "Concepts" / f"{c['title']}.md").write_text(note)

index = '''---
type: project-index
created: 2026-11-07
tags: [support-engine]
---

# AI Customer Support Engine — Start Here

A linked notebook for an event-driven support agent. The Docker starter now runs a fake-agent order inquiry with saved history and Pub/Sub-to-SSE updates. The full agent, refunds, and React dashboard remain planned.

## Project materials

- [[System Design]] — complete design document, with local diagrams.
- [[Implementation Status]] — current executable scope and test evidence.
- [[Learning Log]] — capture discoveries, questions, and implementation evidence.
- [[Templates/Concept Note|Concept Note template]] — use for new concepts.
- [[Templates/Learning Session|Learning Session template]] — use after a build session.

## Suggested learning route

1. [[Event-Driven Architecture]] → [[Webhook Authentication]] → [[Task Queues and RQ]]
2. [[Job Lifecycle and Run Events]] → [[Redis PubSub Streaming]] → [[Server-Sent Events]] → [[Traces and Observability]]
3. [[Agent Tool-Use Loop]] → [[Policy Enforcement]] → [[Human-in-the-Loop Approval]]
4. [[Checkpointing and Recovery]] → [[Leases and Fencing Tokens]]
5. [[Server-Sent Events]] → [[Tenant Isolation]] → [[Traces and Observability]]
6. [[Agent Evaluation]] → [[Backpressure and Retry Budgets]]
7. [[Docker Compose Services]] → [[Database Migrations]] → [[Continuous Integration]]
8. [[ASD-STE100 Writing Rules]] — write clear design notes and project answers.

[[Transactional Outbox]] and [[Tool Gateway]] describe later reliability or code-organization options. Neither is a separate component in the initial architecture.

## Concept index

'''
for category in dict.fromkeys(c["category"] for c in concepts):
    index += f"### {category}\n\n"
    index += "".join(f'- [[{c["title"]}]] — {c["summary"]}\n' for c in concepts if c["category"] == category) + "\n"
index += '''## How this notebook stays useful

After a session, add a dated entry to the learning log, connect the concepts you encountered, and record one piece of implementation evidence. Change a note's status from `to-review` to `understood` only when you can explain it and demonstrate it.

These are normal Markdown notes with wiki links. No Obsidian plugin, API key, or network sync service is required. The HTML explorer opens them using Obsidian's registered URI handler. It cannot read your vault or detect edits. Browser review marks are local to that browser and do not change your note status.

The project contains a portable seed copy. Re-running the provided sync script preserves notes edited inside Obsidian and reports conflicts. It is a manual update operation, not background or two-way synchronization.
'''
(OUT / "Start Here.md").write_text(index)
learning_log_seed = '''---
type: learning-log
tags: [support-engine, learning]
---

# Learning Log

## 2026-11-07 — Project visualization and notebook setup

- Created a map of the proposed architecture and illustrative request walkthroughs.
- Started a linked concept library covering reliability, agents, security, and operations.
- Next: implement the smallest durable webhook-to-worker path.
- Revisit: [[Transactional Outbox]], [[Idempotency]], and [[Task Queues and RQ]].

## Session format

- Date and build task:
- Concept encountered: [[Concept name]]
- My explanation:
- Implementation or test evidence:
- Open question:
- Next experiment:
'''
if not (OUT / "Learning Log.md").exists():
    (OUT / "Learning Log.md").write_text(learning_log_seed)
(OUT / "Templates" / "Concept Note.md").write_text('''---
type: concept
project: ai-customer-support-engine
status: to-review
tags: [support-engine, learning]
---

# {{title}}

## In my own words

## Why this project needs it

## Concrete example

## Common mistake

## Implementation evidence

## Interview question and answer

## Connections

[[Start Here]] · [[Learning Log]]

## Sources
''')
(OUT / "Templates" / "Learning Session.md").write_text('''# Learning session — {{date}}

## What I built

## Concepts encountered

## What surprised me

## Evidence and experiments

## Explain it without notes

## Questions and next steps

[[Learning Log]] · [[Start Here]]
''')
shutil.copy2(ROOT / "docs" / "design.md", OUT / "System Design.md")
shutil.copy2(ROOT / "docs" / "implementation-status.md", OUT / "Implementation Status.md")
shutil.copytree(ROOT / "docs" / "diagrams", OUT / "diagrams", dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("*.py", "__pycache__"))
DIST.mkdir(parents=True, exist_ok=True)
(DIST / "data.js").write_text("window.CONCEPTS = " + json.dumps(concepts, ensure_ascii=False) + ";\n")
shutil.copy2(ROOT / "docs" / "design.md", DIST / "design.md")
shutil.copytree(ROOT / "docs" / "diagrams", DIST / "diagrams", dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("*.py", "__pycache__"))
with zipfile.ZipFile(DIST / "obsidian-notes.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(OUT.rglob("*")):
        if path.is_file():
            archive.write(path, path.relative_to(KB))
print(f"Built {len(concepts)} concept notes, project index, design, log, templates, and download bundle.")
