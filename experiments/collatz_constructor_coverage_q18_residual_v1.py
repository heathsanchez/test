#!/usr/bin/env python3
"""Protected Q18 residual audit for constructor-coverage compiler V1.

Only the three exact record setters left without a recursive-Q17 lower-source
certificate before first coefficient crossing are tested.  Every accepted
reverse certificate is independently replayed.
"""
from __future__ import annotations
import json
from functools import lru_cache
from collatz_live_origin_bridge_v1 import language_counts
from collatz_reverse_predecessor_tree import enumerate_first_contractions, reverse_apply

Q=18
H=1024
NODE_CAP=300_000
SOURCES=[13421671,8088063,63728127]

def T(x:int)->int:
    return (3*x+1)//2 if x&1 else x//2

qmin,_,_=language_counts(H)
certs=enumerate_first_contractions(Q)
by={}
mods=set()
for c in certs:
    mods.add(c.d)
    by.setdefault((c.d,c.residue),[]).append(c)
mods=tuple(sorted(mods))

@lru_cache(maxsize=None)
def neighbors(x:int):
    out={}
    for d in mods:
        for c in by.get((d,x%d),()):
            num=c.a*x-c.c
            if num%d: continue
            p=num//d
            if 0<p<x:
                assert reverse_apply(x,c.word)==p
                out.setdefault(p,c)
    return tuple(sorted(out.items()))

def orbit_to_cross(n:int):
    y=n;q=0
    out=[(0,n)]
    for j in range(1,H+1):
        bit=y&1
        y=T(y);q+=bit
        out.append((j,y))
        if q<qmin[j]:
            return out,(j,y,q)
    raise AssertionError(("no crossing",n))

def below(target:int,n:int):
    stack=[(target,0)]
    seen={target}
    expanded=0
    while stack:
        x,dist=stack.pop()
        expanded+=1
        if expanded>NODE_CAP:
            return {"status":"NODE_CAP","expanded":expanded,"seen":len(seen)}
        for p,c in neighbors(x):
            nd=dist+c.steps
            if p<n:
                z=p
                for _ in range(nd):z=T(z)
                assert z==target
                return {"status":"LOWER_SOURCE","p":p,"b":nd,
                        "last_word":c.word,"expanded":expanded,"seen":len(seen)}
            if p not in seen:
                seen.add(p);stack.append((p,nd))
    return {"status":"NO_LOWER_SOURCE","expanded":expanded,"seen":len(seen)}

rows=[]
for n in SOURCES:
    orb,cross=orbit_to_cross(n)
    cj,cy,cq=cross
    hit=None
    maxexp=0
    for a,y in orb[:-1]:
        h=below(y,n);maxexp=max(maxexp,h["expanded"])
        if h["status"]=="NODE_CAP":
            hit={"constructor":"NODE_CAP","a":a,**h};break
        if h["status"]=="LOWER_SOURCE":
            p=h["p"];b=h["b"]
            x=n
            for _ in range(a):x=T(x)
            z=p
            for _ in range(b):z=T(z)
            assert x==y==z and 0<p<n
            hit={"constructor":"RECURSIVE_Q18_REVERSE","a":a,"p":p,"b":b,
                 "common":y,"max_nodes_expanded":maxexp}
            break
    direct=cy<n
    rows.append({"n":n,"crossing":cj,"crossing_endpoint":cy,
                 "reverse_before_cross":hit,"direct_descent_at_cross":direct})

nodecaps=[r for r in rows if r["reverse_before_cross"] and r["reverse_before_cross"]["constructor"]=="NODE_CAP"]
assert not nodecaps,nodecaps
covered=[r["n"] for r in rows if r["reverse_before_cross"] is not None]
residual=[r["n"] for r in rows if r["reverse_before_cross"] is None]
assert all(r["direct_descent_at_cross"] for r in rows)

print(json.dumps({
  "schema":"COLLATZ_CONSTRUCTOR_COVERAGE_Q18_RESIDUAL_V1",
  "reverse_bank_Q":Q,
  "reverse_certificates":len(certs),
  "sources":SOURCES,
  "q18_pre_cross_covered":covered,
  "q18_pre_cross_residual":residual,
  "rows":rows,
  "status":"Q18_PROTECTED_RESIDUAL_AUDIT",
  "decision":("DEEPER_REVERSE_ADDS_PROTECTED_GAIN" if covered else
              "NO_PROTECTED_GAIN_FROM_Q18_ON_RESIDUAL"),
  "next":("compile new certificates and continue only on residual" if covered else
          "stop blind reverse-depth expansion; derive symbolic law on residual"),
  "global_collatz":"UNKNOWN"
},indent=2))
