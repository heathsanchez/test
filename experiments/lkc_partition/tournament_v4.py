#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"experiments/lkc_partition/generated/Submission_v4.lean"
BENCH=ROOT/"bench"; UPSTREAM=BENCH/".cache/upstream"
EVIDENCE=ROOT/"partition-v4-evidence"
INPUTS=[14,18,22,26,32,36]
STABLE_INPUTS=INPUTS[:5]
EVIDENCE.mkdir(exist_ok=True)

def save(name,obj):
    (EVIDENCE/name).write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps(obj,indent=2),flush=True)

def diagnostic(metric, inputs, label):
    sys.path.insert(0,str(BENCH)); from lkc_bench import cli
    out=EVIDENCE/f"{metric}-{label}"
    code=cli.main(["diagnostic","--problem","partition","--submission",str(SOURCE),
                   "--metric",metric,"--repetitions","3","--timeout","600","--memory-mb","4096",
                   "--inputs",*map(str,inputs),"--output",str(out)])
    data=json.loads((out/"diagnostic.json").read_text())
    return code,data

def resource_probe():
    code,data=diagnostic("wall-time",INPUTS,"full")
    result={
      "complete":bool(data.get("complete")),"returncode":code,
      "comparisons":data.get("comparisons"),"runs":data.get("runs"),
      "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      "classification":"RESOURCE_DOMINANCE_IF_CANDIDATE_COMPLETES_36_AND_BASELINE_DOES_NOT"
    }
    save("resource-probe.json",result)

def instructions():
    code,data=diagnostic("callgrind",STABLE_INPUTS,"stable5")
    if code!=0 or not data.get("complete"): raise RuntimeError("stable-five Callgrind incomplete")
    b=data["totals"]["baseline"]; cand=data["totals"]["candidate"]
    r={"metric":"callgrind","inputs":STABLE_INPUTS,"baseline":b,"candidate":cand,
       "ratio":cand/b,"reduction_pct":100*(1-cand/b),"comparisons":data.get("comparisons"),
       "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
       "official_pmu_measured":False,"stable5_promotion_signal":cand<b,
       "full_contract_resource_probe":"resource-probe.json"}
    save("instruction-verdict.json",r)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("phase",choices=["resource_probe","instructions"]);globals()[p.parse_args().phase]()
