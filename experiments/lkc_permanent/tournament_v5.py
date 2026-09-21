#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"experiments/lkc_permanent/generated/Submission_v5.lean"
BENCH=ROOT/"bench"
EVIDENCE=ROOT/"permanent-v5-evidence"
INPUTS=[
  28064292647,26230790088,26754739663,28361232070,29556043951,
  53794586207,54079857374,54224806958,51875434732,54751654040,
  71077100717,72835838140,72703668916,70268834944,69508517010,
]
STABLE=[28064292647,26230790088,53794586207,54079857374,71077100717,72835838140]
EVIDENCE.mkdir(exist_ok=True)

def save(name,obj):
    (EVIDENCE/name).write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps(obj,indent=2),flush=True)

def diagnostic(metric,repetitions,inputs,label):
    sys.path.insert(0,str(BENCH))
    from lkc_bench import cli
    out=EVIDENCE/f"{metric}-{label}"
    code=cli.main([
      "diagnostic","--problem","permanent","--submission",str(SOURCE),
      "--metric",metric,"--repetitions",str(repetitions),
      "--timeout","900","--memory-mb","8192",
      "--inputs",*map(str,inputs),"--output",str(out)
    ])
    return code,json.loads((out/"diagnostic.json").read_text())

def resource_probe():
    code,data=diagnostic("wall-time",1,INPUTS,"full15")
    candidate=next((r for r in data.get("runs",[]) if r.get("role")=="candidate"),{})
    baseline=next((r for r in data.get("runs",[]) if r.get("role")=="baseline"),{})
    cstatus={str(c.get("n")):c.get("status") for c in candidate.get("cases",[])}
    bstatus={str(c.get("n")):c.get("status") for c in baseline.get("cases",[])}
    save("resource-probe.json",{
      "complete":bool(data.get("complete")),"returncode":code,
      "candidate_case_status":cstatus,"baseline_case_status":bstatus,
      "comparisons":data.get("comparisons"),"runs":data.get("runs"),
      "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      "official_pmu_measured":False
    })

def instructions():
    code,data=diagnostic("callgrind",3,STABLE,"cross-scale6")
    if code!=0 or not data.get("complete"):
        raise RuntimeError("cross-scale Permanent Callgrind incomplete")
    b=data["totals"]["baseline"]; c=data["totals"]["candidate"]
    save("instruction-verdict.json",{
      "metric":"callgrind","inputs":STABLE,
      "baseline":b,"candidate":c,
      "ratio":c/b,"reduction_pct":100*(1-c/b),
      "comparisons":data.get("comparisons"),
      "local_promotion_eligible":c<b,
      "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      "official_pmu_measured":False
    })

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("phase",choices=["resource_probe","instructions"])
    globals()[p.parse_args().phase]()
