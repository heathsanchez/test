#!/usr/bin/env python3
import hashlib, itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"

def relabel(table,n,p):
    out=[0]*(n*n)
    for x in range(n):
        for y in range(n):
            out[p[x]*n+p[y]]=p[table[x*n+y]]
    return tuple(out)

def isomorphic(a,b,n):
    return any(relabel(a,n,p)==b for p in itertools.permutations(range(n)))

def encode(table,n):
    L=lambda v:v
    R=lambda v:n+v
    O=lambda v:2*n+v
    A=lambda v:3*n+v
    T=lambda x,y:4*n+x*n+y
    edges=set()
    for x in range(n):
        for y in range(n):
            z=table[x*n+y]
            t=T(x,y)
            edges.add(tuple(sorted((t,L(x)))))
            edges.add(tuple(sorted((t,R(y)))))
            edges.add(tuple(sorted((t,O(z)))))
    for v in range(n):
        edges.add(tuple(sorted((A(v),L(v)))))
        edges.add(tuple(sorted((A(v),R(v)))))
        edges.add(tuple(sorted((A(v),O(v)))))
    return sorted(edges)

def lean_edges(es):
    return "["+", ".join(f"({a},{b})" for a,b in es)+"]"

def main():
    evidence=json.loads((OUT/"evidence.json").read_text())
    if not evidence["verdict"].startswith("QUALIFIED"):
        raise RuntimeError("V9 qualification did not authorize held-out generation")
    selected=json.loads((OUT/"selected_adapter.json").read_text())
    if selected["mask"]!=63:
        raise RuntimeError("unexpected V9 adapter")

    A=(0,1,2,1,2,0,2,0,1)
    p=(1,2,0)
    B=relabel(A,3,p)
    C=(0,1,2,1,2,0,2,0,0)

    if not isomorphic(A,B,3):
        raise RuntimeError("positive magma pair is not isomorphic")
    if isomorphic(A,C,3):
        raise RuntimeError("negative magma pair unexpectedly isomorphic")

    ea,eb,ec=encode(A,3),encode(B,3),encode(C,3)

    cells=", ".join(
        ["0","0","0","1","1","1","2","2","2","3","3","3"]+["4"]*9
    )

    source=f"""import HexGraphIso.Tactic

open Hex Hex.GraphIso

/-
GENERATED AFTER V9 ORDER-2 EXHAUSTIVE QUALIFICATION.
Order-3 finite magmas are encoded with element-role colours L/R/O/A
and one tuple-node colour T.  The selected adapter uses all six
incidence/identity channels.
-/

def magmaFallback : Coloring 21 5 := Coloring.mod 21 5

def magmaColoring : Coloring 21 5 :=
  (Coloring.ofVector? #v[({cells.split(", ")[0]} : Fin 5), {", ".join(cells.split(", ")[1:])}]).getD magmaFallback

def encA : Colored 21 5 where
  graph := Graph.ofEdges {lean_edges(ea)}
  coloring := magmaColoring

def encB : Colored 21 5 where
  graph := Graph.ofEdges {lean_edges(eb)}
  coloring := magmaColoring

def encC : Colored 21 5 where
  graph := Graph.ofEdges {lean_edges(ec)}
  coloring := magmaColoring

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso
"""
    (ROOT/"Generated.lean").write_text(source)
    meta={
      "heldout_order":3,
      "positive_a":list(A),
      "positive_b":list(B),
      "negative_c":list(C),
      "selected_mask":63,
      "generated_lean_sha256":hashlib.sha256(source.encode()).hexdigest()
    }
    (OUT/"generation.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    print(json.dumps(meta,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
