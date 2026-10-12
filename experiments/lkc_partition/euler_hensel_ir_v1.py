#!/usr/bin/env python3
"""Controlled Callgrind comparison: accepted Euler sparse quotient V1 vs Hensel V1.

Only algorithm evaluation; no universal theorem or formal SAIR submission.
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
    p.add_argument("--arm",choices=("standard","narrow"),required=True)
    p.add_argument("--inputs",type=int,nargs="+",default=[14,22,36])
    a=p.parse_args()
    src=ROOT/"experiments/lkc_partition/generated"
    incumbent=src/"Submission_packed_euler_sparse_probe.lean"
    challenger=src/f"Submission_euler_hensel_{a.arm}_probe.lean"
    finite=json.loads((src/"euler_hensel_v1_finite.json").read_text())
    assert sha(challenger)==finite["arms"][a.arm]["source_sha256"]
    assert incumbent.exists()
    dg.official_baseline=lambda problem:incumbent if problem=="partition" else (_ for _ in ()).throw(ValueError(problem))
    root=ROOT/"hensel-ir-v1"
    root.mkdir(exist_ok=True,parents=True)
    out=root/a.arm
    report=dg.run_diagnostic(
        SimpleNamespace(problem="partition",metric="callgrind",baseline="example",
                        submission=challenger,inputs=a.inputs,repetitions=1,
                        timeout=240,memory_mb=4096,preparation_memory_mb=4096),
        BENCH/".cache/upstream",out)
    baseline=next(x for x in report["runs"] if x["role"]=="baseline")
    actual=next(x for x in report["runs"] if x["role"]=="candidate")
    assert baseline["source_sha256"]==sha(incumbent)
    assert actual["source_sha256"]==sha(challenger)
    result={
      "arm":a.arm,"inputs":a.inputs,
      "boundaries":{"universal_Lean_proof":False,"official_PMU":False,"submission":False},
      "baseline_sha256":sha(incumbent),"candidate_sha256":sha(challenger),
      "complete":report["complete"],"ratio":None,"totals":report["totals"]}
    if report["complete"]:
        result["ratio"]=float(report["totals"]["candidate"])/float(report["totals"]["baseline"])
    (root/f"{a.arm}-attestation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if not report["complete"]: raise SystemExit("Missing same-input evidence")

if __name__=="__main__":
    main()
