#!/usr/bin/env python3
"""Crystal V33: zero-slack K boundary and sharp K-cycle owner contraction.

Parent: V32 exact K-density tradeoff.

Two questions:
1) What recurrent behavior can attain equality in
     19*q - 12*k + 19*D >= 0 ?
2) What does the V32 sharp c=18 counterexample do to the canonical owner?

Result:
* every zero-reduced recurrent component is a 19-edge / 12-odd pure-I cycle;
  no K transition lies on a recurrent equality cycle;
* the sharp 49-edge K cycle (k=49,q=29,D=2) has exact canonical-owner map
      F(m) = (3^29/2^49)m + beta
  with a positive rational fixed point about 6.44e6, far below the sole V23
  source floor 3.8911e19.  Therefore this specific density-lowering K cycle
  cannot repeat indefinitely on a V23 bad owner.

This does not exclude arbitrary aperiodic mixtures of distinct K cycles.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import io, json, hashlib, sys

with redirect_stdout(io.StringIO()):
    import collatz_crystal_k_density_tradeoff_v32 as v32

best=v32.best
edges=v32.edges
dist=v32.dist
MOD=v32.MOD
N0=38_911_100_780_481_085_467

zero=[]
adj=defaultdict(list)
for u,v,bit,cls,drop in edges:
    w=19*bit-12+19*drop
    rc=w+dist[u]-dist[v]
    assert rc>=0
    if rc==0:
        row=(u,v,bit,cls,drop)
        zero.append(row)
        adj[u].append(row)

sys.setrecursionlimit(200000)
index={}; low={}; stack=[]; on=set(); comps=[]
def strong(v):
    index[v]=low[v]=len(index)
    stack.append(v); on.add(v)
    for _u,w,_bit,_cls,_drop in adj.get(v,()):
        if w not in index:
            strong(w); low[v]=min(low[v],low[w])
        elif w in on:
            low[v]=min(low[v],index[w])
    if low[v]==index[v]:
        cc=[]
        while True:
            w=stack.pop(); on.remove(w); cc.append(w)
            if w==v: break
        comps.append(cc)

for v in best:
    if v not in index:
        strong(v)

recurrent=[]
for cc in comps:
    s=set(cc)
    ee=[e for e in zero if e[0] in s and e[1] in s]
    cyc=len(cc)>1 or any(e[0]==e[1] for e in ee)
    if cyc:
        recurrent.append((cc,ee))

assert len(recurrent)==66
rows=[]
for cc,ee in recurrent:
    assert len(cc)==19
    assert len(ee)==19
    q=sum(e[2] for e in ee)
    D=sum(e[4] for e in ee)
    kinds=Counter(e[3] for e in ee)
    assert q==12 and D==0 and kinds==Counter({"I":19})
    rows.append({
        "states":sorted(cc),
        "length":19,
        "odd_steps":12,
        "K_drop":0,
        "classes":{"I":19},
    })

# Recheck V32 sharp c=18 witness and compose its exact canonical-owner map.
cycle=[
169775,254663,381995,41552,328049,492074,246037,369056,184528,
92264,46132,23066,300320,184760,92380,46190,335006,236789,384115,
44732,332819,499229,217403,374422,187211,359326,179663,269495,
404243,74924,378107,35720,17860,8930,279116,139558,475058,237529,
356294,178147,267221,399331,67556,33778,316388,158194,503012,
488798,467477,169775
]
lookup=defaultdict(list)
for e in edges:
    lookup[(e[0],e[1])].append(e)

def edge_map(u,v,bit):
    S,C,_=best[u]
    Sp,Cp,_=best[v]
    if bit==0:
        a=Fraction(2**Sp,2**(S+1))
        b=a*Fraction(C,MOD)-Fraction(Cp,MOD)
    else:
        a=Fraction(3*2**Sp,2**(S+1))
        b=Fraction(2**(Sp-1),1)+a*Fraction(C,MOD)-Fraction(Cp,MOD)
    return a,b

A=Fraction(1); B=Fraction(0)
qsum=Dsum=w18=0
cycle_edges=[]
for u,v in zip(cycle[:-1],cycle[1:]):
    opts=lookup[(u,v)]
    assert opts
    e=min(opts,key=lambda z:19*z[2]-12+18*z[4])
    _u,_v,bit,cls,drop=e
    ww=19*bit-12+18*drop
    a,b=edge_map(u,v,bit)
    B=a*B+b
    A=a*A
    qsum+=bit; Dsum+=drop; w18+=ww
    cycle_edges.append({"u":u,"v":v,"bit":bit,"class":cls,"drop":drop})

assert len(cycle_edges)==49 and qsum==29 and Dsum==2 and w18==-1
assert A==Fraction(3**29,2**49)
assert A<1
fixed=B/(1-A)
assert fixed==Fraction(1692239059429478714212288501,262701689819004684189)
assert fixed.denominator!=1
assert fixed < N0
# For every m >= N0, F(m)<m.
assert A*N0+B < N0

result={
  "schema":"COLLATZ_CRYSTAL_K_BOUNDARY_V33",
  "parent":"collatz-crystal-k-density-tradeoff-v32@c3d0cee0c5793fd1cb15e46b5e2429f47da35b17",
  "zero_slack_boundary":{
    "zero_reduced_edges":len(zero),
    "recurrent_components":len(recurrent),
    "component_shape":"66 disjoint recurrent cycles, each length 19 / q=12 / D=0",
    "K_on_recurrent_zero_slack_cycle":False,
    "first_components":rows[:8],
  },
  "sharp_K_cycle":{
    "length":49,
    "odd_steps":29,
    "K_drop":2,
    "weight_c18":-1,
    "owner_slope_num":A.numerator,
    "owner_slope_den":A.denominator,
    "owner_intercept_num":B.numerator,
    "owner_intercept_den":B.denominator,
    "fixed_point_num":fixed.numerator,
    "fixed_point_den":fixed.denominator,
    "fixed_point_lt_v23_source_floor":True,
    "repetition_consequence":"for every canonical owner m>=V23 source floor, one traversal strictly lowers m; infinite exact repetition cannot remain above the V23 source floor",
  },
  "scientific_verdict":"K_IS_STRICTLY_OFF_THE_ZERO_SLACK_BOUNDARY; SHARP_DENSITY_LOWERING_K_CYCLE_CONTRACTS_OWNER_BELOW_V23_SCALE",
  "next_residual":{
    "name":"APERIODIC_K_MIXTURE_SOURCE_CARRY",
    "statement":"Exclude aperiodic mixtures of distinct positive-slack K cycles that keep every canonical owner >= the original source while the parity liminf equals the rational-2-adic critical density.",
    "smallest_next_experiment":"compute the recurrent SCCs of the positive-slack K return graph after quotienting each return by its exact affine owner map; seek a common source-floor Lyapunov potential or emit the first incompatible cycle pair"
  },
  "universal_status":"UNKNOWN",
  "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
