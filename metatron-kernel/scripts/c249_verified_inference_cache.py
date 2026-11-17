"""C249 exact-frame already-proven inference cache reuse: opt-in whole-source A/B.

All original inputs and expected outcomes are SHA-256 pinned. Only previously PROVEN exact ExprId/frame inference cache entries are reused without a new fuel charge. The experiment never treats a
diagnostic or an UNKNOWN as sufficient for acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile

ARCHIVE = "5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
FLAG = "NUCLEUS_C249_PROVEN_CACHE_REUSE"
EXTRAS = (
    "C182_TYPED_PROOF_IRREL", "C189_NEUTRAL_LAMBDA_PROOF",
    "C190_QUOTIENT_IOTA", "C199_TWO_PARAM_EIGHT_FIELD_RECORD",
    "C201_CLOSED_NULLARY_ENUM", "C216_RIGID_DATA_FUNCTION_CTOR",
)
ORIGINALS = (
    "good/perf/fueled-chain.ndjson",
    "good/perf/grind-ring-5.ndjson",
    "good/perf/magma-list-deep-n36.ndjson",
    "good/perf/magma-list-pair-n7.ndjson",
)
CONTROLS = (
    "bad/bugs/eta-ctor-alias.ndjson",
    "bad/bugs/rec-rule-proof-irrel.ndjson",
    "bad/bugs/rec-rule-proof-irrel-nested.ndjson",
    "bad/bugs/rec-type-proof-irrel.ndjson",
    "bad/bugs/rec-rule-wrong-arg.ndjson",
    "good/tutorial/119_reduceCtorParamRefl.mk.ndjson",
    "good/tutorial/126_quotMkType.ndjson",
)

def replay(exe, src, env, label, log_dir, timeout=240):
    started = time.monotonic()
    run = subprocess.run([str(exe)], input=src, env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         check=False, timeout=timeout)
    stdout = run.stdout.decode(errors="replace")
    stderr = run.stderr.decode(errors="replace")
    (log_dir / (label + ".stdout")).write_text(stdout)
    (log_dir / (label + ".stderr")).write_text(stderr)
    return {"case": label, "exit": run.returncode,
            "elapsed_s": round(time.monotonic() - started, 3),
            "source_sha256": hashlib.sha256(src).hexdigest(),
            "last_downstream": [x for x in stderr.splitlines()
                                if x.startswith("NUCLEUS_DOWNSTREAM:")][-1:]}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--checker", required=True, type=Path)
    parser.add_argument("--flags", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    a = parser.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if hashlib.sha256(a.archive.read_bytes()).hexdigest() != ARCHIVE:
        raise ValueError("Original archive digest changed")
    flags = json.loads(a.flags.read_text())["flags"]
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("Original source-control flags changed")
    base = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    base.update(flags)
    base.update({f"NUCLEUS_EXPERIMENTAL_{k}": "1" for k in EXTRAS})
    base["NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE"] = "1"
    base["NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE"] = "1"
    base["NUCLEUS_C247_TYPED_PI_LOCAL_RETRY"] = "1"
    base["NUCLEUS_C225_JUDGMENT_STEPS"] = "69632"
    base["NUCLEUS_C238_STACK_MIB"] = "128" # prior qualified worker resource boundary
    base["NUCLEUS_TRACE_DOWNSTREAM"] = "1"

    with zipfile.ZipFile(a.archive) as z:
        current = {r["case"]: r for r in json.loads(z.read("current212.json"))}
        if len(current) != 212: raise ValueError("Unexpected corpus size")
        def source(case):
            b = z.read("inputs/" + case)
            if hashlib.sha256(b).hexdigest() != current[case]["sha256"]:
                raise ValueError("Source mismatch: " + case)
            return b
        pairs = []
        for case in ORIGINALS + CONTROLS:
            pair = []
            for enabled in (False, True):
                env = base.copy()
                if enabled: env[FLAG] = "1"
                label = case.replace("/", "_").removesuffix(".ndjson") + f"_reuse{int(enabled)}"
                row = replay(a.checker, source(case), env, label, a.out)
                row.update(original=case, enabled=enabled, expected=current[case]["expected"])
                if row["exit"] not in (0, 1, 2):
                    raise ValueError("Checker crashed: " + str(row))
                if (row["exit"] == 0 and row["expected"] != 0) or (
                    row["exit"] == 1 and row["expected"] != 1
                ):
                    raise ValueError("INCORRECT DECISIVE VERDICT: " + str(row))
                if case in CONTROLS and row["exit"] != current[case]["actual"]:
                    raise ValueError("Protected control changed: " + str(row))
                if case in ORIGINALS and not enabled and row["exit"] != 2:
                    raise ValueError("Unchanged original no longer UNKNOWN: " + str(row))
                pair.append(row)
                print("C249_PAIR", json.dumps(row), flush=True)
            pairs.append(pair)
        remaining = []
        already = set(ORIGINALS + CONTROLS)
        for case in sorted(set(current) - already):
            env = base.copy()
            env[FLAG] = "1"
            label = "full_" + case.replace("/", "_").removesuffix(".ndjson")
            row = replay(a.checker, source(case), env, label, a.out, timeout=180)
            row.update(original=case, expected=current[case]["expected"])
            if row["exit"] not in (0, 1, 2):
                raise ValueError("Checker crashed: " + str(row))
            if (row["exit"] == 0 and row["expected"] != 0) or (
                row["exit"] == 1 and row["expected"] != 1
            ):
                raise ValueError("Incorrect verdict on remaining corpus: " + str(row))
            remaining.append(row)
        all_enabled = [p[1] for p in pairs] + remaining
        if len(all_enabled) != 212 or len(pairs) != 11:
            raise ValueError("Incomplete corpus")
        totals = {
            "ACCEPT": sum(r["exit"] == 0 for r in all_enabled),
            "REJECT": sum(r["exit"] == 1 for r in all_enabled),
            "UNKNOWN": sum(r["exit"] == 2 for r in all_enabled),
        }
        verdict_changes = [{"source": pair[0]["original"], "off": pair[0]["exit"],
                            "on": pair[1]["exit"]} for pair in pairs
                           if pair[0]["exit"] != pair[1]["exit"]]
    report = {"state": "WARRANTED_BOUNDED_IF_CI_GREEN",
              "source_archive": ARCHIVE,
              "candidate": FLAG, "originals": list(ORIGINALS),
              "no_wrong_or_crash": True,
              "decisive_counts": totals,
              "changed_pairs": verdict_changes,
              "paired": pairs,
              "remaining": remaining}
    (a.out / "c249-result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("C249_SUMMARY", json.dumps({
        "counts": totals, "changed_pairs": verdict_changes,
        "whole_original_exits": {pair[0]["original"]: [p["exit"] for p in pair] for pair in pairs
                                if pair[0]["original"] in ORIGINALS}
    }, sort_keys=True), flush=True)

if __name__ == "__main__":
    main()
