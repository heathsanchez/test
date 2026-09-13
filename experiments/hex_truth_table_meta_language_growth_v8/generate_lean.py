#!/usr/bin/env python3
import hashlib, itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"

def relabel(obj,p):
    return tuple(frozenset((p[u],p[v]) for u,v in E) for E in obj)

def source_iso(a,b,n):
    return any(relabel(a,p)==b for p in itertools.permutations(range(n)))

def select_relations(tt,m):
    out=[]
    for i in range(m):
        first=int(i==0)
        last=int(i==m-1)
        if tt[2*first+last]:
            out.append(i)
    return out

def encode(obj,n,selected):
    m=len(obj)
    roles=2*m+1
    fresh=2*m
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

def lean_edges(edges):
    return "["+", ".join(f"({u},{v})" for u,v in edges)+"]"

def json_obj(obj):
    return [[list(e) for e in sorted(E)] for E in obj]

def main():
    evidence=json.loads((OUT/"evidence.json").read_text())
    if not evidence["verdict"].startswith("QUALIFIED"):
        raise RuntimeError("V8 qualification did not authorize held-out generation")
    tt=evidence["selected_operator"]["truth_table"]
    selected=select_relations(tt,4)
    if selected!=[0,1,2,3]:
        raise RuntimeError(("selected operator did not scale to four relations",selected))

    A=(
        frozenset({(0,1)}),
        frozenset({(0,1)}),
        frozenset({(1,0)}),
        frozenset({(0,1),(1,0)})
    )
    p=(1,0)
    B=relabel(A,p)
    C=(
        frozenset({(0,1)}),
        frozenset({(1,0)}),
        frozenset({(1,0)}),
        frozenset({(0,1),(1,0)})
    )

    if not source_iso(A,B,2):
        raise RuntimeError("positive held-out pair is not isomorphic")
    if source_iso(A,C,2):
        raise RuntimeError("negative held-out pair unexpectedly isomorphic")

    encA,encB,encC=encode(A,2,selected),encode(B,2,selected),encode(C,2,selected)
    source=f"""import HexGraphIso.Tactic

open Hex Hex.GraphIso

/-
Generated only after V8 selected an anonymous truth-table operator.
Four named directed relations, carrier size 2.
The selected operator is instantiated from FIRST/LAST boundary signals;
its discovered truth table selects all four relations.
-/

def roleColoring18 : Coloring 18 9 := Coloring.mod 18 9

def encA : Colored 18 9 where
  graph := Graph.ofEdges {lean_edges(encA)}
  coloring := roleColoring18

def encB : Colored 18 9 where
  graph := Graph.ofEdges {lean_edges(encB)}
  coloring := roleColoring18

def encC : Colored 18 9 where
  graph := Graph.ofEdges {lean_edges(encC)}
  coloring := roleColoring18

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso
"""
    (ROOT/"Generated.lean").write_text(source)
    meta={
        "heldout_relation_count":4,
        "heldout_carrier_size":2,
        "selected_truth_table":tt,
        "selected_relations":selected,
        "positive_a":json_obj(A),
        "positive_b":json_obj(B),
        "negative_c":json_obj(C),
        "generated_lean_sha256":hashlib.sha256(source.encode()).hexdigest()
    }
    (OUT/"generation.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    print(json.dumps(meta,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
