#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCES=ROOT/"experiments/lkc_polydisc/generated"
SOURCE=SOURCES/"Submission_v3.lean"; V2=SOURCES/"Submission_v2.lean"
BENCH=ROOT/"bench"; UPSTREAM=BENCH/".cache/upstream"; PACKAGE=UPSTREAM/"evaluation/problems/polydisc"
EVIDENCE=ROOT/"polydisc-v3-evidence"
INPUTS=[19337098,9225987,6476047012455,10487306645701,5042242704654352709,4530401864863699852]
EVIDENCE.mkdir(exist_ok=True)

def save(name,obj):
    (EVIDENCE/name).write_text(json.dumps(obj,indent=2)+"\n"); print(json.dumps(obj,indent=2),flush=True)

def execute(cmd,log,cwd=ROOT,timeout=2400):
    p=EVIDENCE/log
    with p.open("w") as f:
        try:r=subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout);code=r.returncode
        except subprocess.TimeoutExpired:code=124
    text=p.read_text(errors="replace");print(text[-18000:],flush=True);return code,text

def prove():
    original=SOURCE.read_text(); audit=EVIDENCE/"Audit_v3.lean"
    audit.write_text(original+"\n#print axioms Submission.impl_correct\n"
                     +"example : Submission.impl 0 = discSpec 0 := by decide +kernel\n")
    code,text=execute(["lake","env","lean","-DautoImplicit=false","-DwarningAsError=true",str(audit)],
                      "proof.log",cwd=PACKAGE,timeout=2400)
    m=re.search(r"depends on axioms:\s*\[([^\]]*)\]",text); free="does not depend on any axioms" in text
    axioms=({x.strip() for x in m.group(1).split(",") if x.strip()} if m else set())
    passed=code==0 and (m is not None or free) and axioms <= {"propext","Quot.sound","Classical.choice"}
    save("proof-gate.json",{"proof_pass":passed,"axioms":sorted(axioms),
      "candidate_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      "baseline_sha256":hashlib.sha256(V2.read_bytes()).hexdigest()})
    if not passed: raise RuntimeError("Polydisc V3 proof gate failed")

def diagnostic(metric):
    sys.path.insert(0,str(BENCH)); from lkc_bench import cli
    from lkc_bench import diagnostic as engine
    orig=engine.official_baseline; engine.official_baseline=lambda problem:V2
    try:
        out=EVIDENCE/f"{metric}-v2-v3"
        code=cli.main(["diagnostic","--problem","polydisc","--submission",str(SOURCE),
          "--metric",metric,"--repetitions","3","--timeout","900","--memory-mb","4096",
          "--inputs",*map(str,INPUTS),"--output",str(out)])
    finally: engine.official_baseline=orig
    data=json.loads((out/"diagnostic.json").read_text())
    if code!=0 or not data.get("complete"): raise RuntimeError(f"incomplete {metric}")
    b=data["totals"]["baseline"];c=data["totals"]["candidate"]
    return {"metric":metric,"baseline":b,"candidate":c,"ratio":c/b,"reduction_pct":100*(1-c/b),
      "comparisons":data.get("comparisons"),"candidate_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      "baseline_sha256":hashlib.sha256(V2.read_bytes()).hexdigest()}

def screen():save("wall-screen.json",diagnostic("wall-time"))

def qualify():
    code,text=execute(["python3","evaluation/run.py","--problem","polydisc","--submission",str(SOURCE),"--timeout","180"],
                      "canonical.log",cwd=UPSTREAM,timeout=5400)
    ok=code==0 and ": accepted" in text; save("canonical.json",{"accepted":ok})
    if not ok: raise RuntimeError("Polydisc V3 canonical failed")

def instructions():
    r=diagnostic("callgrind");r.update(official_pmu_measured=False,local_promotion_eligible=r["ratio"]<1.0,
       selected_champion="v3" if r["ratio"]<1.0 else "v2");save("instruction-verdict.json",r)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("phase",choices=["prove","screen","qualify","instructions"]);globals()[p.parse_args().phase]()
