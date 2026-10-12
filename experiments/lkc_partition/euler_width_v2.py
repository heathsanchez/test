#!/usr/bin/env python3
"""SAIR Partition Euler quotient V2: base-width/consequence tournament.

Only SCREEN CANDIDATES. No universal Lean proof or SAIR submission.
The same exact partition formula and sparse pentagonal denominator are retained.
Only width selection and arithmetic lowering vary. The baseline is the
unchanged, previously measured sparse Euler V1.
"""
from __future__ import annotations

import json
import hashlib
import runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(exist_ok=True,parents=True)
legacy=runpy.run_path(str(ROOT/"euler_sparse_quotient_v1.py"))
LEAN=legacy["LEAN"]
assert LEAN.count("let w := n + 3")==1
assert LEAN.count("let g1 := j * (3 * j - 1) / 2")==1
assert LEAN.count("let g2 := j * (3 * j + 1) / 2")==1
assert LEAN.count("if j % 2 = 0")==1

ARMS={
    "half":("Nat.shiftRight n 1 + 6",False),
    "quarter":("Nat.shiftRight n 2 + 13",False),
    "minimum":("min (Nat.shiftRight n 1 + 6) (Nat.shiftRight n 2 + 13)",False),
    "fused":("min (Nat.shiftRight n 1 + 6) (Nat.shiftRight n 2 + 13)",True),
}

def candidate_source(name:str)->str:
    width,fuse=ARMS[name]
    t=LEAN.replace("let w := n + 3",f"let w := {width}")
    if fuse:
        t=t.replace("let g1 := j * (3 * j - 1) / 2",
                    "let g1 := Nat.shiftRight (j * (3 * j - 1)) 1")
        t=t.replace("let g2 := j * (3 * j + 1) / 2",
                    "let g2 := Nat.shiftRight (j * (3 * j + 1)) 1")
        t=t.replace("if j % 2 = 0 then",
                    "if (j &&& 1) = 0 then")
    return t

def ref_partition(n:int)->int:
    data=[0]*(n+1);data[0]=1
    for k in range(1,n+1):
        for j in range(k,n+1):
            data[j]+=data[j-k]
    return data[n]

def eval_quotient(n:int,w:int)->int:
    B=1<<w
    pos=neg=0
    j=1
    while j*(3*j-1)//2<=n:
        g1=j*(3*j-1)//2
        g2=j*(3*j+1)//2
        term=B**(n-g1)
        if g2<=n:term+=B**(n-g2)
        if j%2==0:pos+=term
        else:neg+=term
        j+=1
    D=B**n+pos-neg
    assert D>0
    return (B**(2*n)//D)%B

def width_value(arm:str,n:int)->int:
    return {
       "half":n//2+6,
       "quarter":n//4+13,
       "minimum":min(n//2+6,n//4+13),
       "fused":min(n//2+6,n//4+13),
    }[arm]

def main()->None:
    details={x:{"mismatches":[],"widths":{}} for x in ARMS}
    for n in range(0,241):
        expected=ref_partition(n)
        for name in ARMS:
            w=width_value(name,n)
            value=eval_quotient(n,w)
            if value!=expected:details[name]["mismatches"].append({"n":n,"expected":expected,"actual":value})
            if n in (0,1,2,4,8,14,22,32,36,70,100,240):
                details[name]["widths"][str(n)]=w
    assert all(not rec["mismatches"] for rec in details.values()),details
    assert eval_quotient(1,1)!=ref_partition(1),"Negative too-narrow base did not fail"
    for name in ARMS:
        src=candidate_source(name)
        target=OUT/f"Submission_euler_width_{name}_probe.lean"
        target.write_text(src)
        details[name]["source_sha256"]=hashlib.sha256(src.encode()).hexdigest()
        details[name]["source_bytes"]=len(src.encode())
    report={"schema":"lkc-euler-width-screen-v2","state":"FINITE_VERIFIED_ONLY",
            "independent_DP_cases":"0..240",
            "formal_Lean_equivalence":False,
            "public_submission":False,
            "negative_control":{"n":1,"width":1,"state":"FAILED_EXPECTED"},
            "arms":details}
    (OUT/"euler_width_v2_finite.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
