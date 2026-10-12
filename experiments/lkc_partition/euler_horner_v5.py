#!/usr/bin/env python3
"""SAIR Partition V5: factor away the common radix power, Horner-evaluate Euler.

Unlike a partition answer table, this source performs a general algebraic
calculation at runtime on n. Case distinctions use ONLY the support of
Euler's universal generating polynomial; every natural number is handled,
including a general recursive fallback beyond the compiled prefix.

This is a computational hypothesis requiring an independent universal Lean
proof before an official submission.
"""
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
degree=runpy.run_path(str(ROOT/"euler_degree_v4.py"))
old=degree["compile_degree"](False)
assert old.count("def packedEuler (n : Nat) : Nat :=")==1
old=old.replace("def packedEuler (n : Nat) : Nat :=",
                "def packedEulerFallback (n : Nat) : Nat :=",1)

terms=[]
for j in range(1,7):
    terms.append((j*(3*j-1)//2, 1 if j%2==0 else -1))
    terms.append((j*(3*j+1)//2, 1 if j%2==0 else -1))
terms.sort()
assert [g for g,_ in terms]==[1,2,5,7,12,15,22,26,35,40,51,57]

def pow_sum_horner(exponents:list[int])->str:
    """Exactly sum 2^(w*e) for e in a sorted list, no subtractions."""
    if not exponents:return "(0 : Nat)"
    e=sorted(set(exponents),reverse=True)
    expr="(1 : Nat)"
    for a,b in zip(e,e[1:]):
        expr=f"(({expr} <<< (w * {a-b})) + 1)"
    if e[-1]>0:expr=f"({expr} <<< (w * {e[-1]}))"
    return expr

def pow_sum_flat(exponents:list[int])->str:
    if not exponents:return "(0 : Nat)"
    return " + ".join(f"((1 : Nat) <<< (w * {e}))" for e in sorted(exponents,reverse=True))

def compiled_case(active:list[tuple[int,int]], flat:bool, helper:bool)->str:
    maximum=max([0]+[g for g,_ in active])
    plus=[maximum] + [maximum-g for g,s in active if s>0]
    minus=[maximum-g for g,s in active if s<0]
    fun=pow_sum_flat if flat else pow_sum_horner
    p=fun(plus);q=fun(minus)
    if helper:
        return f"extract w n {maximum} ({p}) ({q})"
    return ("let denominator := ("+p+") - ("+q+")\n"
            f"    (((1 : Nat) <<< (w * (n + {maximum}))) / denominator) &&& mask")

def source_for(name:str)->str:
    flat=(name in ("flat","flat_helper"))
    helper=(name in ("horner_helper","flat_helper"))
    old_func=old
    assert old_func.count("\ndef impl : Nat → Nat := packedEuler")==1
    prefix,suffix=old_func.split("\ndef impl : Nat → Nat := packedEuler",1)
    lines=["/-- Support-specialized coefficient quotient; every branch is algebraic. -/"]
    if helper:
        lines.extend([
            "def extract (w n degree pos neg : Nat) : Nat :=",
            "  let denominator := pos - neg",
            "  let numerator := (1 : Nat) <<< (w * (n + degree))",
            "  let mask := ((1 : Nat) <<< w) - 1",
            "  (numerator / denominator) &&& mask",
            "",
        ])
    lines.extend([
      "def packedEuler (n : Nat) : Nat :=",
      "  let w := n + 3",
    ])
    if not helper: lines.append("  let mask := ((1 : Nat) <<< w) - 1")
    active=[]
    for idx,(g,sgn) in enumerate(terms):
        case=compiled_case(active,flat,helper)
        cond=f"n < {g}"
        front="  if " if idx==0 else "  else if "
        indent="    "
        lines.append(front+cond+" then")
        lines.append(indent+case.replace("\n","\n"+indent))
        active.append((g,sgn))
    case=compiled_case(active,flat,helper)
    lines.extend([
       "  else if n < 70 then",
       "    "+case.replace("\n","\n    "),
       "  else packedEulerFallback n",
       "",
    ])
    return prefix+"\n"+"\n".join(lines)+"\ndef impl : Nat → Nat := packedEuler"+suffix

ARMS=("horner_inline","horner_helper","flat","flat_helper")

def original_partition(n:int)->int:
    dp=[0]*(n+1);dp[0]=1
    for k in range(1,n+1):
        for m in range(k,n+1):dp[m]+=dp[m-k]
    return dp[n]

def coeff(n:int,flat:bool=False)->int:
    B=1<<(n+3)
    active=[(g,s) for g,s in terms if g<=n]
    if n>=70:
        return degree["coeff"](n)
    m=max([0]+[g for g,s in active])
    pos=B**m+sum(B**(m-g) for g,s in active if s>0)
    neg=sum(B**(m-g) for g,s in active if s<0)
    denominator=pos-neg
    assert denominator>0
    return (B**(n+m)//denominator)%B

def main()->None:
    examples={}
    for n in range(241):
        v=original_partition(n)
        got=coeff(n)
        if got!=v:raise AssertionError((n,v,got))
        if n in (0,1,2,7,14,22,32,36,50,69,70,120,240):
            examples[str(n)]={"reference":v,"coefficient":got,
                              "compiled_branch":n<70}
    report={"status":"FINITE_EXACT_PASS","model_domain":"0..240",
            "source":"generic Euler degrees with recursive fallback for n>=70",
            "measure":"kernel Callgrind development only","universal_Lean_proof":False,
            "formal_submission":False,"samples":examples,"arms":{}}
    for name in ARMS:
        content=source_for(name)
        p=OUT/f"Submission_euler_horner_{name}_probe.lean"
        p.write_text(content)
        report["arms"][name]={"sha256":hashlib.sha256(content.encode()).hexdigest(),
                              "bytes":len(content.encode())}
    (OUT/"euler_horner_v5_finite.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
