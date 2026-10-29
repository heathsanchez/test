"""Hash-pinned cold Python callable transport SPIKE, not a secure native runtime.

The caller supplies all inputs and an explicit export list. This proves source
portability only; it does not prove that the callable's meaning is correct,
that its argument semantics are typed, or that executing it is authorized.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def resolve(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
        raise ValueError("INVALID_SOURCE_PATH")
    path = (root / rel).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("INVALID_SOURCE_PATH")
    return path


def check_hash(path: Path, digest: str, failure: str) -> None:
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(failure)


def call(manifest: dict, payload: dict) -> dict:
    if manifest.get("schema") != "research.source-call.v0":
        raise ValueError("UNKNOWN_MANIFEST_SCHEMA")
    root = Path(manifest["root"]).resolve()
    module = resolve(root, manifest["module"])
    check_hash(module, manifest["sha256"], "SOURCE_DIGEST_MISMATCH")
    for name, expected in manifest["dependencies"].items():
        check_hash(resolve(root, name), expected, "DEPENDENCY_DIGEST_MISMATCH")
    name = payload.get("symbol")
    if name not in manifest.get("exports", []):
        raise ValueError("SYMBOL_NOT_EXPORTED")
    args = payload.get("args")
    if not isinstance(args, list):
        raise ValueError("INVALID_INPUTS")
    # Only run AFTER source and dependency checks. This is a trusted-source
    # experiment, not an OS sandbox or an independent admission mechanism.
    sys.path.insert(0, str(module.parent))
    spec = importlib.util.spec_from_file_location("verified_research_candidate", module)
    if spec is None or spec.loader is None:
        raise ValueError("UNKNOWN_SOURCE_IMPORT")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    result = getattr(loaded, name)(*args)
    return {"state": "EXECUTED_UNTYPED_NOT_ADMITTED", "result": result}


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("MANIFEST_REQUIRED")
        manifest = json.loads(Path(sys.argv[1]).read_text())
        payload = json.load(sys.stdin)
        print(json.dumps(call(manifest, payload), sort_keys=True))
    except (ValueError, KeyError, AttributeError, TypeError) as err:
        print(str(err), file=sys.stderr)
        raise SystemExit(2) from None
