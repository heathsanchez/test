#!/usr/bin/env python3
"""Frozen-196 SHA/verdict-gated, per-site Nucleus context-copy census.

Two binaries are compiled from the same exact qualified source; the diagnostic
binary retains original Vec cloning and emits only observational counters.
This is NOT an Arena retired-instruction or Mathlib speed benchmark.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

INPUTS = Path(os.environ.get("INPUTS", "/tmp/nucleus-context-inputs"))
OUTPUT = Path(os.environ.get("OUTPUT", "/tmp/nucleus-context-evidence"))
BASE = Path(os.environ.get("BASE", "/tmp/nucleus-baseline"))
PROFILE = Path(os.environ.get("PROFILE", "/tmp/nucleus-profile"))
PIN = Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
OUTPUT.mkdir(exist_ok=True, parents=True)
records = []
report = {
    "status": "UNKNOWN",
    "source_commit": "ff003e7fad888d39a40cfd2375885fe20e3209fa",
    "scope": "frozen196 default mode; diagnostic counters measure cloning frequency only",
    "records": records,
}
try:
    source = json.loads(PIN.read_text())
    cases = source["modes"]["default"]["rows"]
    assert len(cases) == 196, f"expected frozen196 got {len(cases)}"
    for ordinal, row in enumerate(cases):
        path = INPUTS / row["case"]
        assert path.is_file(), f"missing input {path}"
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        assert sha == row["sha256"], f"source-hash mismatch {path}"
        with path.open("rb") as inp:
            a = subprocess.run([str(BASE)], stdin=inp, capture_output=True, timeout=180)
        with path.open("rb") as inp:
            b = subprocess.run([str(PROFILE)], stdin=inp, capture_output=True, timeout=180,
                               env={**os.environ, "METATRON_KERNEL_DIAGNOSTICS": "1"})
        assert a.returncode == b.returncode == row["rc"], (
            f"verdict mismatch {row['case']}: base={a.returncode}, "
            f"instrumented={b.returncode}, expected={row['rc']}"
        )
        found = re.findall(
            r"NUCLEUS_CONTEXT_COST_JSON:(\{[^\n]+\})",
            b.stderr.decode(errors="replace"),
        )
        assert len(found) == 1, f"missing or repeated counter receipt: {row['case']}"
        counts = json.loads(found[0])
        assert counts["copy_sites"] == 7
        copies, slots, widest = (
            counts["copies_by_site"], counts["slots_by_site"], counts["widest_by_site"]
        )
        assert len(copies) == len(slots) == len(widest) == 7
        assert all(isinstance(x, int) and x >= 0 for x in copies+slots+widest)
        entry = {
            "case": row["case"], "sha256": sha, "verdict": row["rc"],
            "copies_by_site": copies, "slots_by_site": slots,
            "widest_by_site": widest, "copies": sum(copies), "slots_cloned": sum(slots),
        }
        records.append(entry)
        if ordinal % 25 == 0:
            print(f"checked {ordinal+1}/196 {row['case']} slots={entry['slots_cloned']}", flush=True)
    totals = {
        "cases": len(records),
        "context_copies": sum(r["copies"] for r in records),
        "context_slots_cloned": sum(r["slots_cloned"] for r in records),
        "nonzero_cases": sum(r["slots_cloned"] > 0 for r in records),
        "peak_context_width": max(max(r["widest_by_site"]) for r in records),
        "copies_by_site": [
            sum(r["copies_by_site"][i] for r in records) for i in range(7)
        ],
        "slots_by_site": [
            sum(r["slots_by_site"][i] for r in records) for i in range(7)
        ],
    }
    report["totals"] = totals
    report["most_slots_cloned"] = sorted(
        records, key=lambda r: r["slots_cloned"], reverse=True
    )[:20]
    report["status"] = "WARRANTED_BOUNDED_CONTEXT_COPY_CENSUS"
    print(json.dumps(totals, indent=2), flush=True)
    rc = 0
except Exception as error:
    report["error"] = repr(error)
    rc = 1
finally:
    (OUTPUT/"context-census.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Final status:", report["status"], flush=True)
sys.exit(rc)
