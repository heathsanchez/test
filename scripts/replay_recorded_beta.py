#!/usr/bin/env python3
"""Replay the exact beta inputs from the original qualified artifact.

Artifact and fixture hashes are checked by this external test harness. The
runtime checker does not inspect expected outcomes or known input hashes.
"""
import argparse
import collections
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import zipfile


ARTIFACT_SHA256 = "d8a2cb8b5c92bb14dea63fb019086e6c7f8a6b6183d804681f53a50fb8c145ee"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    raw = args.archive.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ARTIFACT_SHA256:
        raise ValueError("Original qualification artifact SHA-256 mismatch")
    rows = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.testzip() is not None:
            raise ValueError("Original qualification artifact CRC mismatch")
        original = json.loads(archive.read("beta-rows.json"))
        expected = {row["name"]: row for row in original}
        if len(original) != 356 or len(expected) != len(original):
            raise ValueError("Original corpus size or uniqueness changed")
        seen = set()
        with tarfile.open(fileobj=io.BytesIO(archive.read("tests.tar.gz")), mode="r:gz") as inputs:
            for member in inputs:
                if not member.isfile():
                    continue
                parts = Path(member.name).parts
                if len(parts) < 2 or parts[0] not in ("good", "bad") or ".." in parts:
                    raise ValueError("Unexpected corpus member")
                name = "/".join(parts[1:]).removesuffix(".ndjson")
                if name not in expected or name in seen or not member.name.endswith(".ndjson"):
                    raise ValueError("Unexpected or repeated corpus input: " + name)
                seen.add(name)
                data = inputs.extractfile(member).read()
                previous = expected[name]
                digest = hashlib.sha256(data).hexdigest()
                if digest != previous["sha256"]:
                    raise ValueError("Input SHA-256 mismatch: " + name)
                label = "accept" if parts[0] == "good" else "reject"
                if label != previous["expected"]:
                    raise ValueError("Input expectation mismatch: " + name)
                started = time.monotonic()
                result = subprocess.run([sys.executable, str(root / "arena.py")],
                                        input=data, capture_output=True, timeout=120)
                outcome = {0: "accept", 1: "reject", 2: "unknown"}.get(result.returncode, "error")
                row = {"name": name, "format": previous["format"], "sha256": digest,
                       "expected": label, "previous_raw_exit": previous["raw_exit"],
                       "raw_exit": result.returncode, "observed": outcome,
                       "elapsed_s": round(time.monotonic() - started, 4)}
                rows.append(row)
                print("REPLAY", name, result.returncode, flush=True)
                if result.returncode != previous["raw_exit"]:
                    raise ValueError("Recorded verdict changed: " + json.dumps(row) + "\n" +
                                     result.stderr.decode(errors="replace")[-1200:])
        if seen != set(expected):
            raise ValueError("Original corpus inputs were omitted")
    summary = {"status": "WARRANTED_BOUNDED", "scope": "exact standalone migration replay",
               "source_artifact_sha256": ARTIFACT_SHA256, "input_count": len(rows),
               "counts": dict(collections.Counter(row["observed"] for row in rows)),
               "format_3_2_counts": dict(collections.Counter(row["observed"] for row in rows
                                                           if row["format"] == "3.2.0")),
               "changed_verdicts": [], "rows": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("REPLAY_SUMMARY", json.dumps({key: value for key, value in summary.items() if key != "rows"},
                                       sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
