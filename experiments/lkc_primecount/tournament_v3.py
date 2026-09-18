#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"experiments/lkc_primecount/generated/Submission_v3.lean"
V1=ROOT/"experiments/lkc_primecount/generated/Submission_v1.lean"
BENCH=ROOT/"bench"; UPSTREAM=BENCH/".cache/upstream"; PACKAGE=UPSTREAM/"evaluation/problems/primecount"
EVIDENCE=ROOT/"primecount-v3-evidence"
INPUTS=[50,100,150,300,600,1000]
EVIDENCE.mkdir(exist_ok=True)

def save(name,obj):
    (EVIDENCE/name).write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps(obj,indent=2),flush=True)

def execute(cmd,log,cwd=ROOT,timeout=1800):
    p=EVIDENCE/log
    with p.open("w") as f:
        try:
            r=subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout); code=r.returncode
        except subprocess.TimeoutExpired: code=124
    text=p.read_text(errors="replace"); print(text[-18000:],flush=True); return code,text

def prove():
    original=SOURCE.read_text(); audit=EVIDENCE/"Audit_v3.lean"
    audit.write_text(original+"\n#print axioms Submission.impl_correct\n"
                     +"example : Submission.impl 10 = 4 := by decide +kernel\n"
                     +"example : Submission.impl 50 = 15 := by decide +kernel\n")
    code,text=execute(["lake","env","lean","-DautoImplicit=false","-DwarningAsError=true",str(audit)],
                      "proof.log",cwd=PACKAGE,timeout=1800)
    m=re.search(r"depends on axioms:\s*\[([^\]]*)\]",text); free="does not depend on any axioms" in text
    axioms=({x.strip() for x in m.group(1).split(",") if x.strip()} if m else set())
    passed=code==0 and (m is not None or free) and axioms <= {"propext","Quot.sound","Classical.choice"}
    caught=False
    if passed:
        bad=EVIDENCE/"Negative_v3.lean"; bad.write_text(original+"\nexample : Submission.impl 10 = 5 := by decide +kernel\n")
        bc,bt=execute(["lake","env","lean","-DautoImplicit=false","-DwarningAsError=true",str(bad)],
                      "negative.log",cwd=PACKAGE,timeout=1800)
        caught=bc not in (0,124) and "error:" in bt; passed=passed and caught
    save("proof-gate.json",{"proof_pass":passed,"negative_control_rejected":caught,
         "axioms":sorted(axioms),"candidate_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
         "baseline_sha256":hashlib.sha256(V1.read_bytes()).hexdigest()})
    if not passed: raise RuntimeError("Primecount V3 proof gate failed")

def diagnostic(metric):
    sys.path.insert(0,str(BENCH)); from lkc_bench import cli
    from lkc_bench import diagnostic as engine
    original=engine.official_baseline; engine.official_baseline=lambda problem:V1
    try:
        out=EVIDENCE/f"{metric}-v1-v3"
        code=cli.main(["diagnostic","--problem","primecount","--submission",str(SOURCE),
                       "--metric",metric,"--repetitions","3","--timeout","600","--memory-mb","4096",
                       "--inputs",*map(str,INPUTS),"--output",str(out)])
    finally:
        engine.official_baseline=original
    data=json.loads((out/"diagnostic.json").read_text())
    if code!=0 or not data.get("complete"): raise RuntimeError(f"incomplete {metric}")
    b=data["totals"]["baseline"]; c=data["totals"]["candidate"]
    return {"metric":metric,"baseline":b,"candidate":c,"ratio":c/b,
            "reduction_pct":100*(1-c/b),"comparisons":data.get("comparisons"),
            "candidate_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "baseline_sha256":hashlib.sha256(V1.read_bytes()).hexdigest()}

def screen(): save("wall-screen.json",diagnostic("wall-time"))

def qualify():
    code,text=execute(["python3","evaluation/run.py","--problem","primecount","--submission",str(SOURCE),"--timeout","180"],
                      "canonical.log",cwd=UPSTREAM,timeout=2400)
    ok=code==0 and ": accepted" in text
    save("canonical.json",{"accepted":ok,"returncode":code})
    if not ok: raise RuntimeError("Primecount V3 canonical failed")

def instructions():
    if not json.loads((EVIDENCE/"canonical.json").read_text())["accepted"]: raise RuntimeError("missing canonical")
    r=diagnostic("callgrind")
    r.update(official_pmu_measured=False,local_promotion_eligible=r["ratio"]<1.0,
             selected_champion="v3" if r["ratio"]<1.0 else "v1")
    save("instruction-verdict.json",r)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("phase",choices=["prove","screen","qualify","instructions"]);globals()[p.parse_args().phase]()
