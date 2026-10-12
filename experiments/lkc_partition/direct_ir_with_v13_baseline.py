#!/usr/bin/env python3
"""Source-pinned benchmark adapter: replace ONLY the baseline source with V13.

The independent expected-value oracle, Lean toolchain, export, axiom audit,
timer, and Valgrind instruction collection remain the pinned upstream code.
This is a local developmental measurement, not an official SAIR result.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
BENCH=ROOT/"bench"
sys.path.insert(0,str(BENCH))
from lkc_bench import diagnostic as dg

SOURCES={
 "packed_division":"Submission_packed_division_probe.lean",
 "packed_euler_sparse":"Submission_packed_euler_sparse_probe.lean",
}
V13=ROOT/"experiments/lkc_partition/generated/Submission_v13.lean"
EXPECTED_V13="bcb6325b9d0ca5c7259b0de76d903ba5cb20e05fdb60938b5201745d00491085"

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--arm",choices=list(SOURCES),required=True)
    ap.add_argument("--repetitions",type=int,default=1)
    ap.add_argument("--inputs",nargs="+",type=int,default=[14,22,32,36])
    opts=ap.parse_args()
    if sha(V13)!=EXPECTED_V13:
        raise SystemExit("Unqualified V13 baseline source")
    challenger=ROOT/"experiments/lkc_partition/generated"/SOURCES[opts.arm]
    assert challenger.exists() and challenger.stat().st_size<=1048576
    root=ROOT/"quick-ir-phase-v1"
    root.mkdir(exist_ok=True)
    # Only replace the SOURCE of the baseline arm, not the judge, axioms,
    # expected values, or source of the candidate.
    previous=dg.official_baseline
    dg.official_baseline=lambda problem: V13 if problem=="partition" else previous(problem)
    inputs=list(opts.inputs)
    report=dg.run_diagnostic(
        SimpleNamespace(problem="partition",metric="callgrind",baseline="example",
                        submission=challenger,inputs=inputs,repetitions=opts.repetitions,
                        timeout=240,memory_mb=4096,preparation_memory_mb=4096),
        BENCH/".cache/upstream",
        root/opts.arm)
    source_bindings={r["role"]:r["source_sha256"] for r in report["runs"]}
    assert source_bindings["baseline"]==EXPECTED_V13
    assert source_bindings["candidate"]==sha(challenger)
    note={"arm":opts.arm,"inputs":inputs,"developmental_source_override":"V13 qualified source only",
          "upstream_judge_and_output_reference_unchanged":True,
          "v13_sha256":EXPECTED_V13,
          "candidate_sha256":sha(challenger),
          "report_complete":report["complete"],
          "totals":report["totals"],
          "semantic_note":"Finite external tests, not a universal Lean proof",
          "metric_note":"Callgrind Ir proxy, NOT SAIR official PMU"}
    root.joinpath(opts.arm+"-attestation.json").write_text(json.dumps(note,indent=2)+"\n")
    print(json.dumps(note,indent=2))
    if not report["complete"]:
        raise SystemExit("Source or candidate case failed; evidence retained")

if __name__=="__main__":
    main()
