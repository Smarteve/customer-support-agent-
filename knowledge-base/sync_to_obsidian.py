"""Install/update only this project's notes, preserving vault-side edits.

Usage: python3 knowledge-base/sync_to_obsidian.py '/path/to/vault'
No changes to Obsidian settings or unrelated vault files.
"""

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    source = Path(__file__).resolve().parent / "AI Customer Support Engine"
    vault = Path(sys.argv[1]).expanduser().resolve(strict=True)
    if not (vault / ".obsidian").is_dir():
        raise SystemExit("Target must be an existing Obsidian vault with a .obsidian directory.")
    target = vault / source.name
    state_path = Path(__file__).resolve().parent / ".sync-state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    previous = state.get(str(vault), {})
    recorded = dict(previous)
    created = updated = unchanged = 0
    conflicts = []
    for src in sorted(source.rglob("*")):
        if not src.is_file() or src.is_symlink():
            continue
        relative = src.relative_to(source)
        dst = target / relative
        if not dst.resolve().is_relative_to(vault):
            raise SystemExit(f"Refusing path outside the vault: {relative}")
        incoming = digest(src)
        if dst.exists():
            current = digest(dst)
            if current == incoming:
                unchanged += 1
                recorded[str(relative)] = incoming
                continue
            if previous.get(str(relative)) != current:
                conflicts.append(str(relative))
                continue
            updated += 1
        else:
            created += 1
        dst.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=dst.parent, delete=False) as temp:
            temp.write(src.read_bytes())
            temporary = temp.name
        os.replace(temporary, dst)
        recorded[str(relative)] = incoming
    state[str(vault)] = recorded
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    print(json.dumps({"folder": str(target), "created": created, "updated": updated,
                      "unchanged": unchanged, "preserved_edited_notes": conflicts}, indent=2))
    if conflicts:
        print("Vault edits preserved. Review differences manually; no conflicting note was overwritten.")


if __name__ == "__main__":
    main()
