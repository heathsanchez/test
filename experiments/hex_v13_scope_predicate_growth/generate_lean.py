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
    return f"{pos}|{i % 5}"

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
        raise RuntimeError("V13 not qualified")
    if e["active_scope_predicates_after_growth"] != []:
        raise RuntimeError("scope growth incomplete")
    policy = e["final_policy"]
    selected = select(policy, 6)
    if selected != list(range(6)):
        raise RuntimeError(("unexpected six-relation selection", selected))

    # Same relation count as the final qualification stage, but new multi-arc objects.
    A = (
        frozenset({(0,1)}),
        frozenset({(0,1),(1,0)}),
        frozenset({(1,0)}),
        frozenset({(0,1)}),
        frozenset({(1,0)}),
        frozenset({(0,1),(1,0)}),
    )
    p = (1,0)
    B = relabel(A, p)
    C = (
        frozenset({(0,1)}),
        frozenset({(0,1),(1,0)}),
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
Generated after V13 removed two empirically induced scope predicates only
when typed residuals falsified them. Six named directed relations, carrier 2.
These are held-out multi-arc objects, not members of the one-arc qualification world.
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
    (ROOT / "Generated.lean").write_text(source)
    meta = {
        "heldout_relation_count": 6,
        "heldout_carrier_size": 2,
        "heldout_kind": "multi_arc",
        "selected_relations": selected,
        "generated_lean_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }
    (OUT / "generation.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(json.dumps(meta, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
