#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"experiments/lkc_fib/generated/Submission_v2.lean"
BENCH=ROOT/"bench"; UPSTREAM=BENCH/".cache/upstream"; PACKAGE=UPSTREAM/"evaluation/problems/fib"
EVIDENCE=ROOT/"fib-v2-evidence"
INPUTS=[5000,10000,20000,40000,80000,150000]
EVIDENCE.mkdir(exist_ok=True)

def save(name,obj):
    (EVIDENCE/name).write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps(obj,indent=2),flush=True)

def execute(cmd,log,cwd=ROOT,timeout=1200):
    path=EVIDENCE/log
    with path.open("w") as f:
        try:
            r=subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout); code=r.returncode
        except subprocess.TimeoutExpired: code=124
    text=path.read_text(errors="replace"); print(text[-16000:],flush=True); return code,text

def prove():
    original=SOURCE.read_text(); audit=EVIDENCE/"Audit_v2.lean"
    audit.write_text(original+"\n#print axioms Submission.impl_correct\n"
                     +"example : Submission.impl 10 = 55 := by decide +kernel\n"
                     +"example : Submission.impl 100 = 354224848179261915075 := by decide +kernel\n")
    code,text=execute(["lake","env","lean","-DautoImplicit=false","-DwarningAsError=true",str(audit)],"proof.log",cwd=PACKAGE)
    m=re.search(r"depends on axioms:\s*\[([^\]]*)\]",text); free="does not depend on any axioms" in text
    axioms=({x.strip() for x in m.group(1).split(",") if x.strip()} if m else set())
    passed=code==0 and (m is not None or free) and axioms <= {"propext","Quot.sound","Classical.choice"}
    caught=False
    if passed:
        bad=EVIDENCE/"Negative_v2.lean"; bad.write_text(original+"\nexample : Submission.impl 10 = 54 := by decide +kernel\n")
        bc,bt=execute(["lake","env","lean","-DautoImplicit=false","-DwarningAsError=true",str(bad)],"negative.log",cwd=PACKAGE)
        caught=bc not in (0,124) and "error:" in bt; passed=passed and caught
    save("proof-gate.json",{"proof_pass":passed,"negative_control_rejected":caught,"axioms":sorted(axioms),"source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest()})
    if not passed: raise RuntimeError("Fib V2 proof gate failed")

def diagnostic(metric):
    sys.path.insert(0,str(BENCH)); from lkc_bench import cli
    out=EVIDENCE/f"{metric}-official"
    code=cli.main(["diagnostic","--problem","fib","--submission",str(SOURCE),"--metric",metric,
                   "--repetitions","3","--timeout","600","--memory-mb","4096","--inputs",*map(str,INPUTS),"--output",str(out)])
    data=json.loads((out/"diagnostic.json").read_text())
    if code!=0 or not data.get("complete"): raise RuntimeError(f"incomplete {metric}")
    return {"metric":metric,"totals":data["totals"],"ratio":data["totals"]["candidate"]/data["totals"]["baseline"],
            "reduction_pct":100*(1-data["totals"]["candidate"]/data["totals"]["baseline"]),
            "comparisons":data.get("comparisons"),"source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest()}

def screen(): save("wall-screen.json",diagnostic("wall-time"))

def qualify():
    code,text=execute(["python3","evaluation/run.py","--problem","fib","--submission",str(SOURCE),"--timeout","180"],"canonical.log",cwd=UPSTREAM,timeout=2400)
    ok=code==0 and ": accepted" in text; save("canonical.json",{"accepted":ok})
    if not ok: raise RuntimeError("Fib V2 canonical failed")

def instructions():
    result=diagnostic("callgrind")
    result.update(official_pmu_measured=False,local_promotion_eligible=result["ratio"]<1.0)
    save("instruction-verdict.json",result)

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("phase",choices=["prove","screen","qualify","instructions"]); globals()[p.parse_args().phase]()
