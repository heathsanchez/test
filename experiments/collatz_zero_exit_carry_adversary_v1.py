#!/usr/bin/env python3
"""Exact adversarial audit of fixed-origin live-mass progress.

This widens the previous 20-bit live-origin block test to all odd sources below
2^24 and extracts the longest zero-EXIT carry stretch.  It is deliberately a
falsifier/normalizer, not a Collatz proof.

Definitions:
  qmin[j] = min q with 3^q >= 2^j
  C_j(2^m) = sources <2^m whose first coefficient crossing is exactly j
  P_j(2^m) = sources <2^m with no coefficient crossing through j

Hence P_j is nonincreasing and
  P_j - P_(j+b) = sum_{t=j+1}^{j+b} C_t.

For a fixed actual source after each shortcut step let
  h_j = q_j - qmin[j].
With e_(j+1)=parity(y_j) and delta_(j+1)=qmin[j+1]-qmin[j],
  h_(j+1)=h_j + e_(j+1) - delta_(j+1).
A first coefficient crossing is exactly the fatal boundary transition
  h_j=0, delta_(j+1)=1, e_(j+1)=0.
"""
from __future__ import annotations
import json

BITS = 24
DEPTH = 512
START = 60

def qmin_table(depth: int) -> list[int]:
    out=[0]*(depth+1)
    q,p3=0,1
    for j in range(1,depth+1):
        while p3 < (1<<j):
            p3*=3
            q+=1
        out[j]=q
    return out

QMIN=qmin_table(DEPTH)

def first_crossing(n: int):
    y,q=n,0
    for j in range(1,DEPTH+1):
        if y&1:
            y=(3*y+1)//2
            q+=1
        else:
            y//=2
        if q < QMIN[j]:
            return j,y,q
    return None

hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
late=[]
unresolved=[]
max_cross=0
max_source=None
for n in range(1,1<<BITS,2):
    z=first_crossing(n)
    if z is None:
        unresolved.append(n)
        continue
    j,y,q=z
    hist[j][n.bit_length()]+=1
    if j>=200:
        late.append((n,j))
    if j>max_cross:
        max_cross,max_source=j,n

C=[[0]*(BITS+1) for _ in range(DEPTH+1)]
P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for j in range(1,DEPTH+1):
    for m in range(1,BITS+1):
        C[j][m]=C[j][m-1]+hist[j][m]
for m in range(1,BITS+1):
    P[0][m]=1<<(m-1)
    for j in range(1,DEPTH+1):
        P[j][m]=P[j-1][m]-C[j][m]
        assert P[j][m] <= P[j-1][m]

worst=None
no_next=[]
for m in range(1,BITS+1):
    nxt=None
    next_after=[None]*(DEPTH+1)
    for j in range(DEPTH,-1,-1):
        next_after[j]=nxt
        if j>=1 and C[j][m]>0:
            nxt=j
    for j in range(START,DEPTH):
        if P[j][m]<=0:
            continue
        t=next_after[j]
        if t is None:
            no_next.append({"m":m,"j":j,"live":P[j][m]})
            continue
        b=t-j
        # exact conservation over the candidate block
        lost=P[j][m]-P[t][m]
        exits=sum(C[u][m] for u in range(j+1,t+1))
        assert lost==exits and exits>0
        row={"m":m,"j":j,"next_exit":t,"block":b,
             "live_before":P[j][m],"live_after":P[t][m],
             "lost":lost}
        if worst is None or (b,j,m)>(worst["block"],worst["j"],worst["m"]):
            worst=row

assert not unresolved, unresolved[:5]
assert worst is not None
# Exact adversarial witness against the previously tested B<=32 boundary.
assert worst["m"]==24, worst
assert worst["j"]==249, worst
assert worst["next_exit"]==287, worst
assert worst["block"]==38, worst
assert worst["live_before"]==1 and worst["live_after"]==0, worst
assert max_cross==287 and max_source==13421671, (max_cross,max_source)

