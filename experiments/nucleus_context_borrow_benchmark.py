#!/usr/bin/env python3
"""Source-pinned Nucleus Cow-context A/B: strict verdict parity and selected guest Ir."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

PIN = "ff003e7fad888d39a40cfd2375885fe20e3209fa"
INPUTS = Path("/tmp/nucleus-cow-inputs")
EVIDENCE = Path("/tmp/nucleus-cow-evidence")
BASE = Path("/tmp/nucleus-baseline")
CANDIDATE = Path("/tmp/nucleus-candidate")
BASELINE_REPORT = Path("baseline/metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
CENSUS = Path("/tmp/nucleus-context-census/context-census.json")
EVIDENCE.mkdir(parents=True, exist_ok=True)
result = {"status": "UNKNOWN", "source_pin": PIN, "comparisons": [], "cost": []}

def check(exe, path, timeout=180):
    with path.open("rb") as source:
        proc = subprocess.run([str(exe)], stdin=source, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=timeout)
    return proc.returncode

def count_guest_ir(exe, inp, label):
    output = EVIDENCE / (label + ".callgrind")
    with inp.open("rb") as stdin:
        proc = subprocess.run(
            ["valgrind", "--tool=callgrind", "--callgrind-out-file=" + str(output),
             "--log-file=" + str(EVIDENCE / (label + ".valgrind.log")), str(exe)],
            stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=900,
        )
    assert proc.returncode == 0, f"callgrind {label} verdict {proc.returncode}"
    data = output.read_text()
    measurements = re.findall(r"^summary:\s*(\d+)", data, flags=re.MULTILINE)
    assert measurements, f"missing guest Ir summary {label}"
    return int(measurements[-1])

try:
    baseline = json.loads(BASELINE_REPORT.read_text())["modes"]["default"]["rows"]
    census = json.loads(CENSUS.read_text())
    assert census["status"] == "WARRANTED_BOUNDED_CONTEXT_COPY_CENSUS"
    assert census["source_commit"] == PIN
    assert len(census["records"]) == len(baseline) == 196
    old = {row["case"]: row for row in census["records"]}
    for n, row in enumerate(baseline):
        case = row["case"]
        path = INPUTS / case
        assert path.is_file(), f"input missing {path}"
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual_hash == row["sha256"] == old[case]["sha256"], f"hash drift {case}"
        b = check(BASE, path)
        c = check(CANDIDATE, path)
        assert b == c == row["rc"], f"verdict mismatch {case}: baseline={b} candidate={c} expected={row['rc']}"
        result["comparisons"].append({"case": case, "sha256": actual_hash,
                                      "expected": row["rc"], "baseline": b, "candidate": c})
        if n % 50 == 0: print(f"paired verdicts {n+1}/196", flush=True)
    result["parity"] = "WARRANTED_FROZEN196_SOURCE_HASH_AND_VERDICT_PARITY"
    candidates = []
    for row in baseline:
        name = row["case"]
        path = INPUTS / name
        if row["rc"] == 0 and path.stat().st_size <= 2_000_000:
            candidates.append((old[name]["slots_cloned"], name, path))
    candidates.sort(reverse=True)
    chosen = [(count, name, path) for count, name, path in candidates if count > 100]
    assert len(chosen) >= 3 and len(candidates) >= 12, "insufficient pinned accepted cases"
    # Previously qualified top three plus predeclared holdouts sampled across
    # the accepted-copy distribution, including the lowest-copy case.
    positions = [0, 1, 2, len(candidates)//4, len(candidates)//2,
                 3*len(candidates)//4, len(candidates)-1]
    selected = [candidates[i] for i in positions]
    assert len({name for _, name, _ in selected}) == len(selected)
    result["selection"] = {"rule": "top-three plus accepted quartiles and minimum",
                           "indices": positions, "eligible_count": len(candidates)}
    for index, (count, name, path) in enumerate(selected):
        base_ir = count_guest_ir(BASE, path, f"case{index}-baseline")
        cand_ir = count_guest_ir(CANDIDATE, path, f"case{index}-candidate")
        ratio = cand_ir / base_ir
        receipt = {"case": name, "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                   "context_slots_cloned_in_v1": count, "selection_index": positions[index], "baseline_guest_ir": base_ir,
                   "candidate_guest_ir": cand_ir, "candidate_div_baseline": ratio}
        result["cost"].append(receipt)
        print(json.dumps(receipt), flush=True)
    result["status"] = "WARRANTED_BOUNDED_PAIRED_GUEST_IR"
    status = 0
except Exception as error:
    result["error"] = repr(error)
    status = 1
finally:
    (EVIDENCE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print("FINAL", result["status"], flush=True)
sys.exit(status)
