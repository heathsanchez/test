#!/usr/bin/env python3
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"

def relabel(obj, p):
    return tuple(
        frozenset((p[u], p[v]) for u, v in rel)
        for rel in obj
    )

def source_iso(a, b, n):
    return any(relabel(a, p) == b for p in itertools.permutations(range(n)))

def encode(obj, n):
    m = len(obj)
    roles = 2 * m + 1
    fresh = roles - 1
    idx = lambda v, role: roles * v + role
    edges = set()

    for r, rel in enumerate(obj):
        tail, head = 2 * r, 2 * r + 1
        for u, v in rel:
            edges.add(tuple(sorted((idx(u, tail), idx(v, head)))))

    # Synthesized table 1111 selects every relation.
    for r in range(m):
        for role in (2 * r, 2 * r + 1):
            for v in range(n):
                edges.add(tuple(sorted((idx(v, role), idx(v, fresh)))))

    return sorted(edges)

def lean_edges(edges):
    return "[" + ", ".join(f"({u},{v})" for u, v in edges) + "]"

def as_json(obj):
    return [[list(e) for e in sorted(rel)] for rel in obj]

def main():
    evidence = json.loads((OUT / "evidence.json").read_text())
    if not evidence["verdict"].startswith("QUALIFIED"):
        raise RuntimeError("V8 qualification did not authorize held-out generation")
    primitive = json.loads((OUT / "synthesized_primitive.json").read_text())
    if primitive["bits"] != "1111":
        raise RuntimeError("unexpected synthesized primitive")

    A = (
        frozenset({(0,1), (1,2)}),
        frozenset({(0,2)}),
        frozenset({(2,0), (1,0)}),
        frozenset({(2,1)}),
    )
    p = (1,2,0)
    B = relabel(A, p)
    C = (
        frozenset({(0,1), (1,2)}),
        frozenset({(0,2)}),
        frozenset({(2,0), (1,0)}),
        frozenset(),
    )

    if not source_iso(A, B, 3):
        raise RuntimeError("positive held-out pair is not isomorphic")
    if source_iso(A, C, 3):
        raise RuntimeError("negative held-out pair unexpectedly isomorphic")

    encA, encB, encC = encode(A,3), encode(B,3), encode(C,3)

    source = f"""import HexGraphIso.Tactic

open Hex Hex.GraphIso

/-
GENERATED AFTER V8 QUALIFICATION.
Four named directed relations on carrier size 3.
The selector primitive was synthesized as the anonymous Boolean truth
table 1111 over the prior FIRST/LAST observations; no TRUE atom is used
as an available constructor in V8.
-/

def roleColoring27 : Coloring 27 9 := Coloring.mod 27 9

def encA : Colored 27 9 where
  graph := Graph.ofEdges {lean_edges(encA)}
  coloring := roleColoring27

def encB : Colored 27 9 where
  graph := Graph.ofEdges {lean_edges(encB)}
  coloring := roleColoring27

def encC : Colored 27 9 where
  graph := Graph.ofEdges {lean_edges(encC)}
  coloring := roleColoring27

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso
"""
    (ROOT / "Generated.lean").write_text(source)

    meta = {
        "heldout_relation_count": 4,
        "heldout_carrier_size": 3,
        "positive_a": as_json(A),
        "positive_b": as_json(B),
        "negative_c": as_json(C),
        "synthesized_truth_table": "1111",
        "generated_lean_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }
    (OUT / "generation.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(meta, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
