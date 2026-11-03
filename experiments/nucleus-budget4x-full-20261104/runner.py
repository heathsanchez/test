#!/usr/bin/env python3
"""Source-pinned budget-only Nucleus replay; no cached verdicts are trusted.

The candidate is the exact binary from causal tournament 41709666161. This
runner deliberately cannot alter kernel semantics, restore a persistent ACCEPT,
or classify a nonzero/unfinished full-source check as complete.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent
INPUT_SHA = "22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6"
BINARY_SHA = "659d68f956fefac853e3b4b9c6a402a317de362588f3ddc7962e950cfce8161a"
SOURCE_PATCH_SHA = "203de44b272d3f0d524e6dff8a25aaddee06d291ca565a0123d2694ca0bdd719"
ORIGIN_RUN = 41709666161
ORIGIN_ARTIFACT = 13266857833
MAX_FRONTIER = 128 * 1024 * 1024


def sha256(path):
    with Path(path).open("rb") as data:
        return hashlib.file_digest(data, "sha256").hexdigest()


def classify_exit(code):
    return {0: "ACCEPT", 1: "REJECT", 2: "UNKNOWN", 124: "TIMEOUT"}.get(code, "ERROR")


def protected_nonregression(rows, prior_unknown, expected_count=208):
    """Known ACCEPT/REJECT must not weaken; old UNKNOWN may improve or stay.

    The source-pinned manifest provides expected outcomes, but only the
    historically UNKNOWN cases may remain UNKNOWN after this budget change.
    """
    if len(rows) != expected_count or len({r.get("case") for r in rows}) != expected_count:
        return False
    return all(
        r.get("expected") in (0, 1)
        and r.get("rc") in ((r["expected"], 2) if r["case"] in prior_unknown else (r["expected"],))
        for r in rows
    )


def extract_frontier(source, out, name, max_prefix_bytes=MAX_FRONTIER):
    """Retain bounded exact prefix by matching NDJSON NameId ancestry.

    When the frontier is later than the size cap, preserve only its exact
    record/byte offset. A later targeted workflow can reconstruct that prefix
    from the already pinned full-source artifact; no partial input is mislabeled.
    """
    parts = name.split(".")
    matched = {0: 0}
    record = None
    total_bytes = 0
    retained = True
    output = Path(out)
    with Path(source).open("rb") as src, output.open("wb") as dst:
        for line_no, line in enumerate(src, 1):
            total_bytes += len(line)
            if retained and total_bytes <= max_prefix_bytes:
                dst.write(line)
            else:
                retained = False
            row = json.loads(line)
            if "in" in row:
                child = row.get("str") or row.get("num")
                if child:
                    parent = matched.get(child.get("pre"))
                    component = str(child.get("str", child.get("i")))
                    if parent is not None and parent < len(parts) and component == parts[parent]:
                        matched[row["in"]] = parent + 1
            for tag in ("thm", "def", "opaque"):
                if tag in row and matched.get(row[tag].get("name")) == len(parts):
                    record = dict(name=name, record=line_no, tag=tag,
                                  name_id=row[tag]["name"], end_byte=total_bytes)
                    break
            if record:
                break
    if record is None:
        output.unlink()
        return None
    record["retained"] = retained
    if not retained:
        output.unlink()
        record["reason"] = "exact prefix exceeds artifact cap; reconstruct from source SHA"
        return record
    record["sha256"] = sha256(output)
    compressed = Path(str(output) + ".zst")
    subprocess.run(["zstd", "-q", "-f", "-3", str(output), "-o", str(compressed)],
                   check=True, capture_output=True)
    output.unlink()
    record["compressed_bytes"] = compressed.stat().st_size
    record["compressed_sha256"] = sha256(compressed)
    return record


def existing_runtime():
    # Import the exact tournament configuration instead of maintaining a
    # possibly divergent hand-copied collection of experimental flags.
    path = EXPERIMENTS / "nucleus-let-preservation-20261104" / "runner.py"
    spec = importlib.util.spec_from_file_location("nucleus_budget4x_existing", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    env = module.R.N.runtime(True)
    flags = {key: value for key, value in env.items() if key.startswith("NUCLEUS_")}
    if len(flags) != 20 or any(v != "1" for v in flags.values()):
        raise ValueError("original causal tournament flag set is no longer reproduced")
    return env, module.t


def check_receipts(binary, source_patch):
    if sha256(binary) != BINARY_SHA:
        raise ValueError("candidate binary does not match causal source tournament")
    if sha256(source_patch) != SOURCE_PATCH_SHA:
        raise ValueError("candidate source patch does not match causal source tournament")


def full(args):
    from pathlib import Path
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    binary = Path(args.binary).resolve()
    check_receipts(binary, args.source_patch)
    if sha256(args.source) != INPUT_SHA:
        raise ValueError("full source digest mismatch: no verdict may be reused")
    env, tournament = existing_runtime()
    env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    result = tournament.measure(binary, Path(args.source), env, out / "full-input",
                                timeout=args.timeout, perf=False)
    stderr = (out / "full-input" / "stderr").read_text(errors="replace")
    terminals = re.findall(r"^NUCLEUS_DOWNSTREAM:name=(.*?):stage=([^\r\n]*)", stderr, re.M)
    terminal = terminals[-1] if terminals else None
    next_frontier = None
    if result["rc"] == 2 and terminal and not terminal[0].startswith("<"):
        next_frontier = extract_frontier(Path(args.source), out / "next-frontier.ndjson", terminal[0])
    summary = dict(
        kind="budget-only full Mathlib replay", experiment_run=ORIGIN_RUN,
        experiment_artifact=ORIGIN_ARTIFACT, workflow_commit=os.environ.get("GITHUB_SHA"),
        source_patch_sha256=SOURCE_PATCH_SHA, binary_sha256=BINARY_SHA,
        input_sha256=INPUT_SHA, original_prefix_result="ACCEPT",
        result=result, verdict=classify_exit(result["rc"]),
        complete_mathlib_accept=result["rc"] == 0,
        terminal=terminal, next_frontier=next_frontier,
        persistent_cache_skips=0, performance_claim="not qualified",
        configuration={key: value for key, value in env.items() if key.startswith("NUCLEUS_")},
    )
    tournament.write_json(out / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def corpus(args):
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    binary = Path(args.binary).resolve()
    check_receipts(binary, args.source_patch)
    env, tournament = existing_runtime()
    root = Path(args.inputs).resolve()
    manifest_file = root / "inputs-manifest.json"
    manifest = json.loads(manifest_file.read_text())
    if len(manifest) != 208:
        raise ValueError("not the complete 208-case protected corpus")
    rows = tournament.replay(binary, manifest, root, env, out / "verdicts.json")
    qualified = protected_nonregression(rows, tournament.EXPECTED_UNKNOWN)
    summary = dict(
        kind="budget-only protected corpus replay", experiment_run=ORIGIN_RUN,
        experiment_artifact=ORIGIN_ARTIFACT, workflow_commit=os.environ.get("GITHUB_SHA"),
        source_patch_sha256=SOURCE_PATCH_SHA, binary_sha256=BINARY_SHA,
        manifest_sha256=sha256(manifest_file), count=len(rows),
        results={str(rc): sum(r["rc"] == rc for r in rows) for rc in (0, 1, 2)},
        protected_nonregression=qualified,
        regressions=[r for r in rows if not protected_nonregression([r],
                    tournament.EXPECTED_UNKNOWN, expected_count=1)],
        independent_kernel_native_tests="reused from source tournament; not rerun",
        configuration={key: value for key, value in env.items() if key.startswith("NUCLEUS_")},
    )
    tournament.write_json(out / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)
    if not qualified:
        raise SystemExit("candidate failed protected source-pinned corpus; never promote")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("full", "corpus"))
    parser.add_argument("--binary", required=True)
    parser.add_argument("--source-patch", required=True)
    parser.add_argument("--source", default="/tmp/mathlib.ndjson")
    parser.add_argument("--inputs", default="/tmp/current208")
    parser.add_argument("--timeout", type=int, default=5400)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    (full if args.phase == "full" else corpus)(args)


if __name__ == "__main__":
    main()
