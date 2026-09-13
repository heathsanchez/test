#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

def relabel(edges, p):
    return frozenset((p[u], p[v]) for u, v in edges)

def symmetrize(edges):
    return frozenset(tuple(sorted((u, v))) for u, v in edges)

def encode(edges, n, c):
    roles = c["roles"]
    a, b = c["arc_channel"]
    idx = lambda v, role: roles * v + role
    target = set()
    for u, v in edges:
        x, y = idx(u, a), idx(v, b)
        if x != y:
            target.add(tuple(sorted((x, y))))
    for x, y in c["identity_couplings"]:
        for v in range(n):
            target.add(tuple(sorted((idx(v, x), idx(v, y)))))
    return sorted(target)

def lean_edges(edges):
    return "[" + ", ".join(f"({u},{v})" for u, v in edges) + "]"

def main():
    c = json.loads((RESULTS / "selected_adapter.json").read_text())
    roles = c["roles"]

    # Held out from qualification: n=4 only.
    A = frozenset({(0, 1), (1, 2), (2, 3)})
    p = (2, 0, 3, 1)
    B = relabel(A, p)
    C = frozenset({(0, 1), (2, 1), (2, 3)})

    encA = encode(A, 4, c)
    encB = encode(B, 4, c)
    encC = encode(C, 4, c)
    N = 4 * roles

    lossA = sorted(symmetrize(A))
    lossC = sorted(symmetrize(C))

    source = f"""import HexGraphIso.Tactic

open Hex Hex.GraphIso

/-
GENERATED AFTER QUALIFICATION.
Selected adapter:
  roles = {roles}
  arc_channel = {c["arc_channel"]}
  identity_couplings = {c["identity_couplings"]}
Qualification used n=3 only. These obligations use held-out n=4 objects.
-/

def selectedColoring : Coloring {N} {roles} := Coloring.mod {N} {roles}

def encA : Colored {N} {roles} where
  graph := Graph.ofEdges {lean_edges(encA)}
  coloring := selectedColoring

def encB : Colored {N} {roles} where
  graph := Graph.ofEdges {lean_edges(encB)}
  coloring := selectedColoring

def encC : Colored {N} {roles} where
  graph := Graph.ofEdges {lean_edges(encC)}
  coloring := selectedColoring

set_option trace.graph_iso true in
example : Isomorphic encA encB := by
  graph_iso

set_option trace.graph_iso true in
example : ¬ Isomorphic encA encC := by
  graph_iso

def lossyA : Graph 4 := Graph.ofEdges {lean_edges(lossA)}
def lossyC : Graph 4 := Graph.ofEdges {lean_edges(lossC)}

set_option trace.graph_iso true in
example : Graph.Isomorphic lossyA lossyC := by
  graph_iso
"""
    out = ROOT / "Generated.lean"
    out.write_text(source)
    meta = {
        "selected_adapter": c,
        "heldout_n": 4,
        "positive_source_a": sorted(map(list, A)),
        "positive_source_b": sorted(map(list, B)),
        "negative_source_c": sorted(map(list, C)),
        "generated_lean_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }
    (RESULTS / "generation.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(json.dumps(meta, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
