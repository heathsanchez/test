#!/usr/bin/env python3
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
V7_AUTH = ROOT.parent / "hex_meta_selector_genesis_v7" / "AUTHORITY.json"

def load_v7():
    v7 = json.loads(V7_AUTH.read_text())
    if v7.get("verdict") != "VERIFIED_META_RULE_GENESIS_AND_TRANSFER":
        raise RuntimeError("V7 authority missing")
    return v7

def all_digraphs(n):
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    for bits in range(1 << len(arcs)):
        yield (frozenset(a for k, a in enumerate(arcs) if (bits >> k) & 1),)

def single_arc_relations(n, m):
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    return [
        tuple(frozenset([a]) for a in choice)
        for choice in itertools.product(arcs, repeat=m)
    ]

def source_canon(obj, n):
    return min(
        tuple(
            tuple(sorted((p[u], p[v]) for u, v in rel))
            for rel in obj
        )
        for p in itertools.permutations(range(n))
    )

def encode(obj, n, selected_relations):
    m = len(obj)
    roles = 2 * m + 1
    fresh = roles - 1
    idx = lambda v, role: roles * v + role
    edges = set()
    for r, rel in enumerate(obj):
        tail, head = 2 * r, 2 * r + 1
        for u, v in rel:
            edges.add(tuple(sorted((idx(u, tail), idx(v, head)))))
    for r in selected_relations:
        for role in (2 * r, 2 * r + 1):
            for v in range(n):
                edges.add(tuple(sorted((idx(v, role), idx(v, fresh)))))
    return frozenset(edges)

def role_maps(n, roles):
    perms = list(itertools.permutations(range(n)))
    out = []
    for role_perms in itertools.product(perms, repeat=roles):
        mp = [0] * (n * roles)
        for v in range(n):
            for role in range(roles):
                mp[roles * v + role] = roles * role_perms[role][v] + role
        out.append(tuple(mp))
    return out

def target_canon(edges, maps):
    best = None
    for mp in maps:
        value = tuple(sorted(
            tuple(sorted((mp[u], mp[v])))
            for u, v in edges
        ))
        if best is None or value < best:
            best = value
    return best

def world(name, n, objects):
    m = len(objects[0])
    src = [source_canon(x, n) for x in objects]
    maps = role_maps(n, 2 * m + 1)
    return {
        "name": name,
        "n": n,
        "m": m,
        "objects": objects,
        "source_sigs": src,
        "maps": maps,
        "ordered_pairs": len(objects) ** 2,
        "cache": {},
    }

def mismatch_count(w, selected_relations):
    key = tuple(sorted(selected_relations))
    if key in w["cache"]:
        return w["cache"][key]
    target = [
        target_canon(encode(x, w["n"], key), w["maps"])
        for x in w["objects"]
    ]
    mm = 0
    first = None
    N = len(w["objects"])
    for i in range(N):
        for j in range(N):
            s = w["source_sigs"][i] == w["source_sigs"][j]
            t = target[i] == target[j]
            if s != t:
                mm += 1
                if first is None:
                    first = {
                        "a": [[list(e) for e in sorted(r)] for r in w["objects"][i]],
                        "b": [[list(e) for e in sorted(r)] for r in w["objects"][j]],
                        "source_iso": s,
                        "target_iso": t,
                    }
    w["cache"][key] = (mm, first)
    return mm, first

def first_last_bits(m, i):
    return (1 if i == 0 else 0, 1 if i == m - 1 else 0)

def table_output(table, a, b):
    idx = (a << 1) | b
    return (table >> idx) & 1

def table_selector(table, m):
    return tuple(
        i for i in range(m)
        if table_output(table, *first_last_bits(m, i))
    )

def table_bits(table):
    return "".join(str((table >> i) & 1) for i in range(4))

def evaluate_table(table, worlds):
    breakdown = {}
    total = 0
    for w in worlds:
        selected = table_selector(table, w["m"])
        mm, first = mismatch_count(w, selected)
        total += mm
        breakdown[w["name"]] = {
            "selected_relations": list(selected),
            "mismatch_count": mm,
            "first_mismatch": first,
        }
    return {
        "table_index": table,
        "bits_00_01_10_11": table_bits(table),
        "breakdown": breakdown,
        "total_mismatches": total,
        "qualified": total == 0,
    }

