#!/usr/bin/env python3
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"

def relabel(rel, p):
    return frozenset(tuple(p[x] for x in t) for t in rel)

def source_iso(a, b, n):
    return any(relabel(a, p) == b for p in itertools.permutations(range(n)))

def encode_full_star(rel, n, arity):
    tuples = sorted(rel)
    if len(tuples) != n:
        raise ValueError("held-out generator requires tuple_count == carrier_size")
    roles = arity + 2
    anchor_role = arity
    occurrence_role = arity + 1
    idx = lambda row, role: roles * row + role
    edges = set()

    # One argument-role copy of each source vertex, tied to a common identity anchor.
    for v in range(n):
        for pos in range(arity):
            edges.add(tuple(sorted((idx(v, pos), idx(v, anchor_role)))))

    # One same-coloured occurrence node per tuple, connected to every argument role.
    for occ, tup in enumerate(tuples):
        for pos, v in enumerate(tup):
            edges.add(tuple(sorted((idx(occ, occurrence_role), idx(v, pos)))))

    return sorted(edges), roles * n, roles

def lean_edges(edges):
    return "[" + ", ".join(f"({u},{v})" for u, v in edges) + "]"

def emit(path, arity, A, B, C):
    n = 3
    ea, N, colors = encode_full_star(A, n, arity)
    eb, _, _ = encode_full_star(B, n, arity)
    ec, _, _ = encode_full_star(C, n, arity)

    source = f"""import HexGraphIso.Tactic

open Hex Hex.GraphIso

/-
Generated only after V19 selected ALL_ACTIVE.
Held-out relation arity {arity}, carrier {n}, tuple count {n}.
Each tuple occurrence is connected to every active argument-position role.
-/

def roleColoring : Coloring {N} {colors} := Coloring.mod {N} {colors}

def encA : Colored {N} {colors} where
  graph := Graph.ofEdges {lean_edges(ea)}
  coloring := roleColoring

def encB : Colored {N} {colors} where
  graph := Graph.ofEdges {lean_edges(eb)}
  coloring := roleColoring

def encC : Colored {N} {colors} where
  graph := Graph.ofEdges {lean_edges(ec)}
  coloring := roleColoring

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso
"""
    (ROOT / path).write_text(source)
    return {
        "arity": arity,
        "carrier_size": n,
        "tuple_count": n,
        "node_count": N,
        "color_count": colors,
        "sha256": hashlib.sha256(source.encode()).hexdigest(),
    }

def main():
    ev = json.loads((OUT / "evidence.json").read_text())
    if ev["verdict"] != "QUALIFIED_ALL_ACTIVE_ARITY_LAW_FOR_HEX_HELDOUT":
        raise RuntimeError("V19 law selection did not qualify")
    if ev["selected_law"] != "ALL_ACTIVE":
        raise RuntimeError("unexpected selected law")

    p = (1,2,0)

    A4 = frozenset({
        (0,0,1,2),
        (1,2,0,1),
        (2,1,2,0),
    })
    B4 = relabel(A4, p)
    C4 = frozenset({
        (0,0,1,2),
        (1,2,0,1),
        (2,1,2,1),
    })
    assert source_iso(A4, B4, 3)
    assert not source_iso(A4, C4, 3)

    A5 = frozenset({
        (0,0,1,2,1),
        (1,2,0,1,0),
        (2,1,2,0,2),
    })
    B5 = relabel(A5, p)
    C5 = frozenset({
        (0,0,1,2,1),
        (1,2,0,1,0),
        (2,1,2,0,1),
    })
    assert source_iso(A5, B5, 3)
    assert not source_iso(A5, C5, 3)

    meta = {
        "selected_law": "ALL_ACTIVE",
        "arity4": emit("Arity4.lean", 4, A4, B4, C4),
        "arity5": emit("Arity5.lean", 5, A5, B5, C5),
    }
    (OUT / "generation.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(json.dumps(meta, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