survivors=[(n,j) for (n,j) in late if n < (1<<worst["m"]) and j>worst["j"]]
assert survivors==[(13421671,287)], survivors[:20]
witness=survivors[0][0]

# Exact carry trace for the unique record survivor.
trace=[]
boundary_returns=[]
y,q=witness,0
prev_h=0
for j in range(1,worst["next_exit"]+1):
    e=y&1
    if e:
        y=(3*y+1)//2
        q+=1
    else:
        y//=2
    h=q-QMIN[j]
    if j==1:
        # h recurrence starts from q_0=qmin_0=0
        assert h == e-(QMIN[1]-QMIN[0])
    else:
        assert h == prev_h + e - (QMIN[j]-QMIN[j-1])
    prev_h=h
    if j>=worst["j"]:
        rec={"j":j,"endpoint":y,"q":q,"qmin":QMIN[j],"h":h}
        if j<worst["next_exit"]:
            delta=QMIN[j+1]-QMIN[j]
            next_bit=y&1
            rec.update({"next_delta":delta,"next_bit":next_bit})
            if h==0:
                fatal=(delta==1 and next_bit==0)
                br={**rec,"fatal_next":fatal}
                boundary_returns.append(br)
        trace.append(rec)

assert trace[-1]["h"]==-1
assert boundary_returns[-1]["j"]==286
assert boundary_returns[-1]["next_delta"]==1
assert boundary_returns[-1]["next_bit"]==0
assert boundary_returns[-1]["fatal_next"] is True
# There is a genuine safe zero-height return before the fatal one.
assert any((r["j"]==273 and not r["fatal_next"]) for r in boundary_returns)

result={
  "schema":"COLLATZ_ZERO_EXIT_CARRY_ADVERSARY_V1",
  "authority_boundary":{
    "source_bits":BITS,
    "max_source_exclusive":1<<BITS,
    "depth":DEPTH,
    "start_depth":START,
    "arithmetic":"exact integers"
  },
  "population":{
    "odd_sources":1<<(BITS-1),
    "max_first_crossing_depth":max_cross,
    "record_source":max_source,
    "unresolved_through_depth":len(unresolved)
  },
  "resource":{
    "candidate":"P_j(2^m) in Nat",
    "conservation":"P_j-P_(j+b)=sum_{t=j+1}^{j+b} C_t",
    "strict_drop_equiv":"some C_t>0 in the future block"
  },
  "adversarial_witness":worst | {
    "unique_live_source_at_j":witness,
    "zero_exit_future_steps":worst["block"]-1
  },
  "candidate_status":{
    "B_le_32_uniform_block":"REJECTED_ON_DECLARED_FINITE_BOUNDARY",
    "B_le_37_uniform_block":"REJECTED_ON_DECLARED_FINITE_BOUNDARY",
    "P_as_Nat_resource":"CANDIDATE",
    "universal_eventual_strict_drop":"UNKNOWN",
    "global_collatz":"UNKNOWN"
  },
  "carry_normal_form":{
    "h":"q_j-qmin[j]",
    "delta":"qmin[j+1]-qmin[j] in {0,1}",
    "epsilon":"parity(endpoint_j)",
    "recurrence":"h_(j+1)=h_j+epsilon_(j+1)-delta_(j+1)",
    "first_crossing_shape":"h_j=0 and delta_(j+1)=1 and epsilon_(j+1)=0",
    "boundary_returns_in_record_zero_exit_stretch":boundary_returns
  },
  "record_trace":trace,
  "crystal_consequence":{
    "rejected":"infer a universal small block bound from the 20-bit B<=32 census",
    "retained":"P is an exact nonincreasing Nat-valued population resource",
    "irreducible_residual":"prove that a nonempty fixed-origin population cannot support an infinite actual-source-coherent carry execution with h_j>=0 forever",
    "noncircular_form":"exclude an infinite fixed-positive-source endpoint/odd-count carry path; do not assume eventual first crossing"
  }
}
print(json.dumps(result,indent=2))
