#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"experiments/lkc_sha256/generated/Submission_v5.lean"
BENCH=ROOT/"bench"
EVIDENCE=ROOT/"sha256-v5-evidence"
INPUTS=[18860801433,17252521710,138725260120,140599404248,2199121876686,2199573357346]
STABLE=INPUTS[:4]
EVIDENCE.mkdir(exist_ok=True)

def save(name,obj):
    (EVIDENCE/name).write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps(obj,indent=2),flush=True)

def diagnostic(metric,repetitions,inputs,label):
    sys.path.insert(0,str(BENCH))
    from lkc_bench import cli
    out=EVIDENCE/f"{metric}-{label}"
    code=cli.main([
      "diagnostic","--problem","sha256","--submission",str(SOURCE),
      "--metric",metric,"--repetitions",str(repetitions),
      "--timeout","900","--memory-mb","4096",
      "--inputs",*map(str,inputs),"--output",str(out)
    ])
    data=json.loads((out/"diagnostic.json").read_text())
    return code,data

def resource_probe():
    code,data=diagnostic("wall-time",1,INPUTS,"full6")
    candidate=next((r for r in data.get("runs",[]) if r.get("role")=="candidate"),{})
    baseline=next((r for r in data.get("runs",[]) if r.get("role")=="baseline"),{})
    cstatus={str(c.get("n")):c.get("status") for c in candidate.get("cases",[])}
    bstatus={str(c.get("n")):c.get("status") for c in baseline.get("cases",[])}
    cand_complete=all(cstatus.get(str(n))=="complete" for n in INPUTS)
    result={
      "candidate_full_complete":cand_complete,
      "diagnostic_complete":bool(data.get("complete")),
      "returncode":code,
      "candidate_case_status":cstatus,
      "baseline_case_status":bstatus,
      "runs":data.get("runs"),
      "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      "official_pmu_measured":False
    }
    save("resource-probe.json",result)
    if not cand_complete:
        raise RuntimeError("SHA V5 candidate still fails at least one full-contract resource case")

def instructions():
    probe=json.loads((EVIDENCE/"resource-probe.json").read_text())
    if not probe["candidate_full_complete"]:
        raise RuntimeError("full resource gate not passed")
    code,data=diagnostic("callgrind",3,STABLE,"stable4")
    if code!=0 or not data.get("complete"):
        raise RuntimeError("stable-four SHA Callgrind incomplete")
    b=data["totals"]["baseline"]; c=data["totals"]["candidate"]
    save("instruction-verdict.json",{
      "metric":"callgrind","inputs":STABLE,
      "baseline":b,"candidate":c,"ratio":c/b,
      "reduction_pct":100*(1-c/b),
      "comparisons":data.get("comparisons"),
      "candidate_full_resource_complete":True,
      "local_promotion_eligible":c<b,
      "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      "official_pmu_measured":False
    })

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("phase",choices=["resource_probe","instructions"])
    globals()[p.parse_args().phase]()
