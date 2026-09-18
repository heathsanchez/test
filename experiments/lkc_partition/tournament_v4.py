#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"experiments/lkc_partition/generated/Submission_v4.lean"
BENCH=ROOT/"bench"; UPSTREAM=BENCH/".cache/upstream"
EVIDENCE=ROOT/"partition-v4-evidence"
INPUTS=[14,18,22,26,32,36]
EVIDENCE.mkdir(exist_ok=True)

def save(name,obj):
    (EVIDENCE/name).write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps(obj,indent=2),flush=True)

def diagnostic(metric):
    sys.path.insert(0,str(BENCH)); from lkc_bench import cli
    out=EVIDENCE/f"{metric}-diagnostic"
    code=cli.main(["diagnostic","--problem","partition","--submission",str(SOURCE),
                   "--metric",metric,"--repetitions","3","--timeout","600","--memory-mb","4096",
                   "--inputs",*map(str,INPUTS),"--output",str(out)])
    data=json.loads((out/"diagnostic.json").read_text())
    if code!=0 or not data.get("complete"): raise RuntimeError(f"incomplete {metric}")
    return {"metric":metric,"totals":data["totals"],
            "ratio":data["totals"]["candidate"]/data["totals"]["baseline"],
            "reduction_pct":100*(1-data["totals"]["candidate"]/data["totals"]["baseline"]),
            "comparisons":data.get("comparisons"),
            "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest()}

def screen(): save("wall-screen.json",diagnostic("wall-time"))
def instructions():
    r=diagnostic("callgrind")
    r.update(official_pmu_measured=False,local_promotion_eligible=r["ratio"]<1.0)
    save("instruction-verdict.json",r)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("phase",choices=["screen","instructions"]);globals()[p.parse_args().phase]()
