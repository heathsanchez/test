#!/usr/bin/env python3
"""Degree-aware Euler polynomial compiler: decision tree over mathematical support.

No precomputed partition answers. Every branch uses the same Euler generating
polynomial terms 1,2,5,7,12,15,..., evaluated in base 2^(n+3); the universal
recursive tail is retained for n beyond the compiled algebraic prefix.

The finite model check is NOT a universal Lean proof. This is a controlled
kernel instruction screen intended to test AST-reduction cost.
"""
from __future__ import annotations
import hashlib,json,runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)
source=runpy.run_path(str(ROOT/"euler_sparse_quotient_v1.py"))["LEAN"]
spine=runpy.run_path(str(ROOT/"euler_spine_v3.py"))
start=source.index("def packedEuler (n : Nat) : Nat :=")
finish=source.index("\ndef impl : Nat → Nat := packedEuler",start)
MAX_PAIRS=6

terms=[]
for j in range(1,MAX_PAIRS+1):
    values=(j*(3*j-1)//2,j*(3*j+1)//2)
    for g in values:terms.append((g,1 if j%2==0 else -1))
terms.sort()
assert [g for g,_ in terms]==[1,2,5,7,12,15,22,26,35,40,51,57]

def denom_expr(active:list[tuple[int,int]],tail:bool=False)->str:
    pos=[f"((1 : Nat) <<< (w * (n - {g})))" for g,sign in active if sign==1]
    neg=[f"((1 : Nat) <<< (w * (n - {g})))" for g,sign in active if sign==-1]
    pos_expr=" + ".join(pos) if pos else "0"
    neg_expr=" + ".join(neg) if neg else "0"
    if tail:
        return ("let (posTail, negTail) := pentagonalParts n w (n + 1) 6 0 0\n"
                "      (baseTerm + ("+pos_expr+") + posTail) - (("+neg_expr+") + negTail)")
    return f"(baseTerm + ({pos_expr})) - ({neg_expr})"

def compile_degree(bool_branch:bool)->str:
    lines=["def packedEuler (n : Nat) : Nat :=",
           "  let w := n + 3",
           "  let baseTerm := (1 : Nat) <<< (w * n)",
           "  /- Fixed Euler-pentagonal degrees; all inputs share this source and",
           "     the generic recursive tail remains for arbitrary n. -/",
           "  let denom : Nat :="]
    active=[]
    for idx,(g,sign) in enumerate(terms):
        cond=f"n < {g}"
        if bool_branch:cond="decide ("+cond+")"
        leader="bif" if bool_branch else "if"
        branch=("    " if idx==0 else "    else ")+leader+" "+cond+" then "+denom_expr(active)
        lines.append(branch)
        active.append((g,sign))
    # For n<next term (g=70), all 12 compiled terms are complete.
    leader="bif" if bool_branch else "if"
    last="decide (n < 70)" if bool_branch else "n < 70"
    lines.append("    else "+leader+" "+last+" then "+denom_expr(active))
    lines.append("    else")
    lines.append("      "+denom_expr(active,tail=True).replace("\n","\n      "))
    lines.extend([
       "  let num := (1 : Nat) <<< (w * (2 * n))",
       "  let mask := ((1 : Nat) <<< w) - 1",
       "  (num / denom) &&& mask",
       ""
    ])
    candidate=source[:start]+"\n".join(lines)+source[finish:]
    return candidate

ARMS={
 "unroll3":spine["compile_source"](3),
 "unroll5":spine["compile_source"](5),
 "degree":compile_degree(False),
 "degree_bool":compile_degree(True),
}

def ref(n:int)->int:
    a=[0]*(n+1);a[0]=1
    for k in range(1,n+1):
        for j in range(k,n+1):
            a[j]+=a[j-k]
    return a[n]

def coeff(n:int)->int:
    w=n+3;B=1<<w;pos=neg=0
    for g,sign in terms:
        if g<=n:
            t=B**(n-g)
            if sign>0:pos+=t
            else:neg+=t
    for j in range(7,n+2):
        g1=j*(3*j-1)//2
        if g1>n:break
        g2=j*(3*j+1)//2
        t=B**(n-g1)+(B**(n-g2) if g2<=n else 0)
        if j%2==0:pos+=t
        else:neg+=t
    return (B**(2*n)//(B**n+pos-neg))%B

def main()->None:
    for n in range(241):
        assert coeff(n)==ref(n),(n,coeff(n),ref(n))
    results={}
    for name,t in ARMS.items():
        out=OUT/f"Submission_euler_degree_{name}_probe.lean"
        out.write_text(t)
        results[name]={"source_sha256":hashlib.sha256(t.encode()).hexdigest(),
                       "bytes":len(t.encode())}
    record={"schema":"lkc-euler-degree-compiler-v4",
            "finite_exact_dp_cases":"n=0..240","controls":"degree/support rather than answer lookup",
            "universal_fallback_after_g7":True,"proof_of_Lean_impl_correct":False,
            "official_submission":False,"arms":results}
    (OUT/"euler_degree_v4_finite.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record,indent=2))

if __name__=="__main__":
    main()
