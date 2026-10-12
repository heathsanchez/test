#!/usr/bin/env python3
"""Run source-controlled V4 degree-aware -> V5 factored Horner Euler instruction measurements.

The pinned public evaluator, reference values, official Lean export, axiom audit
and Callgrind collection are unchanged. This only substitutes already vetted
degree Euler V4 as the *developmental comparison source*.
"""
from __future__ import annotations

import argparse,hashlib,json,sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
BENCH=ROOT/"bench"
sys.path.insert(0,str(BENCH))
from lkc_bench import diagnostic as dg

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--arm",choices=("fixed40_horner","fixed57_horner","fixed57_flat","stage26_40_57_horner"),required=True)
    p.add_argument("--repetitions",type=int,default=1)
    p.add_argument("--inputs",nargs="+",type=int,default=[14,22,36])
    args=p.parse_args()
    src=ROOT/"experiments/lkc_partition/generated"
    baseline=src/"Submission_euler_degree_degree_probe.lean"
    challenger=src/f"Submission_fixed_euler_{args.arm}_probe.lean"
    assert baseline.exists() and challenger.exists()
    assert baseline.read_bytes()!=challenger.read_bytes()
    frozen=json.loads((src/"fixed_euler_v6_finite.json").read_text())
    assert sha(challenger)==frozen["arms"][args.arm]["sha256"]
    dg.official_baseline=lambda problem: baseline if problem=="partition" else (_ for _ in ()).throw(ValueError(problem))
    out=ROOT/"fixed-ir-v6"/args.arm
    out.parent.mkdir(parents=True,exist_ok=True)
    report=dg.run_diagnostic(
        SimpleNamespace(problem="partition",metric="callgrind",baseline="example",
                        submission=challenger,inputs=args.inputs,repetitions=args.repetitions,
                        timeout=240,memory_mb=4096,preparation_memory_mb=4096),
        BENCH/".cache/upstream",out)
    assert report["metric"]=="callgrind"
    assert report["runs"][0]["source_sha256"]==sha(baseline)
    assert report["runs"][1]["source_sha256"]==sha(challenger)
    result={
        "arm":args.arm,"v4_sha256":sha(baseline),"candidate_sha256":sha(challenger),
        "development_only":True,"pin":"Lean 4.33.1 / bench d8ea5fc","inputs":args.inputs,
        "complete":report["complete"],"totals":report["totals"],"ratio":None,
        "universal_proof":False,"official_PMU":False,"official_submission":False}
    if report["complete"]:
        result["ratio"]=float(report["totals"]["candidate"])/float(report["totals"]["baseline"])
    (out.parent/f"{args.arm}-attestation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if not report["complete"]:raise SystemExit(1)

if __name__=="__main__":
    main()
