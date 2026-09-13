#!/usr/bin/env python3
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"

V2_AUTHORITY = {
    "verdict": "VERIFIED_BOUNDED_ADAPTER_GENESIS",
    "workflow_run_id": 34727765985,
    "head_sha": "8e897d6571bf53a35980d8ff635a68652bf81173",
    "artifact_id": 10309130239,
    "artifact_zip_sha256": "a384b953d8cf3236255cd104679a3079430ab8d8ce2bbd60a6e2fcc996f24891",
    "selected_adapter": {
        "roles": 3,
        "arc_channel": [0, 1],
        "identity_couplings": [[0, 2], [1, 2]],
    },
    "hex_kernel_check": "PASS",
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

def encode(edges, n, roles, arc_channel, identity_couplings):
    a, b = arc_channel
    idx = lambda v, role: roles * v + role
    target = set()
    for u, v in edges:
        x, y = idx(u, a), idx(v, b)
        if x != y:
            target.add(tuple(sorted((x, y))))
    for x, y in identity_couplings:
        for v in range(n):
            target.add(tuple(sorted((idx(v, x), idx(v, y)))))
    return frozenset(target)

def role_maps(n, roles):
    perms = list(itertools.permutations(range(n)))
    out = []
    for role_perms in itertools.product(perms, repeat=roles):
        m = [0] * (n * roles)
        for v in range(n):
            for role in range(roles):
                m[roles * v + role] = roles * role_perms[role][v] + role
        out.append((tuple(role_perms), tuple(m)))
    return out

def target_canon(edges, maps):
    best = None
    for _, m in maps:
        value = tuple(sorted(
            tuple(sorted((m[u], m[v])))
            for u, v in edges
        ))
        if best is None or value < best:
            best = value
    return best

def target_witness(a, b, maps):
    for role_perms, m in maps:
        mapped = frozenset(
            tuple(sorted((m[u], m[v])))
            for u, v in a
        )
        if mapped == b:
            return [list(p) for p in role_perms]
    return None

def eval_candidate(graphs, source_sigs, maps, roles, arc, couplings):
    encoded = [encode(g, 3, roles, arc, couplings) for g in graphs]
    target_sigs = [target_canon(e, maps[roles]) for e in encoded]
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
                        "i": i,
                        "j": j,
                        "a": [list(e) for e in sorted(graphs[i])],
                        "b": [list(e) for e in sorted(graphs[j])],
                        "source_iso": source_eq,
                        "target_iso": target_eq,
                    }
    if first and first["target_iso"]:
        first["target_witness_role_permutations"] = target_witness(
            encoded[first["i"]], encoded[first["j"]], maps[roles]
        )
    if first:
        first.pop("i", None)
        first.pop("j", None)
    return {
        "roles": roles,
        "arc_channel": list(arc),
        "identity_couplings": [list(x) for x in couplings],
        "mismatch_count": mismatch_count,
        "qualified": mismatch_count == 0,
        "first_mismatch": first,
    }

def enumerate_initial():
    candidates = []
    for roles in (1, 2):
        coupling_types = list(itertools.combinations(range(roles), 2))
        for arc in itertools.product(range(roles), repeat=2):
            for mask in range(1 << len(coupling_types)):
                couplings = tuple(
                    coupling_types[k]
                    for k in range(len(coupling_types))
                    if (mask >> k) & 1
                )
                candidates.append((roles, tuple(arc), couplings))
    return candidates