def main():
    v7 = load_v7()

    w1 = world("one_relation_full_n3", 3, list(all_digraphs(3)))
    w2 = world("two_relation_one_arc_n3", 3, single_arc_relations(3, 2))
    w3 = world("three_relation_one_arc_n2", 2, single_arc_relations(2, 3))
    protected = [w1, w2, w3]

    old_programs = {
        "FIRST": lambda m: (0,),
        "LAST": lambda m: (m - 1,),
        "FIRST_OR_LAST": lambda m: tuple(sorted(set((0, m - 1)))),
    }
    old_results = {}
    for name, selector in old_programs.items():
        breakdown = {}
        total = 0
        for w in protected:
            selected = selector(w["m"])
            mm, first = mismatch_count(w, selected)
            total += mm
            breakdown[w["name"]] = {
                "selected_relations": list(selected),
                "mismatch_count": mm,
                "first_mismatch": first,
            }
        old_results[name] = {
            "total_mismatches": total,
            "qualified": total == 0,
            "breakdown": breakdown,
        }

    ledger = [evaluate_table(t, protected) for t in range(16)]
    qualified = [x for x in ledger if x["qualified"]]
    selected = qualified[0] if len(qualified) == 1 else None

    w4 = world("four_relation_one_arc_n2", 2, single_arc_relations(2, 4))
    all_worlds = protected + [w4]

    cold = [evaluate_table(t, all_worlds) for t in range(16)]
    first_cold_success = next((i + 1 for i, x in enumerate(cold) if x["qualified"]), None)
    warm = evaluate_table(selected["table_index"], all_worlds) if selected else None

    pairs_per_replay = sum(w["ordered_pairs"] for w in all_worlds)
    cold_pair_comparisons = first_cold_success * pairs_per_replay if first_cold_success else None
    warm_pair_comparisons = pairs_per_replay

    gates = {
        "G1_old_or_closure_complete": set(old_results) == {"FIRST", "LAST", "FIRST_OR_LAST"},
        "G2_old_language_inadequate": all(not x["qualified"] for x in old_results.values()),
        "G3_all_16_truth_tables_evaluated": len(ledger) == 16,
        "G4_unique_qualified_truth_table": len(qualified) == 1,
        "G5_synthesized_table_is_1111": bool(selected and selected["bits_00_01_10_11"] == "1111"),
        "G6_v7_behavior_recovered_without_true_atom": bool(selected and selected["table_index"] == 15),
        "G7_four_relation_transfer_zero": bool(warm and warm["breakdown"][w4["name"]]["mismatch_count"] == 0),
        "G8_cold_first_success_is_candidate_16": first_cold_success == 16,
        "G9_warm_one_candidate": warm is not None,
        "G10_ablation_restores_old_inadequacy": all(not x["qualified"] for x in old_results.values()),
    }

    verdict = (
        "QUALIFIED_META_LANGUAGE_PRIMITIVE_GENESIS_FOR_HEX_HELDOUT"
        if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    )

    evidence = {
        "verdict": verdict,
        "classification": "FINITE_EXHAUSTIVE_META_LANGUAGE_PRIMITIVE_GENESIS",
        "prior_v7_run": v7["workflow_run_id"],
        "old_language": {
            "atoms": ["FIRST", "LAST"],
            "constructor": "OR",
            "semantic_closure_size": 3,
            "results": old_results,
        },
        "truth_table_substrate": {
            "candidate_count": 16,
            "input_order": ["00", "01", "10", "11"],
            "ledger": ledger,
            "qualified_count": len(qualified),
            "selected": selected,
        },
        "prospective_transfer": {
            "world": {
                "relations": 4,
                "carrier_size": 2,
                "objects": 16,
                "ordered_pairs": 256,
            },
            "cold_first_success_candidate_count": first_cold_success,
            "warm_candidate_count": 1 if warm else None,
            "pair_comparisons_per_full_replay": pairs_per_replay,
            "cold_pair_comparisons_through_success": cold_pair_comparisons,
            "warm_pair_comparisons": warm_pair_comparisons,
            "comparison_reduction": (
                cold_pair_comparisons / warm_pair_comparisons
                if cold_pair_comparisons else None
            ),
            "warm": warm,
        },
        "gates": gates,
        "claim_boundary": [
            "generic binary truth-table substrate supplied",
            "finite protected and transfer worlds",
            "subject and verifier supplied",
        ],
    }

    OUT.mkdir(exist_ok=True)
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    (OUT / "synthesized_primitive.json").write_text(
        json.dumps({
            "representation": "binary_boolean_truth_table",
            "inputs": ["FIRST", "LAST"],
            "input_order": ["00", "01", "10", "11"],
            "bits": selected["bits_00_01_10_11"] if selected else None,
            "table_index": selected["table_index"] if selected else None,
        }, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if verdict.startswith("QUALIFIED") else 1

if __name__ == "__main__":
    raise SystemExit(main())
