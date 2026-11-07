# Project context

This is an event-driven AI customer support learning project. `docs/design.md` is the proposed system design. The application is starting with a Dockerized fake-agent request path. The full agent and React dashboard remain later milestones. `visualization/` is a static architecture explorer with illustrative simulations, not a running support engine.

Use only `https://github.com/Smarteve/customer-support-agent-.git` for this project. Keep the application, visualization, design, notes, and CI in this checkout. Do not create or publish a separate visualization repository.

The checkout is the project root. Run Git, Docker, and build commands here. `compose.yaml`, `src/`, `docs/`, `knowledge-base/`, and `visualization/` sit directly in this folder. Do not add a nested `repository/` folder.

## Writing method

The user requests ASD-STE100 for design text and project answers. Use short sentences, active voice, and one topic per paragraph. Define technical terms before use. Use one name for each component. Keep code, API names, and identifiers exact. Do not claim full STE compliance without a complete rules and vocabulary review.

The current design starts with eight main components. FastAPI serves webhooks, status queries, operator commands, and SSE. The worker contains validation and policy checks; do not add a separate Tool Gateway box. Initial scheduling commits the event and pending run to PostgreSQL, then submits its run ID directly to RQ. An Outbox Dispatcher is a later reliability option. State the database/queue failure gap and initial manual retry behavior. The worker commits state and run_events to PostgreSQL, then publishes a Redis Pub/Sub notice. FastAPI subscribes, reads saved events on notification or reconnect, and streams them through SSE. Use no routine database polling or PostgreSQL NOTIFY for the current live path. Subscribe before replay. Redis Pub/Sub is transient; document missed-notice recovery and the commit/publish failure gap. One Redis deployment supplies RQ scheduling and Pub/Sub as separate roles.

## Maintain the learning notebook

The user wants concepts encountered during the build recorded for later review in Obsidian.

- Use `knowledge-base/concepts.json` for curated explanations shared by the HTML explorer and portable seed notes.
- Keep project notes in the existing Obsidian vault under `AI Customer Support Engine/`. Discover the vault path locally; do not commit personal sync state.
- For substantial new concepts, capture a plain-language explanation, project example, failure mode, interview question, trustworthy reference, and links to related notes. Record actual implementation evidence as it becomes available.
- Keep a dated learning log. Preserve entries and personal edits. Never overwrite a vault note with a generated seed without checking for user edits.
- `knowledge-base/sync_to_obsidian.py` safely installs new notes and reports conflicts; it does not perform continuous or two-way synchronization. Honor filesystem access restrictions when updating the vault.
- Build note/browser artifacts with `python3 knowledge-base/build.py`, then `python3 visualization/build_html.py`. Personal vault edits are not read into the explorer.
- Do not read unrelated personal notes. Push only project source and curated technical notes to the configured GitHub repository. Keep secrets and personal sync state untracked. GitHub authorization does not authorize unrelated website hosting.

## Application commands

Use Docker Compose from this checkout. Start with `docker compose up --build -d --wait`. Run the demo with `docker compose run --rm simulator`. CI checks Ruff, container integration tests, and `alembic check`. The current API port is 8001. The explorer on 8080 is a design reference, not a live operator dashboard.
