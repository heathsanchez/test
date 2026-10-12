#!/usr/bin/env python3
"""Proof-directed partial evaluation of Euler pentagonal terms.

This is not an input-answer table. Each compiled source retains the complete
all-N algorithm, including a recursive tail for generalized-pentagonal terms
beyond the fixed unrolling boundary. Source-level correctness remains
CANDIDATE pending a universal Lean proof; independent DP and paired kernel
checks are mandatory.
"""
from __future__ import annotations
import hashlib, json, runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)
raw=runpy.run_path(str(ROOT/"euler_sparse_quotient_v1.py"))["LEAN"]

ANCHOR="  let (pos, neg) := pentagonalParts n w (n + 1) 0 0 0"
assert raw.count(ANCHOR)==1
ARMS=(4,6,8)

def generalized(j:int)->tuple[int,int]:
    return j*(3*j-1)//2, j*(3*j+1)//2

def compile_source(k:int)->str:
    pos=[];neg=[]
    for j in range(1,k+1):
        a,b=generalized(j)
        t1=f"(if n < {a} then 0 else (1 : Nat) <<< (w * (n - {a})))"
        t2=f"(if n < {b} then 0 else (1 : Nat) <<< (w * (n - {b})))"
        if j%2==0:pos.extend([t1,t2])
        else:neg.extend([t1,t2])
    nxt=generalized(k+1)[0]
    code=[
      f"  /- First {k} universal Euler-pentagonal pairs, partially evaluated at source generation. -/",
      "  let posHead := "+(" +\n      ".join(pos) if pos else "(0 : Nat)"),
      "  let negHead := "+(" +\n      ".join(neg) if neg else "(0 : Nat)"),
      f"  let (posTail, negTail) : Nat × Nat :=",
      f"    if n < {nxt} then (0,0)",
      f"    else pentagonalParts n w (n + 1) {k} 0 0",
      "  let pos := posHead + posTail",
      "  let neg := negHead + negTail"
    ]
    return raw.replace(ANCHOR,"\n".join(code))

def model_parts(n:int,w:int,prefix:int)->tuple[int,int]:
    B=1<<w
    pos=neg=0
    for j in range(1,prefix+1):
        a,b=generalized(j)
        term=(B**(n-a) if a<=n else 0)+(B**(n-b) if b<=n else 0)
        if j%2==0:pos+=term
        else:neg+=term
    if n>=generalized(prefix+1)[0]:
        for j in range(prefix+1,n+2):
            a,b=generalized(j)
            if n<a:break
            term=B**(n-a)+(B**(n-b) if b<=n else 0)
            if j%2==0:pos+=term
            else:neg+=term
    return pos,neg

def original_parts(n:int,w:int)->tuple[int,int]:
    B=1<<w
    pos=neg=0
    for j in range(1,n+2):
        a,b=generalized(j)
        if n<a:break
        term=B**(n-a)+(B**(n-b) if b<=n else 0)
        if j%2==0:pos+=term
        else:neg+=term
    return pos,neg

def ref_p(n:int)->int:
    dp=[0]*(n+1);dp[0]=1
    for k in range(1,n+1):
        for m in range(k,n+1):dp[m]+=dp[m-k]
    return dp[n]

def main()->None:
    reports={}
    for k in ARMS:
        mismatches=[];samples={}
        for n in range(241):
            w=n+3
            pos,neg=model_parts(n,w,k)
            opos,oneg=original_parts(n,w)
            if (pos,neg)!=(opos,oneg):
                mismatches.append({"n":n,"kind":"Euler pair mismatch"})
                continue
            B=1<<w
            numerator=B**(2*n)
            denom=B**n+pos-neg
            assert denom>0
            got=numerator//denom%B
            if got!=ref_p(n):mismatches.append({"n":n,"got":got,"expected":ref_p(n)})
            if n in (0,1,14,22,32,36,51,70,100,240):
                samples[str(n)]={"result":got,"prefix_pairs":k,
                                 "recursive_tail_active":n>=generalized(k+1)[0]}
        assert not mismatches,mismatches[:15]
        source=compile_source(k)
        out=OUT/f"Submission_euler_spine_{k}_probe.lean"
        out.write_text(source)
        reports[str(k)]={"source_sha256":hashlib.sha256(source.encode()).hexdigest(),
                         "bytes":len(source.encode()),
                         "first_tail_pentagonal":generalized(k+1)[0],
                         "samples":samples,"independent_checks":241}
    result={"status":"FINITE_EXACT_PASS","scope":"0..240 with independent row DP",
            "source_semantics":"unrolled prefix plus universal recursive tail",
            "arms":reports,"universal_Lean_proof":False,
            "official_submission":False}
    (OUT/"euler_spine_v3_finite.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
