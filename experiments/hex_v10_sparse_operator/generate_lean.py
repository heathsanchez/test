#!/usr/bin/env python3
import hashlib, itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"

def relabel(obj,p):
    return tuple(frozenset((p[u],p[v]) for u,v in E) for E in obj)

def source_iso(a,b,n):
    return any(relabel(a,p)==b for p in itertools.permutations(range(n)))

def pattern(i,m):
    return 2*int(i==0)+int(i==m-1)

def select(table,m):
    return [i for i in range(m) if table[pattern(i,m)]]

def encode(obj,n,selected):
    m=len(obj); roles=2*m+1; fresh=2*m
    idx=lambda v,r:roles*v+r
    edges=set()
    for rel,E in enumerate(obj):
        for u,v in E:
            edges.add(tuple(sorted((idx(u,2*rel),idx(v,2*rel+1)))))
    for rel in selected:
        for role in (2*rel,2*rel+1):
            for v in range(n):
                edges.add(tuple(sorted((idx(v,role),idx(v,fresh)))))
    return sorted(edges)

def lean_edges(es):
    return "["+", ".join(f"({a},{b})" for a,b in es)+"]"

def main():
    e=json.loads((OUT/"evidence.json").read_text())
    if not e["verdict"].startswith("QUALIFIED"):
        raise RuntimeError("V10 not qualified")
    table=e["final_truth_table"]
    selected=select(table,6)
    if selected!=list(range(6)):
        raise RuntimeError(("unexpected six-relation selection",selected))

    A=(
      frozenset({(0,1)}),
      frozenset({(0,1)}),
      frozenset({(1,0)}),
      frozenset({(0,1)}),
      frozenset({(1,0)}),
      frozenset({(0,1),(1,0)})
    )
    p=(1,0)
    B=relabel(A,p)
    C=(
      frozenset({(0,1)}),
      frozenset({(0,1)}),
      frozenset({(1,0)}),
      frozenset({(1,0)}),
      frozenset({(1,0)}),
      frozenset({(0,1),(1,0)})
    )
    assert source_iso(A,B,2)
    assert not source_iso(A,C,2)

    a,b,c=encode(A,2,selected),encode(B,2,selected),encode(C,2,selected)
    source=f"""import HexGraphIso.Tactic

open Hex Hex.GraphIso

/-
Generated after V10 sparse operator construction.
Six named directed relations over a two-vertex carrier.
The selector table was built cell-by-cell from staged unseen-pattern residuals.
-/

def roleColoring26 : Coloring 26 13 := Coloring.mod 26 13

def encA : Colored 26 13 where
  graph := Graph.ofEdges {lean_edges(a)}
  coloring := roleColoring26

def encB : Colored 26 13 where
  graph := Graph.ofEdges {lean_edges(b)}
  coloring := roleColoring26

def encC : Colored 26 13 where
  graph := Graph.ofEdges {lean_edges(c)}
  coloring := roleColoring26

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso
"""
    (ROOT/"Generated.lean").write_text(source)
    meta={
      "heldout_relation_count":6,
      "heldout_carrier_size":2,
      "constructed_truth_table":table,
      "selected_relations":selected,
      "generated_lean_sha256":hashlib.sha256(source.encode()).hexdigest()
    }
    (OUT/"generation.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    print(json.dumps(meta,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
