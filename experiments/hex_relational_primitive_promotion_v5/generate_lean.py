#!/usr/bin/env python3
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"

def relabel(obj, p):
    return tuple(
        frozenset((p[u], p[v]) for u, v in E)
        for E in obj
    )

def source_iso(a, b, n):
    return any(relabel(a, p) == b for p in itertools.permutations(range(n)))

def encode(obj, n):
    roles = 5
    idx = lambda v, role: roles * v + role
    target = set()
    for rel_id, E in enumerate(obj):
        a, b = 2 * rel_id, 2 * rel_id + 1
        for u, v in E:
            target.add(tuple(sorted((idx(u, a), idx(v, b)))))
    for role in range(4):
        for v in range(n):
            target.add(tuple(sorted((idx(v, role), idx(v, 4)))))
    return sorted(target)

def lean_edges(edges):
    return "[" + ", ".join(f"({u},{v})" for u, v in edges) + "]"

def json_obj(obj):
    return [[list(e) for e in sorted(E)] for E in obj]

def main():
    evidence = json.loads((OUT / "qualification.json").read_text())
    if not evidence["verdict"].startswith("QUALIFIED"):
        raise RuntimeError("qualification did not authorize held-out generation")

    # Held-out n=4, with multiple arcs per relation.
    A = (
        frozenset({(0,1), (1,2), (2,3)}),
        frozenset({(0,2), (1,3)}),
    )
    p = (2,0,3,1)
    B = relabel(A, p)
    C = (
        frozenset({(0,1), (1,2), (2,3)}),
        frozenset({(0,2)}),
    )

    if not source_iso(A, B, 4):
        raise RuntimeError("positive held-out source pair is not isomorphic")
    if source_iso(A, C, 4):
        raise RuntimeError("negative held-out source pair unexpectedly isomorphic")

    encA, encB, encC = encode(A,4), encode(B,4), encode(C,4)
    source = f"""import HexGraphIso.Tactic

open Hex Hex.GraphIso

/-
GENERATED AFTER V5 QUALIFICATION.
Two named directed binary relations, n=4 held out from the n=3
one-arc-per-relation qualification world.
The promoted macro instantiates one fresh identity role coupled to all
four active relation endpoint roles.
-/

def roleColoring20 : Coloring 20 5 := Coloring.mod 20 5

def encA : Colored 20 5 where
  graph := Graph.ofEdges {lean_edges(encA)}
  coloring := roleColoring20

def encB : Colored 20 5 where
  graph := Graph.ofEdges {lean_edges(encB)}
  coloring := roleColoring20

def encC : Colored 20 5 where
  graph := Graph.ofEdges {lean_edges(encC)}
  coloring := roleColoring20

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso
"""
    (ROOT / "Generated.lean").write_text(source)
    meta = {
        "heldout_n": 4,
        "positive_a": json_obj(A),
        "positive_b": json_obj(B),
        "negative_c": json_obj(C),
        "generated_lean_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "macro": evidence["induced_macro"],
    }
    (OUT / "generation.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(meta, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
