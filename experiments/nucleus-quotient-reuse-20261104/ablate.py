#!/usr/bin/env python3
"""Exact-frozen-corpus rule ablation for already-compiled Nucleus binaries."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile

BASE_FLAGS = (
    "CONTEXT_BINDER EXPECTED_LAMBDA FORMED_PROP_DOMAIN_RETRY "
    "POLYMORPHIC_PROP_IRREL PROJECTION_CONTEXT PROJECTION_CROSSFRAME_512 "
    "PROP_SINGLETON_2P1F RELEVANCE REPLAY_NEUTRAL_PROJECTION "
    "REPLAY_PROJECTION_MAJOR SOURCE_PAIR_DEPTH8 SUBSTITUTION_RECLOSURE "
    "TYPED_DATA_CONGRUENCE TYPED_LINEAGE TYPED_PROJECTION_SPINE "
    "TYPED_RECEIVER TYPED_VALUE_NORMALIZATION"
).split()


def run(args):
    with zipfile.ZipFile(args.reference) as archive:
        previous = json.loads(archive.read("candidate/verdicts.json"))
    manifest = json.loads((args.corpus / "inputs-manifest.json").read_text())
    assert len(previous) == len(manifest) == 208
    env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    for flag in BASE_FLAGS + ["CERTIFIED_QUOT_IOTA", "SOURCE_PROOF_IRREL"]:
        env["NUCLEUS_EXPERIMENTAL_" + flag] = "1"
    env["NUCLEUS_FROZEN196"] = str(args.corpus / "inputs")
    rows = []
    start = time.monotonic()
    for item, old in zip(manifest, previous):
        assert item["case"] == old["case"] and item["sha256"] == old["sha256"]
        path = args.corpus / "inputs" / item["relative_path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        with path.open("rb") as source:
            result = subprocess.run(
                [str(args.binary)], stdin=source, capture_output=True,
                env=env, timeout=240,
            )
        row = dict(case=item["case"], reference=old["rc"], current=result.returncode,
                   expected=item["expected"])
        rows.append(row)
        if result.returncode != old["rc"]:
            print("DELTA", row, flush=True)
    summary = dict(
        candidate_binary_sha256=hashlib.sha256(args.binary.read_bytes()).hexdigest(),
        removed_flag="NUCLEUS_EXPERIMENTAL_EXACT_PROOF_NEUTRALS",
        corpus_count=len(rows),
        verdict_counts={str(code): sum(x["current"] == code for x in rows) for code in (0, 1, 2)},
        verdict_differences=[x for x in rows if x["current"] != x["reference"]],
        errors=[x for x in rows if x["current"] not in (x["expected"], 2)],
        wall_seconds=time.monotonic()-start,
    )
    if args.output:
        args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)
    assert not summary["errors"]
    assert not summary["verdict_differences"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    arguments.binary = arguments.binary.resolve()
    arguments.corpus = arguments.corpus.resolve()
    run(arguments)