def main():
    graphs = list(all_loopless_digraphs(3))
    source_sigs = [source_canon(g, 3) for g in graphs]
    maps = {r: role_maps(3, r) for r in (1, 2, 3)}

    initial = []
    for roles, arc, couplings in enumerate_initial():
        initial.append(eval_candidate(
            graphs, source_sigs, maps, roles, arc, couplings
        ))

    initial_qualified = [x for x in initial if x["qualified"]]
    two_role = [x for x in initial if x["roles"] == 2]
    best_two_role = min(x["mismatch_count"] for x in two_role)

    diagnostic = eval_candidate(
        graphs, source_sigs, maps,
        2, (0, 1), ((0, 1),)
    )
    witness = (
        diagnostic["first_mismatch"] or {}
    ).get("target_witness_role_permutations")
    desynchronized = bool(
        witness and len(witness) == 2 and witness[0] != witness[1]
    )
    residual_class = (
        "ROLE_PERMUTATION_DESYNCHRONIZATION"
        if desynchronized
        else "UNRESOLVED_TWO_ROLE_FAILURE"
    )

    repairs = {
        "ADD_INERT_ROLE": (),
        "ADD_PARTIAL_IDENTITY_CHANNEL_0": ((0, 2),),
        "ADD_PARTIAL_IDENTITY_CHANNEL_1": ((1, 2),),
        "ADD_FULL_IDENTITY_CHANNEL": ((0, 2), (1, 2)),
    }

    repair_results = {}
    for name, couplings in repairs.items():
        repair_results[name] = eval_candidate(
            graphs, source_sigs, maps,
            3, (0, 1), couplings
        )

    full = repair_results["ADD_FULL_IDENTITY_CHANNEL"]
    ablations = []
    for removed in ((0, 2), (1, 2)):
        remaining = tuple(
            x for x in ((0, 2), (1, 2)) if x != removed
        )
        ev = eval_candidate(
            graphs, source_sigs, maps,
            3, (0, 1), remaining
        )
        ablations.append({
            "removed": list(removed),
            "mismatch_count": ev["mismatch_count"],
            "first_mismatch": ev["first_mismatch"],
        })

    selected = {
        "roles": full["roles"],
        "arc_channel": full["arc_channel"],
        "identity_couplings": full["identity_couplings"],
    }
    matches_v2 = selected == V2_AUTHORITY["selected_adapter"]

    gates = {
        "G1_complete_world": len(graphs) == 64,
        "G2_initial_substrate_complete": len(initial) == 9,
        "G3_initial_substrate_inadequate": len(initial_qualified) == 0,
        "G4_two_role_residual_nonzero": best_two_role > 0,
        "G5_residual_desynchronization": residual_class == "ROLE_PERMUTATION_DESYNCHRONIZATION",
        "G6_inert_and_partial_repairs_fail": (
            repair_results["ADD_INERT_ROLE"]["mismatch_count"] > 0
            and repair_results["ADD_PARTIAL_IDENTITY_CHANNEL_0"]["mismatch_count"] > 0
            and repair_results["ADD_PARTIAL_IDENTITY_CHANNEL_1"]["mismatch_count"] > 0
        ),
        "G7_full_identity_channel_repairs": full["mismatch_count"] == 0,
        "G8_ablation_restores_failure": (
            len(ablations) == 2
            and all(x["mismatch_count"] > 0 for x in ablations)
        ),
        "G9_matches_independently_hex_checked_v2_adapter": matches_v2,
    }

    snapshot = {
        "qualification_n": 3,
        "graph_count": len(graphs),
        "ordered_pair_count": len(graphs) ** 2,
        "initial_substrate": "all adapters with role_count <= 2",
        "growth_constructors": list(repairs),
        "arc_channel_during_growth": [0, 1],
        "prior_v2_authority": V2_AUTHORITY,
    }

    verdict = (
        "VERIFIED_RESIDUAL_GUIDED_SUBSTRATE_GROWTH"
        if all(gates.values()) else
        "NEGATIVE_OR_PARTIAL"
    )

    evidence = {
        "verdict": verdict,
        "classification": "FINITE_EXHAUSTIVE_CAUSAL_SUBSTRATE_GROWTH",
        "snapshot": snapshot,
        "snapshot_digest": digest(snapshot),
        "initial_candidate_count": len(initial),
        "initial_best_mismatch_count": min(x["mismatch_count"] for x in initial),
        "best_two_role_mismatch_count": best_two_role,
        "diagnostic_candidate": diagnostic,
        "residual_classification": residual_class,
        "repair_results": repair_results,
        "ablations": ablations,
        "selected_growth_result": selected,
        "matches_v2_adapter": matches_v2,
        "gates": gates,
        "claim_boundary": [
            "growth constructor set supplied in advance",
            "finite qualification world only",
            "no autonomous constructor invention",
            "no open-ended grammar growth",
        ],
    }

    OUT.mkdir(exist_ok=True)
    (OUT / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    )
    (OUT / "initial_ledger.json").write_text(
        json.dumps(initial, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if verdict.startswith("VERIFIED") else 1

if __name__ == "__main__":
    raise SystemExit(main())
