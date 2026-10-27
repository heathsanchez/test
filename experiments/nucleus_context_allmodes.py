#!/usr/bin/env python3
"""Independent Nucleus Cow all-mode source/exit qualification.

188+ checks per mode: genuine frozen196 official Arena exports and protected
adversarial controls. Uses exact historical baseline pinned in the repository.
This gate is solely semantic compatibility, not an Arena performance score.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

PIN = "ff003e7fad888d39a40cfd2375885fe20e3209fa"
ROOT = Path("/tmp/nucleus-cow-inputs")
REPORT = Path("/tmp/nucleus-cow-allmodes-evidence")
BASE = Path("/tmp/nucleus-baseline")
CAND = Path("/tmp/nucleus-candidate")
LEDGER = Path("baseline/metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
PROTECTED = Path("candidate/metatron-kernel/tests/fixtures")
RESULTS = {"status": "UNKNOWN", "source_pin": PIN, "modes": {}}
REPORT.mkdir(parents=True, exist_ok=True)

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def execute(exe, path, environment, seconds=180):
    with path.open("rb") as data:
        proc = subprocess.run(
            [str(exe)], stdin=data, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=seconds, env=environment
        )
    return proc.returncode

try:
    ledger = json.loads(LEDGER.read_text())
    modes = ledger["modes"]
    flags = ledger["origin_flags"]
    assert set(["default", "origin", "demand"]) <= set(modes)
    assert len(flags) >= 10
    clean = {k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    for mode in ["default", "origin", "demand"]:
        env = dict(clean)
        if mode != "default":
            env.update({"NUCLEUS_EXPERIMENTAL_" + name: "1" for name in flags})
        if mode == "demand":
            env["NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR"] = "1"
        expected = modes[mode]["rows"]
        assert len(expected) == 196, (mode, len(expected))
        rows = []
        for i, entry in enumerate(expected):
            path = ROOT / entry["case"]
            assert path.is_file(), f"missing pinned source {path}"
            sha = digest(path)
            assert sha == entry["sha256"], f"source hash drift {entry['case']}"
            b = execute(BASE, path, env)
            c = execute(CAND, path, env)
            assert b == c == entry["rc"], {
                "case": entry["case"], "mode": mode,
                "expected": entry["rc"], "baseline": b, "candidate": c
            }
            rows.append({"case": entry["case"], "sha256": sha,
                         "expected": entry["rc"], "baseline": b, "candidate": c})
            if i % 50 == 0:
                print(f"{mode}: {i+1}/196 matched", flush=True)
        negatives = []
        for name in ["protected-false-index.ndjson", "protected-eta-ctor-alias.ndjson"]:
            path = PROTECTED / name
            assert path.is_file(), f"missing protected control {name}"
            b = execute(BASE, path, env)
            c = execute(CAND, path, env)
            assert b == c and b in (1, 2), {
                "control": name, "mode": mode, "baseline": b, "candidate": c
            }
            negatives.append({"case": name, "sha256": digest(path), "baseline": b, "candidate": c})
        counts = {
            "accept": sum(r["candidate"] == 0 for r in rows),
            "reject": sum(r["candidate"] == 1 for r in rows),
            "unknown": sum(r["candidate"] == 2 for r in rows),
            "error": sum(r["candidate"] not in [0, 1, 2] for r in rows)
        }
        if mode == "default":
            assert counts == {"accept": 118, "reject": 71, "unknown": 7, "error": 0}, counts
        else:
            assert counts == {"accept": 119, "reject": 71, "unknown": 6, "error": 0}, counts
        RESULTS["modes"][mode] = {"counts": counts, "cases": rows, "protected": negatives}
        print(json.dumps({"mode": mode, "counts": counts, "protected": negatives}), flush=True)
    RESULTS["status"] = "WARRANTED_BOUNDED_ALL196_THREE_MODES"
    exit_code = 0
except Exception as error:
    RESULTS["error"] = repr(error)
    exit_code = 1
finally:
    (REPORT / "allmodes.json").write_text(json.dumps(RESULTS, indent=2) + "\n")
    print("FINAL", RESULTS["status"], flush=True)
sys.exit(exit_code)
