#!/usr/bin/env python3
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"

HEX_RELEASE = {
    "repo": "leanprover/hex-graph-iso",
    "tag": "v0.6.0",
    "commit": "f247c0898414ca29c502691e3a8ad0b3ce0b4f6a",
    "lean_toolchain": "leanprover/lean4:v4.34.0-rc2",
}

def digest(obj):
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()

def all_loopless_digraphs(n):
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    for bits in range(1 << len(arcs)):
        yield frozenset(a for k, a in enumerate(arcs) if (bits >> k) & 1)

def relabel_digraph(edges, p):
    return frozenset((p[u], p[v]) for u, v in edges)

def source_iso(a, b, n):
    return any(relabel_digraph(a, p) == b for p in itertools.permutations(range(n)))

def role_split_anchor(edges, n):
    # Interleave OUT/IN/ANCHOR so Hex's verified Coloring.mod (i % 3)
    # supplies the role colouring without an extra proof obligation.
    out = lambda v: 3 * v
    inn = lambda v: 3 * v + 1
    anchor = lambda v: 3 * v + 2
    target_edges = set()
    for v in range(n):
        target_edges.add(tuple(sorted((anchor(v), out(v)))))
        target_edges.add(tuple(sorted((anchor(v), inn(v)))))
    for u, v in edges:
        target_edges.add(tuple(sorted((out(u), inn(v)))))
    colors = tuple(i % 3 for i in range(3 * n))
    return frozenset(target_edges), colors

def color_preserving_iso(a, b):
    ea, ca = a
    eb, cb = b
    if len(ca) != len(cb):
        return False
    color_ids = sorted(set(ca))
    classes = []
    for c in color_ids:
        left = [i for i, x in enumerate(ca) if x == c]
        right = [i for i, x in enumerate(cb) if x == c]
        if len(left) != len(right):
            return False
        classes.append((left, right))
    choices = [list(itertools.permutations(right)) for _, right in classes]
    for selected in itertools.product(*choices):
        p = [None] * len(ca)
        for (left, _), image in zip(classes, selected):
            for x, y in zip(left, image):
                p[x] = y
        mapped = frozenset(tuple(sorted((p[u], p[v]))) for u, v in ea)
        if mapped == eb:
            return True
    return False

def symmetrize(edges):
    return frozenset(tuple(sorted((u, v))) for u, v in edges)

def undirected_iso(a, b, n):
    for p in itertools.permutations(range(n)):
        mapped = frozenset(tuple(sorted((p[u], p[v]))) for u, v in a)
        if mapped == b:
            return True
    return False

def as_json_edges(edges):
    return [list(e) for e in sorted(edges)]

def qualify_n3():
    graphs = list(all_loopless_digraphs(3))
    correct_mismatches = []
    lossy_mismatches = []
    ordered_pairs = 0

    for a in graphs:
        enca = role_split_anchor(a, 3)
        syma = symmetrize(a)
        for b in graphs:
            ordered_pairs += 1
            source = source_iso(a, b, 3)
            target = color_preserving_iso(enca, role_split_anchor(b, 3))
            if source != target:
                correct_mismatches.append({
                    "a": as_json_edges(a), "b": as_json_edges(b),
                    "source_iso": source, "target_iso": target,
                })
            lossy = undirected_iso(syma, symmetrize(b), 3)
            if source != lossy:
                lossy_mismatches.append({
                    "a": as_json_edges(a), "b": as_json_edges(b),
                    "source_iso": source, "lossy_target_iso": lossy,
                })

    return {
        "n": 3,
        "graph_count": len(graphs),
        "ordered_pair_count": ordered_pairs,
        "role_split_anchor_mismatch_count": len(correct_mismatches),
        "symmetrize_mismatch_count": len(lossy_mismatches),
        "first_role_split_anchor_mismatch": correct_mismatches[0] if correct_mismatches else None,
        "first_symmetrize_mismatch": lossy_mismatches[0] if lossy_mismatches else None,
    }

def heldout_n4():
    a = frozenset({(0, 1), (1, 2), (2, 3)})
    p = (2, 0, 3, 1)
    b = relabel_digraph(a, p)
    c = frozenset({(0, 1), (2, 1), (2, 3)})

    checks = {
        "positive_source_iso": source_iso(a, b, 4),
        "positive_target_iso": color_preserving_iso(role_split_anchor(a, 4), role_split_anchor(b, 4)),
        "negative_source_noniso": not source_iso(a, c, 4),
        "negative_target_noniso": not color_preserving_iso(role_split_anchor(a, 4), role_split_anchor(c, 4)),
        "lossy_control_false_positive": undirected_iso(symmetrize(a), symmetrize(c), 4),
    }
    return {
        "n": 4,
        "a": as_json_edges(a),
        "positive_b": as_json_edges(b),
        "negative_c": as_json_edges(c),
        "permutation_old_to_new": list(p),
        "checks": checks,
        "encoded_a": as_json_edges(role_split_anchor(a, 4)[0]),
        "encoded_b": as_json_edges(role_split_anchor(b, 4)[0]),
        "encoded_c": as_json_edges(role_split_anchor(c, 4)[0]),
    }

def main():
    qualification = qualify_n3()
    heldout = heldout_n4()
    gates = {
        "G1_complete_n3_world": qualification["graph_count"] == 64 and qualification["ordered_pair_count"] == 4096,
        "G2_candidate_zero_semantic_disagreement": qualification["role_split_anchor_mismatch_count"] == 0,
        "G3_lossy_control_rejected": qualification["symmetrize_mismatch_count"] > 0,
        "G4_heldout_source_positive": heldout["checks"]["positive_source_iso"],
        "G5_heldout_target_positive": heldout["checks"]["positive_target_iso"],
        "G6_heldout_source_negative": heldout["checks"]["negative_source_noniso"],
        "G7_heldout_target_negative": heldout["checks"]["negative_target_noniso"],
        "G8_lossy_heldout_false_positive": heldout["checks"]["lossy_control_false_positive"],
    }

    snapshot = {
        "source_domain": "loopless directed graphs",
        "qualification_size": 3,
        "heldout_size": 4,
        "candidate_adapters": ["ROLE_SPLIT_ANCHOR", "SYMMETRIZE"],
        "hex_release": HEX_RELEASE,
    }
    verdict = "QUALIFIED_FOR_HEX_HELDOUT_CHECK" if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    evidence = {
        "verdict": verdict,
        "classification": "FINITE_EXHAUSTIVE_ADAPTER_QUALIFICATION_PILOT",
        "snapshot": snapshot,
        "snapshot_digest": digest(snapshot),
        "qualification": qualification,
        "heldout": heldout,
        "gates": gates,
        "claim_boundary": [
            "No general all-n proof of adapter faithfulness",
            "No learned adapter discovery",
            "No open-ended transfer",
            "Hex correctness is external authority, not re-proved here",
        ],
    }

    OUT.mkdir(exist_ok=True)
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if verdict.startswith("QUALIFIED") else 1

if __name__ == "__main__":
    raise SystemExit(main())
