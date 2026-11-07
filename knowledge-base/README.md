# Project knowledge base

The curated seed notebook is in `AI Customer Support Engine/`. The existing vault is `/path/to/Obsidian Vault`; this project's notes belong in its `AI Customer Support Engine/` folder.

Build the seed notes and browser content:

```bash
python3 knowledge-base/build.py
```

Install or update this folder in your existing vault:

```bash
python3 knowledge-base/sync_to_obsidian.py '/path/to/Obsidian Vault'
```

The sync script creates new notes, updates previously installed files only when they remain unedited in the vault, and preserves/report conflicts. It never deletes notes or changes vault settings. `.sync-state.json` records hashes for this comparison and should remain local.

Edit personal learning notes in Obsidian. Keep generic seed explanations in `concepts.json`. The HTML has a static copy of those explanations; it does not read vault edits or continuously synchronize. Browser review marks are separate from Obsidian note status.

When adding knowledge during future build sessions, create a concept note with the template, link it from `Start Here` and the learning log, and include a real example, a failure mode, and implementation evidence. This is a workflow to follow during sessions, not an installed automation.

The explorer's links follow the [official Obsidian URI format](https://obsidian.md/help/uri). They require Obsidian and this vault on the device opening the link. A downloadable zip supports other devices.
