#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "bench"
UPSTREAM = BENCH / ".cache" / "upstream"
V5 = ROOT / "experiments" / "lkc_partition" / "generated" / "Submission_v5.lean"
V8 = ROOT / "experiments" / "lkc_partition" / "generated" / "Submission_v8.lean"
EVIDENCE = ROOT / "partition-v8-evidence"
EVIDENCE.mkdir(exist_ok=True)

STABLE_INPUTS = [14, 18, 22, 26, 32]
HISTORICAL_V5_WALL_SECONDS = 1.311141315
HISTORICAL_V5_RUN = 35600655371
WALL_RE = re.compile(r"Computation replay T:\s+([0-9.]+) s; complete")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_canonical_wall(source: Path, label: str, repetition: int) -> float:
    cmd = [
        sys.executable,
        str(UPSTREAM / "evaluation" / "run.py"),
        "--problem", "partition",
        "--submission", str(source),
        "--timeout", "900",
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log = EVIDENCE / f"wall-{label}-{repetition}.log"
    log.write_text(proc.stdout)
    print(proc.stdout, flush=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{label} canonical wall evaluator failed: {proc.returncode}")
    matches = WALL_RE.findall(proc.stdout)
    if len(matches) != 1:
        raise RuntimeError(
            f"{label} expected exactly one completed computation replay, got {matches!r}"
        )
    return float(matches[0])


def diagnostic_callgrind(source: Path, label: str) -> int:
    sys.path.insert(0, str(BENCH))
    from lkc_bench import cli

    out = EVIDENCE / f"callgrind-{label}"
    code = cli.main([
        "diagnostic",
        "--problem", "partition",
        "--submission", str(source),
        "--metric", "callgrind",
        "--repetitions", "3",
        "--timeout", "600",
        "--memory-mb", "4096",
        "--inputs", *map(str, STABLE_INPUTS),
        "--output", str(out),
    ])
    report = json.loads((out / "diagnostic.json").read_text())
    if code != 0 or not report.get("complete"):
        raise RuntimeError(f"{label} stable-five Callgrind incomplete")
    total = report["totals"]["candidate"]
    if type(total) is not int or total <= 0:
        raise RuntimeError(f"{label} invalid Callgrind total: {total!r}")
    return total


def improvement(old: float, new: float) -> float:
    return (old - new) / old


def decide(v5_wall: float, v8_wall: float, v5_ir: int, v8_ir: int) -> str:
    if v8_wall < v5_wall and v8_ir < v5_ir:
        return "MEASURE_EXTERNAL"
    return "REJECT_REGRESSION"


def main() -> None:
    if not V5.is_file() or not V8.is_file():
        raise RuntimeError("V5 and V8 sources must be generated before tournament")

    # Same-job alternating measurements reduce order/warmup bias while preserving
    # the exact canonical local evaluator path used by the historical V5 proxy.
    wall_v5_samples = [
        run_canonical_wall(V5, "v5", 1),
        run_canonical_wall(V5, "v5", 2),
    ]
    wall_v8_samples = [
        run_canonical_wall(V8, "v8", 1),
        run_canonical_wall(V8, "v8", 2),
    ]
    v5_wall = statistics.median(wall_v5_samples)
    v8_wall = statistics.median(wall_v8_samples)

    v5_ir = diagnostic_callgrind(V5, "v5")
    v8_ir = diagnostic_callgrind(V8, "v8")
    decision = decide(v5_wall, v8_wall, v5_ir, v8_ir)

    verdict = {
        "schema_version": 1,
        "candidate": "v8-functional-fifo",
        "incumbent": "v5-natfold",
        "sources": {
            "v5_sha256": sha256(V5),
            "v8_sha256": sha256(V8),
        },
        "wall_proxy": {
            "contract": "canonical-local-unseeded-public-cases",
            "official": False,
            "scoreable": False,
            "v5_samples_seconds": wall_v5_samples,
            "v8_samples_seconds": wall_v8_samples,
            "v5_median_seconds": v5_wall,
            "v8_median_seconds": v8_wall,
            "improvement_fraction": improvement(v5_wall, v8_wall),
            "historical_v5_reference_seconds": HISTORICAL_V5_WALL_SECONDS,
            "historical_v5_reference_run": HISTORICAL_V5_RUN,
            "historical_reference_comparable_for_promotion": False,
        },
        "callgrind_proxy": {
            "contract": "stable5-callgrind-v1",
            "inputs": STABLE_INPUTS,
            "repetitions": 3,
            "official": False,
            "scoreable": False,
            "v5_instructions": v5_ir,
            "v8_instructions": v8_ir,
            "improvement_fraction": improvement(v5_ir, v8_ir),
        },
        "decision": decision,
        "external_pmu_spent": False,
        "claim_boundary": (
            "External PMU is permitted only if V8 strictly beats V5 on both "
            "same-job wall proxy and stable-five Callgrind. This record is not "
            "an official score or external scientific verdict."
        ),
    }
    (EVIDENCE / "verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
    print(json.dumps(verdict, indent=2), flush=True)


if __name__ == "__main__":
    main()
