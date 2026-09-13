#!/usr/bin/env python3
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"

def relabel(obj, p):
    return tuple(frozenset((p[u], p[v]) for u, v in E) for E in obj)

def source_iso(a, b, n):
    return any(relabel(a, p) == b for p in itertools.permutations(range(n)))

def position_tag(i, m):
    if i == 0:
        pos = "LEFT"
    elif i == m - 1:
        pos = "RIGHT"
    else:
        pos = "INTERIOR"
    return f"{pos}|{i % 3}"

def select(policy, m):
    return [i for i in range(m) if policy[position_tag(i, m)]]

def encode(obj, n, selected):
    m = len(obj)
    roles = 2 * m + 1
    fresh = 2 * m
    idx = lambda v, r: roles * v + r
    edges = set()
    for rel, E in enumerate(obj):
        for u, v in E:
            edges.add(tuple(sorted((idx(u, 2 * rel), idx(v, 2 * rel + 1)))))
    for rel in selected:
        for role in (2 * rel, 2 * rel + 1):
            for v in range(n):
                edges.add(tuple(sorted((idx(v, role), idx(v, fresh)))))
    return sorted(edges)

def lean_edges(edges):
    return "[" + ", ".join(f"({u},{v})" for u, v in edges) + "]"

def main():
    e = json.loads((OUT / "evidence.json").read_text())
    if not e["verdict"].startswith("QUALIFIED"):
        raise RuntimeError("V12 not qualified")
    policy = e["final_policy"]
    selected = select(policy, 8)
    if selected != list(range(8)):
        raise RuntimeError(("unexpected eight-relation selection", selected))

    A = (
        frozenset({(0,1)}),
        frozenset({(0,1)}),
        frozenset({(1,0)}),
        frozenset({(0,1)}),
        frozenset({(1,0)}),
        frozenset({(0,1)}),
        frozenset({(1,0)}),
        frozenset({(0,1),(1,0)}),
    )
    p = (1,0)
    B = relabel(A, p)
    C = (
        frozenset({(0,1)}),
        frozenset({(0,1)}),
        frozenset({(1,0)}),
        frozenset({(0,1)}),
        frozenset({(1,0)}),
        frozenset({(1,0)}),
        frozenset({(1,0)}),
        frozenset({(0,1),(1,0)}),
    )
    assert source_iso(A, B, 2)
    assert not source_iso(A, C, 2)

    a, b, c = encode(A, 2, selected), encode(B, 2, selected), encode(C, 2, selected)
    source = f"""import HexGraphIso.Tactic

open Hex Hex.GraphIso

/-
Generated after V12 selected repair-schema generality by consequence.
Eight named directed relations over a two-vertex carrier.
The active selector keys are POSITION|TAG with TAG = relation index mod 3.
-/

def roleColoring34 : Coloring 34 17 := Coloring.mod 34 17

def encA : Colored 34 17 where
  graph := Graph.ofEdges {lean_edges(a)}
  coloring := roleColoring34

def encB : Colored 34 17 where
  graph := Graph.ofEdges {lean_edges(b)}
  coloring := roleColoring34

def encC : Colored 34 17 where
  graph := Graph.ofEdges {lean_edges(c)}
  coloring := roleColoring34

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso
"""
    (ROOT / "Generated.lean").write_text(source)
    meta = {
        "heldout_relation_count": 8,
        "heldout_carrier_size": 2,
        "selected_relations": selected,
        "generated_lean_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }
    (OUT / "generation.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(json.dumps(meta, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
