#!/usr/bin/env python3
import hashlib, itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"

def relabel(obj,p):
    return tuple(frozenset((p[u],p[v]) for u,v in E) for E in obj)

def source_iso(a,b):
    return any(relabel(a,p)==b for p in itertools.permutations(range(3)))

def encode(obj):
    roles=7
    fresh=6
    edges=set()
    for rel,E in enumerate(obj):
        for u,v in E:
            edges.add(tuple(sorted((roles*u+2*rel,roles*v+2*rel+1))))
    for rel in range(3):
        for role in (2*rel,2*rel+1):
            for v in range(3):
                edges.add(tuple(sorted((roles*v+role,roles*v+fresh))))
    return sorted(edges)

def lean_edges(es):
    return "["+", ".join(f"({a},{b})" for a,b in es)+"]"

def main():
    e=json.loads((OUT/"evidence.json").read_text())
    if e["verdict"]!="VERIFIED_META_RULE_GENESIS":
        raise RuntimeError("V7 selector not qualified")
    if e["selected_program"]!=["ATOM","TRUE"]:
        raise RuntimeError("unexpected selected selector")

    A=(
      frozenset({(0,1),(1,2)}),
      frozenset({(0,2)}),
      frozenset({(2,0),(1,0)})
    )
    p=(1,2,0)
    B=relabel(A,p)
    C=(
      frozenset({(0,1),(1,2)}),
      frozenset({(0,2)}),
      frozenset({(2,0)})
    )
    assert source_iso(A,B)
    assert not source_iso(A,C)

    a,b,c=encode(A),encode(B),encode(C)
    source=f"""import HexGraphIso.Tactic

open Hex Hex.GraphIso

/-
Generated after V7 meta-rule selection.
Three named directed relations on n=3.
Selected selector TRUE connects every active endpoint role to one fresh role.
-/

def roleColoring21 : Coloring 21 7 := Coloring.mod 21 7

def encA : Colored 21 7 where
  graph := Graph.ofEdges {lean_edges(a)}
  coloring := roleColoring21

def encB : Colored 21 7 where
  graph := Graph.ofEdges {lean_edges(b)}
  coloring := roleColoring21

def encC : Colored 21 7 where
  graph := Graph.ofEdges {lean_edges(c)}
  coloring := roleColoring21

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso
"""
    (ROOT/"Generated.lean").write_text(source)
    meta={"heldout_relations":3,"heldout_n":3,
          "generated_lean_sha256":hashlib.sha256(source.encode()).hexdigest()}
    (OUT/"generation.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    print(json.dumps(meta,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
