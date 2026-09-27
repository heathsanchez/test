#!/usr/bin/env python3
"""24-bit Crystal stress test for the exact one-equality-credit carry law.

Consumes the exact first-crossing histogram over all positive odd sources <2^24,
reconstructs P_j(2^m) by conservation, reproduces the common-Q adaptive policy,
and tests whether a realized normalized-equality macro can be followed by a
second realized normalized-equality macro.

Bounded theorem discovery only. Global Collatz remains UNKNOWN.
"""
from __future__ import annotations
import json,sys
from collections import defaultdict,Counter
from fractions import Fraction
from pathlib import Path

DEPTH=512
BITS=24
BMAX=64

def language_counts(depth:int):
    qmin=[0]*(depth+1)
    q=0;p3=1
    for j in range(1,depth+1):
        while p3 < (1<<j):
            p3*=3;q+=1
        qmin[j]=q
    counts={0:1}; live=[1]; terminal=[0]
    for j in range(1,depth+1):
        nxt=defaultdict(int); leaves=0
        for q,c in counts.items():
            for bit in (0,1):
                if q+bit < qmin[j]: leaves += c
                else: nxt[q+bit] += c
        counts=dict(nxt)
        live.append(sum(counts.values()))
        terminal.append(leaves)
        assert live[j]+terminal[j]==2*live[j-1]
    return qmin,live,terminal

def main(path:str)->int:
    obj=json.loads(Path(path).read_text())
    assert obj["schema"]=="COLLATZ_24BIT_LIVE_ORIGIN_HISTOGRAM_V1"
    assert obj["source_bits"]==BITS and obj["depth"]==DEPTH
    assert obj["unresolved"]==0 and obj["overflow"]==0
    assert obj["odd_sources"]==(1<<(BITS-1))

    qmin,F,H=language_counts(DEPTH)
    hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
    for r in obj["rows"]:
        hist[r["j"]][r["m"]]=r["count"]

    C=[[0]*(BITS+1) for _ in range(DEPTH+1)]
    P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
    for j in range(1,DEPTH+1):
        for m in range(1,BITS+1):
            C[j][m]=C[j][m-1]+hist[j][m]
    for m in range(1,BITS+1):
        P[0][m]=1<<(m-1)
        for j in range(1,DEPTH+1):
            P[j][m]=P[j-1][m]-C[j][m]
            assert P[j-1][m]==P[j][m]+C[j][m]
    assert P[DEPTH][BITS]==0

    def debt_class(j,m):
        if not P[j][m]: return None
        return (P[j][m]<<j)//F[j]

    def normalized_ratio(j,b,m):
        if not P[j][m]: return Fraction(0)
        a=Fraction(P[j+b][m]*F[j],P[j][m]*F[j+b])
        e=(6*(j+b))//125-(6*j)//125-b
        scale=Fraction(2**e,1) if e>=0 else Fraction(1,2**(-e))
        return a/scale

    G=defaultdict(list)
    for j in range(60,DEPTH-BMAX+1):
        for m in range(1,BITS+1):
            d=debt_class(j,m)
            if d is not None:
                G[(j&1,d)].append((j,m))

    policy={}
    missing=[]
    for q,xs in G.items():
        found=None
        for b in range(1,BMAX+1):
            if all(j+b<=DEPTH and normalized_ratio(j,b,m)<=1 for j,m in xs):
                found=b;break
        if found is None: missing.append({"Q":list(q),"members":xs[:20]})
        else: policy[q]=found

    equality=[]
    double=[]
    positive_exit_on_equality=[]
    next_without_loss=[]
    singleton_eq=[]
    waits=Counter()

    if not missing:
        for q,xs in G.items():
            b=policy[q]
            for j,m in xs:
                if normalized_ratio(j,b,m)!=1:
                    continue
                j2=j+b
                c1=P[j][m]-P[j2][m]
                row1={"j":j,"m":m,"P":P[j][m],"b1":b,"j2":j2,"C1":c1,
                      "phase1":j%125,"Q":[q[0],q[1]]}
                equality.append(row1)
                if P[j][m]==1: singleton_eq.append(row1)
                if c1!=0: positive_exit_on_equality.append(row1)
                if j2>DEPTH-BMAX or not P[j2][m]:
                    continue
                q2=(j2&1,debt_class(j2,m))
                if q2 not in policy:
                    continue
                b2=policy[q2]
                r2=normalized_ratio(j2,b2,m)
                c2=P[j2][m]-P[j2+b2][m]
                waits[b2]+=1
                row={**row1,"b2":b2,"j3":j2+b2,"P2":P[j2][m],
                     "P3":P[j2+b2][m],"C2":c2,"r2":[r2.numerator,r2.denominator],
                     "phase2":j2%125,"Q2":[q2[0],q2[1]]}
                if r2==1: double.append(row)
                if c2<=0: next_without_loss.append(row)

    result={
      "schema":"COLLATZ_CRYSTAL_SINGLETON_EQUALITY_CARRY_24BIT_V1",
      "source_bits":BITS,
      "depth":DEPTH,
      "max_first_crossing":obj["max_first_crossing"],
      "policy_classes":len(G),
      "policy_missing_within_BMAX":len(missing),
      "first_policy_missing":missing[:10],
      "equality_states":len(equality),
      "singleton_equality_states":len(singleton_eq),
      "first_singleton_equalities":singleton_eq[:20],
      "equality_with_positive_exit":len(positive_exit_on_equality),
      "realized_double_equalities":len(double),
      "first_double_equalities":double[:20],
      "successor_macros_without_positive_live_loss":len(next_without_loss),
      "first_successor_without_loss":next_without_loss[:20],
      "successor_block_histogram":dict(sorted(waits.items())),
      "candidate_rank":"lexicographic (P,E), E one equality credit",
      "status":(
          "POLICY_BOUNDARY_INSUFFICIENT" if missing else
          "24BIT_EQUALITY_CREDIT_FALSIFIED" if double else
          "24BIT_NO_DOUBLE_EQUALITY_SURVIVES"
      ),
      "next":(
          "extract first falsifying carry separator" if double else
          "derive no-double-equality from exact canonical source/carry conservation; do not infer universality from this bounded result"
      ),
      "global_collatz":"UNKNOWN"
    }
    print(json.dumps(result,indent=2))
    return 1 if missing or double else 0

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: collatz_crystal_singleton_equality_carry_24bit_v1.py histogram.json")
    raise SystemExit(main(sys.argv[1]))
