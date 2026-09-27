#!/usr/bin/env python3
"""Crystal residual campaign: source/carry realizability of repeated equality.

Consumes the exact residual left by TWO_EQUALITY_INTEGER_V1:
abstract count integrality admits repeated equality.  This campaign asks what
actual canonical source-prefix conservation permits.  It repeatedly promotes
only exact identities, rejects vacuous/aggregate explanations, and emits the
smallest surviving residual.

This is bounded theorem discovery.  It does not prove Collatz.
"""
from __future__ import annotations
import json
from collections import defaultdict, Counter
from fractions import Fraction
from collatz_live_origin_bridge_v1 import language_counts, first_crossing

BITS=20; DEPTH=512; BMAX=64
qmin,F,H=language_counts(DEPTH)

# Exact source-coupled first-crossing conservation P[j-1,m]=P[j,m]+C[j,m].
hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for n in range(1,1<<BITS,2):
    z=first_crossing(n,qmin)
    if z:
        j,_,_=z; hist[j][n.bit_length()]+=1
C=[[0]*(BITS+1) for _ in range(DEPTH+1)]
P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for j in range(1,DEPTH+1):
    for m in range(1,BITS+1): C[j][m]=C[j][m-1]+hist[j][m]
for m in range(1,BITS+1):
    P[0][m]=1<<(m-1)
    for j in range(1,DEPTH+1):
        P[j][m]=P[j-1][m]-C[j][m]
        assert P[j-1][m]==P[j][m]+C[j][m]

def D(j,m): return (P[j][m]<<j)//F[j] if P[j][m] else None
def rr(j,b,m):
    if not P[j][m]: return Fraction(0)
    a=Fraction(P[j+b][m]*F[j],P[j][m]*F[j+b])
    e=(6*(j+b))//125-(6*j)//125-b
    return a/Fraction(2**e if e>=0 else 1,1 if e>=0 else 2**(-e))

# Reproduce warranted common-Q policy.
G=defaultdict(list)
for j in range(60,DEPTH-BMAX+1):
    for m in range(1,BITS+1):
        d=D(j,m)
        if d is not None: G[(j&1,d)].append((j,m))
policy={}
for q,xs in G.items():
    for b in range(1,BMAX+1):
        if all(j+b<=DEPTH and rr(j,b,m)<=1 for j,m in xs):
            policy[q]=b; break
assert len(policy)==len(G)

cycles=[]
# Cycle 1: actual realized repeated equality, not abstract count feasibility.
eq=[]; double=[]
for q,xs in G.items():
    b=policy[q]
    for j,m in xs:
        if rr(j,b,m)!=1: continue
        j2=j+b
        if j2>DEPTH-BMAX or not P[j2][m]: continue
        q2=(j2&1,D(j2,m))
        if q2 not in policy: continue
        b2=policy[q2]; r2=rr(j2,b2,m)
        row={"j":j,"m":m,"b1":b,"j2":j2,"b2":b2,
             "phase":[j%125,j2%125],
             "P":[P[j][m],P[j2][m],P[j2+b2][m]],
             "C":[P[j][m]-P[j2][m],P[j2][m]-P[j2+b2][m]],
             "D":[D(j,m),D(j2,m)]}
        eq.append(row)
        if r2==1: double.append(row)
cycles.append({"cycle":1,"capability":"ACTUAL_SOURCE_CARRY_REALIZATION",
 "equality_states":len(eq),"double_equalities":len(double),
 "first_double":double[:20],
 "promotion":"REJECT_ONE_EQUALITY_CREDIT" if double else "BOUNDED_NO_DOUBLE_EQUALITY"})

# Cycle 2: if bounded no-double equality survives, mine the smallest exact
# separator already forced by conservation.  Equality over [j,j+b] means an
# exact rational relation between P endpoints; record crossing mass Cblock.
patterns=Counter()
for r in eq:
    p0,p1,p2=r["P"]; c1,c2=r["C"]
    patterns[(c1==0,c2==0,r["phase"][0],r["b1"],r["b2"])]+=1
cycles.append({"cycle":2,"capability":"MINIMUM_CARRY_SEPARATOR",
 "distinct_patterns":len(patterns),
 "top_patterns":[{"pattern":list(k),"count":v} for k,v in patterns.most_common(20)]})

# Cycle 3: test a source-coupled theorem stronger than count integrality:
# normalized equality fixes P1/P0 exactly.  Conservation then fixes C1/P0.
# Ask whether a second equality would require C2/P1 equal to its exact required
# value; actual P supplies the falsification oracle.  Preserve the algebraic
# obligation for universal proof.
obligations=Counter()
for r in eq:
    j,b1,b2=r["j"],r["b1"],r["b2"]
    e1=(6*(j+b1))//125-(6*j)//125-b1
    e2=(6*(j+b1+b2))//125-(6*(j+b1))//125-b2
    # Equality requires Pnext/P = (Fnext/F)*2^e.
    target2=Fraction(F[j+b1+b2],F[j+b1]) * Fraction(2**e2 if e2>=0 else 1,1 if e2>=0 else 2**(-e2))
    # Conservation-required crossing fraction under hypothetical equality.
    required_carry=1-target2
    obligations[(j%125,b1,b2,required_carry.numerator,required_carry.denominator)]+=1
cycles.append({"cycle":3,"capability":"SECOND_EQUALITY_CARRY_OBLIGATION",
 "obligation_classes":len(obligations),
 "sample":[{"key":list(k),"realized_first_equalities":v} for k,v in list(obligations.items())[:20]],
 "interpretation":"a universal proof must show the next exact source-crossing mass cannot equal this required fraction on a live first-equality cylinder"})

if double:
    residual={"name":"REALIZED_DOUBLE_EQUALITY","examples":double[:20],
      "next":"split on the minimum exact source/carry observable distinguishing these realized paths"}
    status="CANDIDATE_REJECTED"
elif eq:
    residual={"name":"UNIVERSAL_SECOND_EQUALITY_CARRY_EXCLUSION",
      "statement":"on every actual live source cylinder satisfying first normalized equality, exact canonical lift/conservation forbids the next policy block from satisfying its required crossing fraction",
      "bounded_equality_states":len(eq),
      "next":"derive this carry exclusion from canonical (q,R,Y) lift arithmetic; do not increase depth as a substitute"}
    status="BOUNDED_SOURCE_CARRY_EXCLUSION"
else:
    residual={"name":"VACUOUS_POLICY_OR_NO_EQUALITY","next":"repair experiment; no theorem promotion"}
    status="REJECT_VACUOUS"

print(json.dumps({"schema":"COLLATZ_CRYSTAL_SOURCE_CARRY_REALIZABILITY_V1",
 "cycles":cycles,"status":status,"residual":residual,"global_collatz":"UNKNOWN"},indent=2,default=str))
