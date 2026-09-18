#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"experiments/lkc_permanent/generated/Submission_v2.lean"
BENCH=ROOT/"bench"
EVIDENCE=ROOT/"permanent-v2-evidence"
INPUTS=[
28064292647,26230790088,26754739663,28361232070,29556043951,
53794586207,54079857374,54224806958,51875434732,54751654040,
71077100717,72835838140,72703668916,70268834944,69508517010]
STABLE=[n for n in INPUTS if n != 72835838140]
EVIDENCE.mkdir(exist_ok=True)

def save(name,obj):
    (EVIDENCE/name).write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps(obj,indent=2),flush=True)

def diagnostic(metric,inputs,label,memory=8192):
    sys.path.insert(0,str(BENCH)); from lkc_bench import cli
    out=EVIDENCE/f"{metric}-{label}"
    code=cli.main(["diagnostic","--problem","permanent","--submission",str(SOURCE),
                   "--metric",metric,"--repetitions","3","--timeout","900","--memory-mb",str(memory),
                   "--inputs",*map(str,inputs),"--output",str(out)])
    data=json.loads((out/"diagnostic.json").read_text())
    return code,data

def resource_probe():
    code,data=diagnostic("wall-time",INPUTS,"full",8192)
    save("resource-probe.json",{
      "complete":bool(data.get("complete")),"returncode":code,"totals":data.get("totals"),
      "comparisons":data.get("comparisons"),"runs":data.get("runs"),
      "candidate_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    })

def instructions():
    code,data=diagnostic("callgrind",STABLE,"stable14",8192)
    if code!=0 or not data.get("complete"): raise RuntimeError("stable Permanent diagnostic incomplete")
    b=data["totals"]["baseline"]; c=data["totals"]["candidate"]
    save("instruction-verdict.json",{
      "metric":"callgrind","inputs":STABLE,"baseline":b,"candidate":c,
      "ratio":c/b,"reduction_pct":100*(1-c/b),"comparisons":data.get("comparisons"),
      "official_pmu_measured":False,"local_promotion_eligible":c<b,
      "full_contract_resource_probe":"resource-probe.json",
      "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    })

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("phase",choices=["resource_probe","instructions"]); globals()[p.parse_args().phase]()
