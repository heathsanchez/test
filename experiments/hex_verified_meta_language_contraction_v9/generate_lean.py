#!/usr/bin/env python3
import hashlib, itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"

def relabel(obj,p):
    return tuple(frozenset((p[u],p[v]) for u,v in E) for E in obj)

def source_iso(a,b,n):
    return any(relabel(a,p)==b for p in itertools.permutations(range(n)))

def encode_all(obj,n):
    m=len(obj)
    roles=2*m+1
    fresh=2*m
    idx=lambda v,r:roles*v+r
    edges=set()
    for rel,E in enumerate(obj):
        for u,v in E:
            edges.add(tuple(sorted((idx(u,2*rel),idx(v,2*rel+1)))))
    for rel in range(m):
        for role in (2*rel,2*rel+1):
            for v in range(n):
                edges.add(tuple(sorted((idx(v,role),idx(v,fresh)))))
    return sorted(edges)

def lean_edges(edges):
    return "["+", ".join(f"({u},{v})" for u,v in edges)+"]"

def main():
    e=json.loads((OUT/"evidence.json").read_text())
    if not e["verdict"].startswith("QUALIFIED"):
        raise RuntimeError("V9 contraction not qualified")
    if e["contracted_dependency_set"]["keep"]!=[] or e["contracted_output"]!=1:
        raise RuntimeError("unexpected contraction")

    A=(
        frozenset({(0,1)}),
        frozenset({(0,1)}),
        frozenset({(1,0)}),
        frozenset({(0,1)}),
        frozenset({(0,1),(1,0)})
    )
    p=(1,0)
    B=relabel(A,p)
    C=(
        frozenset({(0,1)}),
        frozenset({(0,1)}),
        frozenset({(1,0)}),
        frozenset({(1,0)}),
        frozenset({(0,1),(1,0)})
    )
    assert source_iso(A,B,2)
    assert not source_iso(A,C,2)

    a,b,c=encode_all(A,2),encode_all(B,2),encode_all(C,2)
    source=f"""import HexGraphIso.Tactic

open Hex Hex.GraphIso

/-
Generated after V9 verified contraction.
Five named directed relations, carrier size 2.
The retained selector has no FIRST/LAST inputs: it returns 1 unconditionally,
so every relation receives the identity-channel coupling.
-/

def roleColoring22 : Coloring 22 11 := Coloring.mod 22 11

def encA : Colored 22 11 where
  graph := Graph.ofEdges {lean_edges(a)}
  coloring := roleColoring22

def encB : Colored 22 11 where
  graph := Graph.ofEdges {lean_edges(b)}
  coloring := roleColoring22

def encC : Colored 22 11 where
  graph := Graph.ofEdges {lean_edges(c)}
  coloring := roleColoring22

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso
"""
    (ROOT/"Generated.lean").write_text(source)
    meta={
        "heldout_relation_count":5,
        "heldout_carrier_size":2,
        "selector_dependency_count":0,
        "selector_constant_output":1,
        "generated_lean_sha256":hashlib.sha256(source.encode()).hexdigest()
    }
    (OUT/"generation.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    print(json.dumps(meta,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
