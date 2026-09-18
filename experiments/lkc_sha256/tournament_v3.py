#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"experiments/lkc_sha256/generated/Submission_v3.lean"
BENCH=ROOT/"bench"; UPSTREAM=BENCH/".cache/upstream"; PACKAGE=UPSTREAM/"evaluation/problems/sha256"
EVIDENCE=ROOT/"sha256-v3-evidence"
INPUTS=[18860801433,17252521710,138725260120,140599404248,2199121876686,2199573357346]
EVIDENCE.mkdir(exist_ok=True)

def save(name,obj):
    (EVIDENCE/name).write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps(obj,indent=2),flush=True)

def execute(cmd,log,cwd=ROOT,timeout=2400):
    path=EVIDENCE/log
    with path.open("w") as f:
        try:
            r=subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout); code=r.returncode
        except subprocess.TimeoutExpired: code=124
    text=path.read_text(errors="replace"); print(text[-20000:],flush=True); return code,text

def prove():
    original=SOURCE.read_text(); audit=EVIDENCE/"Audit_v3.lean"
    audit.write_text(original+"\n#print axioms Submission.impl_correct\n"
                     +"example : Submission.impl 4294967297 = sha256Spec 4294967297 := by decide +kernel\n")
    code,text=execute(["lake","env","lean","-DautoImplicit=false","-DwarningAsError=true",
                       "-DmaxRecDepth=4000000","-DmaxHeartbeats=0",str(audit)],
                      "proof.log",cwd=PACKAGE,timeout=2400)
    m=re.search(r"depends on axioms:\s*\[([^\]]*)\]",text); free="does not depend on any axioms" in text
    axioms=({x.strip() for x in m.group(1).split(",") if x.strip()} if m else set())
    passed=code==0 and (m is not None or free) and axioms <= {"propext","Quot.sound","Classical.choice"}
    caught=False
    if passed:
        bad=EVIDENCE/"Negative_v3.lean"; bad.write_text(original+"\nexample : Submission.impl 4294967297 = 0 := by decide +kernel\n")
        bc,bt=execute(["lake","env","lean","-DautoImplicit=false","-DwarningAsError=true",
                       "-DmaxRecDepth=4000000","-DmaxHeartbeats=0",str(bad)],
                      "negative.log",cwd=PACKAGE,timeout=2400)
        caught=bc not in (0,124) and "error:" in bt
        passed=passed and caught
    save("proof-gate.json",{"proof_pass":passed,"negative_control_rejected":caught,
         "axioms":sorted(axioms),"source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest()})
    if not passed: raise RuntimeError("SHA packed V3 proof gate failed")

def qualify():
    code,text=execute(["python3","evaluation/run.py","--problem","sha256",
                       "--submission",str(SOURCE),"--timeout","300"],
                      "canonical.log",cwd=UPSTREAM,timeout=5400)
    ok=code==0 and ": accepted" in text and "Computation replay T:" in text
    save("canonical.json",{"accepted":ok,"returncode":code})
    if not ok: raise RuntimeError("SHA packed V3 canonical acceptance failed")

def diagnostic(metric,repetitions,label):
    sys.path.insert(0,str(BENCH)); from lkc_bench import cli
    out=EVIDENCE/f"{metric}-{label}"
    code=cli.main(["diagnostic","--problem","sha256","--submission",str(SOURCE),
                   "--metric",metric,"--repetitions",str(repetitions),"--timeout","900",
                   "--memory-mb","4096","--inputs",*map(str,INPUTS),"--output",str(out)])
    data=json.loads((out/"diagnostic.json").read_text())
    return code,data

def resource_probe():
    code,data=diagnostic("wall-time",1,"full-resource")
    candidate=next((r for r in data.get("runs",[]) if r.get("role")=="candidate"),{})
    case_status={str(c.get("n")):c.get("status") for c in candidate.get("cases",[])}
    complete=all(case_status.get(str(n))=="complete" for n in INPUTS)
    save("resource-probe.json",{
      "candidate_full_complete":complete,"diagnostic_complete":bool(data.get("complete")),
      "returncode":code,"case_status":case_status,"runs":data.get("runs"),
      "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    })
    if not complete: raise RuntimeError("SHA packed V3 did not clear the full resource boundary")

def instructions():
    probe=json.loads((EVIDENCE/"resource-probe.json").read_text())
    if not probe["candidate_full_complete"]: raise RuntimeError("full resource gate missing")
    code,data=diagnostic("callgrind",3,"full")
    # Baseline may remain incomplete on the two 512-step cases. Preserve per-case evidence either way.
    candidate=next((r for r in data.get("runs",[]) if r.get("role")=="candidate"),{})
    case_status={str(c.get("n")):c.get("status") for c in candidate.get("cases",[])}
    cand_complete=all(case_status.get(str(n))=="complete" for n in INPUTS)
    result={
      "diagnostic_complete":bool(data.get("complete")),"returncode":code,
      "candidate_full_complete":cand_complete,"totals":data.get("totals"),
      "comparisons":data.get("comparisons"),"runs":data.get("runs"),
      "official_pmu_measured":False,
      "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    }
    save("instruction-verdict.json",result)
    if not cand_complete: raise RuntimeError("SHA packed V3 Callgrind candidate incomplete")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("phase",choices=["prove","qualify","resource_probe","instructions"]);globals()[p.parse_args().phase]()
