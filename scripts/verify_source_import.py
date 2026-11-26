#!/usr/bin/env python3
"""Verify runtime bytes against the frozen, qualified source import."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "evidence/source-import-20261126.json").read_text())
    expected = manifest["runtime_files"]
    actual = {p.relative_to(root).as_posix() for p in (root / "src").rglob("*") if p.is_file()}
    actual.update(("Cargo.toml", "Cargo.lock", "arena.py", "arena-flags.json"))
    failures = []
    for name in sorted(set(expected) | actual):
        path = root / name
        if name not in expected or name not in actual or not path.is_file():
            failures.append(name + ": missing or unexpected runtime file")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected[name]["sha256"]:
            failures.append(name + ": differs from qualified source")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Verified {len(expected)} runtime files against {manifest['original_commit']}")
    print("Original src tree:", manifest["original_src_tree"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
