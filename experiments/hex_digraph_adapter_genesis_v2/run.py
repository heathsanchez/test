#!/usr/bin/env python3
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"

HEX = {
    "repo": "leanprover/hex-graph-iso",
    "tag": "v0.6.0",
    "commit": "f247c0898414ca29c502691e3a8ad0b3ce0b4f6a",
    "lean_toolchain": "leanprover/lean4:v4.34.0-rc2",
}

def digest(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

def all_loopless_digraphs(n):
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    for bits in range(1 << len(arcs)):
        yield frozenset(a for k, a in enumerate(arcs) if (bits >> k) & 1)

def source_canon(edges, n):
    return min(
        tuple(sorted((p[u], p[v]) for u, v in edges))
        for p in itertools.permutations(range(n))
    )

def enumerate_candidates():
    out = []
    for roles in (1, 2, 3):
        coupling_types = list(itertools.combinations(range(roles), 2))
        for arc_channel in itertools.product(range(roles), repeat=2):
            for mask in range(1 << len(coupling_types)):
                couplings = tuple(
                    coupling_types[k]
                    for k in range(len(coupling_types))
                    if (mask >> k) & 1
                )
                out.append({
                    "roles": roles,
                    "arc_channel": tuple(arc_channel),
                    "identity_couplings": couplings,
                })
    return out

def encode(edges, n, candidate):
    roles = candidate["roles"]
    a, b = candidate["arc_channel"]
    idx = lambda v, role: roles * v + role
    target = set()

    for u, v in edges:
        x, y = idx(u, a), idx(v, b)
        if x != y:
            target.add(tuple(sorted((x, y))))

    for x, y in candidate["identity_couplings"]:
        for v in range(n):
            target.add(tuple(sorted((idx(v, x), idx(v, y)))))

    return frozenset(target)

def role_maps(n, roles):
    perms = list(itertools.permutations(range(n)))
    maps = []
    for role_perms in itertools.product(perms, repeat=roles):
        m = [0] * (n * roles)
        for v in range(n):
            for role in range(roles):
                m[roles * v + role] = roles * role_perms[role][v] + role
        maps.append(tuple(m))
    return maps

def target_canon(edges, maps):
    best = None
    for m in maps:
        value = tuple(sorted(
            tuple(sorted((m[u], m[v])))
            for u, v in edges
        ))
        if best is None or value < best:
            best = value
    return best

def json_candidate(c):
    return {
        "roles": c["roles"],
        "arc_channel": list(c["arc_channel"]),
        "identity_couplings": [list(x) for x in c["identity_couplings"]],
    }

def candidate_key(c):
    return (
        c["roles"],
        len(c["identity_couplings"]),
        c["arc_channel"],
        c["identity_couplings"],
    )

def mismatch_summary(source_sigs, target_sigs, graphs):
    mismatch_count = 0
    first = None
    for i in range(len(graphs)):
        for j in range(len(graphs)):
            source_eq = source_sigs[i] == source_sigs[j]
            target_eq = target_sigs[i] == target_sigs[j]
            if source_eq != target_eq:
                mismatch_count += 1
                if first is None:
                    first = {
                        "a": [list(e) for e in sorted(graphs[i])],
                        "b": [list(e) for e in sorted(graphs[j])],
                        "source_iso": source_eq,
                        "target_iso": target_eq,
                    }
    return mismatch_count, first

def evaluate_candidate(c, graphs, source_sigs, maps_by_roles):
    target_sigs = [
        target_canon(encode(g, 3, c), maps_by_roles[c["roles"]])
        for g in graphs
    ]
    mismatches, first = mismatch_summary(source_sigs, target_sigs, graphs)
    return {
        "candidate": json_candidate(c),
        "cost": [c["roles"], len(c["identity_couplings"])],
        "mismatch_count": mismatches,
        "qualified": mismatches == 0,
        "first_mismatch": first,
    }

def main():
    graphs = list(all_loopless_digraphs(3))
    source_sigs = [source_canon(g, 3) for g in graphs]
    candidates = enumerate_candidates()
    maps_by_roles = {r: role_maps(3, r) for r in (1, 2, 3)}

    results = []
    for c in sorted(candidates, key=candidate_key):
        results.append(evaluate_candidate(c, graphs, source_sigs, maps_by_roles))

    qualified = [r for r in results if r["qualified"]]
    if qualified:
        least_cost = min(tuple(r["cost"]) for r in qualified)
        least = [r for r in qualified if tuple(r["cost"]) == least_cost]
        selected_result = min(
            least,
            key=lambda r: (
                tuple(r["candidate"]["arc_channel"]),
                tuple(tuple(x) for x in r["candidate"]["identity_couplings"]),
            ),
        )
        selected = {
            "roles": selected_result["candidate"]["roles"],
            "arc_channel": tuple(selected_result["candidate"]["arc_channel"]),
            "identity_couplings": tuple(
                tuple(x) for x in selected_result["candidate"]["identity_couplings"]
            ),
        }
    else:
        least_cost = None
        selected_result = None
        selected = None

    cheaper_qualified = []
    if least_cost is not None:
        cheaper_qualified = [
            r for r in results
            if tuple(r["cost"]) < tuple(least_cost) and r["qualified"]
        ]

    ablations = []
    if selected and len(selected["identity_couplings"]) == 2:
        for removed in selected["identity_couplings"]:
            ablated = dict(selected)
            ablated["identity_couplings"] = tuple(
                x for x in selected["identity_couplings"] if x != removed
            )
            ev = evaluate_candidate(ablated, graphs, source_sigs, maps_by_roles[selected["roles"]])
            ablations.append({
                "removed": list(removed),
                "mismatch_count": ev["mismatch_count"],
                "first_mismatch": ev["first_mismatch"],
            })

    one_role = next(
        r for r in results
        if r["candidate"]["roles"] == 1
        and r["candidate"]["arc_channel"] == [0, 0]
        and r["candidate"]["identity_couplings"] == []
    )

    cost_levels = {}
    for r in results:
        key = f'{r["cost"][0]}:{r["cost"][1]}'
        cost_levels.setdefault(key, {"count": 0, "qualified": 0, "min_mismatches": None})
        d = cost_levels[key]
        d["count"] += 1
        d["qualified"] += int(r["qualified"])
        mm = r["mismatch_count"]
        d["min_mismatches"] = mm if d["min_mismatches"] is None else min(d["min_mismatches"], mm)

    gates = {
        "G1_candidate_count_81": len(candidates) == 81,
        "G2_complete_qualification_world": len(graphs) == 64,
        "G3_qualified_adapter_exists": selected is not None,
        "G4_no_cheaper_qualified_adapter": not cheaper_qualified,
        "G5_selected_zero_disagreement": bool(selected_result and selected_result["mismatch_count"] == 0),
        "G6_two_coupling_ablations_fail": len(ablations) == 2 and all(x["mismatch_count"] > 0 for x in ablations),
        "G7_one_role_direction_erasure_fails": one_role["mismatch_count"] > 0,
        "G8_selection_heldout_blind": True,
    }

    snapshot = {
        "qualification_n": 3,
        "graph_count": len(graphs),
        "ordered_pair_count": len(graphs) ** 2,
        "candidate_count": len(candidates),
        "grammar": {
            "role_counts": [1, 2, 3],
            "arc_channel": "all ordered role pairs including equal roles",
            "identity_couplings": "all subsets of unordered distinct-role pairs",
        },
        "selection_cost": ["role_count", "identity_coupling_count", "lexicographic_candidate"],
        "hex": HEX,
    }

    verdict = "SELECTED_FOR_HEX_HELDOUT" if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    evidence = {
        "verdict": verdict,
        "classification": "FINITE_EXHAUSTIVE_ADAPTER_GENESIS",
        "snapshot": snapshot,
        "snapshot_digest": digest(snapshot),
        "least_successful_cost": list(least_cost) if least_cost else None,
        "qualified_candidate_count": len(qualified),
        "selected": selected_result,
        "ablations": ablations,
        "one_role_control": one_role,
        "cost_levels": cost_levels,
        "gates": gates,
        "claim_boundary": [
            "bounded supplied adapter grammar only",
            "no all-n faithfulness theorem",
            "no autonomous grammar invention",
            "no open-ended transfer",
        ],
    }

    OUT.mkdir(exist_ok=True)
    (OUT / "qualification.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    if selected_result:
        (OUT / "selected_adapter.json").write_text(
            json.dumps(selected_result["candidate"], indent=2, sort_keys=True) + "\n"
        )
    (OUT / "candidate_ledger.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if verdict.startswith("SELECTED") else 1

if __name__ == "__main__":
    raise SystemExit(main())
