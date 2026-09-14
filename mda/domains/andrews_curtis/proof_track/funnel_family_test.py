#!/usr/bin/env python3
"""Prospective verifier-grounded test of the funnel family R_{m,k}.

R_{m,k} = (x y^{-m} x^{-1} y^{m+1}, y^{-k} x^{-1}).

The construction is fixed symbolically before the grid is replayed:
  1. left-multiply A by B;
  2. conjugate B by y^{-m};
  3. left-multiply A by B^{-1};
  4. conjugate B back by y^m;
  5. left-multiply B by A=y, k times;
  6. invert B;
  7. exchange (y,x) to (x,y).

Atomic conjugations by a word are compiled into the official one-letter
conjugation moves. No search is performed.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

GENS=(1,-1,2,-2)
TARGET=((1,),(2,))

def red(w):
    out=[]
    for a in w:
        if out and out[-1]==-a: out.pop()
        else: out.append(a)
    return tuple(out)

def inv(w): return tuple(-a for a in reversed(w))

def family_state(m,k):
    return (
      red((1,)+(-2,)*m+(-1,)+(2,)*(m+1)),
      red((-2,)*k+(-1,))
    )

def conj_moves(rel,w):
    mp=({1:6,-1:7,2:8,-2:9} if rel==0
        else {1:10,-1:11,2:12,-2:13})
    return [mp[a] for a in reversed(w)]

def build(core,m,k):
    st=family_state(m,k); p=[]
    def emit(ms):
        nonlocal st
        for z in ms:
            st=core.apply_move(st,z);p.append(z)
    # left A by B: A -> B A
    B=st[1]; emit([2]+conj_moves(0,B))
    # B -> C = y^-m B y^m
    emit([13]*m)
    # A=C y -> C^-1 A = y
    B=st[1]; emit([3]+conj_moves(0,inv(B)))
    # C -> original B
    emit([12]*m)
    # y^-k x^-1 -> x^-1
    for _ in range(k): emit([4,12])
    emit([1])
    if st != ((2,),(1,)):
        raise RuntimeError(("pre-swap invariant",m,k,st))
    # fixed exact exchange of (y,x) to (x,y)
    emit([0,2,5,2,8])
    return p,st

def main():
    acc=Path(sys.argv[1]);out=Path(sys.argv[2])
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]
    rows=[]
    # Development and prospective ranges are declared in code before outcomes.
    grids=[
      ("development",range(0,5),range(0,9)),
      ("prospective",range(5,9),range(9,14)),
    ]
    for split,ms,ks in grids:
      for m in ms:
       for k in ks:
        p,end=build(core,m,k)
        challenge={
          "challenge_id":f"synthetic-funnel-{m}-{k}",
          "move_spec_version":core.MOVE_SPEC_VERSION,
          "initial_relators":[list(w) for w in family_state(m,k)],
          "target_relators":[[1],[2]],
        }
        v=core.verify(challenge,p,core.MOVE_SPEC_VERSION,limits)
        rows.append({"split":split,"m":m,"k":k,"length":len(p),
                     "ok":bool(v.get("ok")),"work":v.get("work"),
                     "hash":v.get("certificate_hash")})
        if not v.get("ok"): raise RuntimeError((m,k,v))
    report={
      "experiment":"ACC_PARAMETERIZED_FUNNEL_FAMILY_V1",
      "status":"VERIFIED_PARAMETERIZED_CONSTRUCTION_ON_FROZEN_GRID",
      "family":"(x y^-m x^-1 y^(m+1), y^-k x^-1)",
      "development_cases":sum(r["split"]=="development" for r in rows),
      "prospective_cases":sum(r["split"]=="prospective" for r in rows),
      "failures":sum(not r["ok"] for r in rows),
      "m2k7_length":next(r["length"] for r in rows if r["m"]==2 and r["k"]==7),
      "claim_boundary":"Finite official-semantics validation of a symbolic construction. Universal m,k claim requires the companion Lean proof."
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"cases.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    print("FUNNEL_FAMILY",json.dumps(report,sort_keys=True))

if __name__=="__main__":main()
