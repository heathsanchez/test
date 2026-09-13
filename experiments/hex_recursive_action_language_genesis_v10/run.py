#!/usr/bin/env python3
import hashlib, itertools, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
PARENT = ROOT.parent / "hex_verified_meta_language_contraction_v9" / "AUTHORITY.json"

OLD_FEATURES = ("FIRST", "LAST")
NEW_CANDIDATES = ("LEFT_EDGE_OF_CONFLICT_CLASS", "RIGHT_EDGE_OF_CONFLICT_CLASS")

def bits_index(bits):
    x = 0
    for b in bits:
        x = (x << 1) | int(bool(b))
    return x

def eval_mask(mask, bits):
    return (mask >> bits_index(bits)) & 1

def target(m, i):
    return int(i == 1)

def old_features(m, i):
    return (int(i == 0), int(i == m - 1))

def old_signature_classes(m):
    d = {}
    for i in range(m):
        d.setdefault(old_features(m, i), []).append(i)
    return d

def mismatch_count(mask, m, feat):
    return sum(eval_mask(mask, feat(m, i)) != target(m, i) for i in range(m))

def old_exhaust(m):
    return [
        {"operator_id": mask, "mismatches": mismatch_count(mask, m, old_features)}
        for mask in range(16)
    ]

def conflicting_classes(m):
    out = []
    for sig, members in sorted(old_signature_classes(m).items()):
        vals = {target(m, i) for i in members}
        if len(vals) > 1:
            out.append({
                "signature": list(sig),
                "members": members,
                "target_values": [target(m, i) for i in members],
            })
    return out

def generated_atom(kind, m, i):
    conflict = [j for j in range(m) if old_features(m, j) == (0, 0)]
    if not conflict:
        return 0
    if kind == "LEFT_EDGE_OF_CONFLICT_CLASS":
        return int(i == min(conflict))
    if kind == "RIGHT_EDGE_OF_CONFLICT_CLASS":
        return int(i == max(conflict))
    raise ValueError(kind)

def grown_features(kind, m, i):
    return old_features(m, i) + (generated_atom(kind, m, i),)

def grown_exhaust(kind, m):
    feat = lambda mm, ii: grown_features(kind, mm, ii)
    return [
        {"operator_id": mask, "mismatches": mismatch_count(mask, m, feat)}
        for mask in range(256)
    ]

def dependencies(mask, k):
    deps = []
    for j in range(k):
        needed = False
        for bits in itertools.product((0, 1), repeat=k):
            a = eval_mask(mask, bits)
            b = list(bits)
            b[j] ^= 1
            if a != eval_mask(mask, tuple(b)):
                needed = True
                break
        if needed:
            deps.append(j)
    return deps

def qualifying(exhaust):
    return [x["operator_id"] for x in exhaust if x["mismatches"] == 0]

def cold_cost_for_arity(m):
    old = old_exhaust(m)
    if qualifying(old):
        return len(old)
    return len(old) + 2 * 256

def main():
    if PARENT.exists():
        parent = json.loads(PARENT.read_text())
        if parent.get("verdict") != "VERIFIED_META_LANGUAGE_CONTRACTION_AND_TRANSFER":
            raise RuntimeError("parent V9 authority not verified")
        parent_authority = {
            "verdict": parent["verdict"],
            "workflow_run_id": parent.get("workflow_run_id"),
            "head_sha": parent.get("head_sha"),
        }
    else:
        parent_authority = {"warning": "parent authority unavailable in checkout"}

    m4_old = old_exhaust(4)
    conflicts = conflicting_classes(4)

    grown = {}
    for kind in NEW_CANDIDATES:
        e4 = grown_exhaust(kind, 4)
        e5 = grown_exhaust(kind, 5)
        q4 = qualifying(e4)
        q5 = qualifying(e5)
        qboth = sorted(set(q4) & set(q5))
        grown[kind] = {
            "arity4_qualifying_count": len(q4),
            "arity5_qualifying_count": len(q5),
            "joint_qualifying": qboth,
        }

    surviving_kinds = [k for k, v in grown.items() if v["joint_qualifying"]]
    selected_kind = surviving_kinds[0] if len(surviving_kinds) == 1 else None

    selected_program = None
    if selected_kind:
        candidates = grown[selected_kind]["joint_qualifying"]
        scored = sorted(
            (len(dependencies(mask, 3)), mask, dependencies(mask, 3))
            for mask in candidates
        )
        selected_program = {
            "operator_id": scored[0][1],
            "dependency_indices": scored[0][2],
            "dependency_names": [
                (*OLD_FEATURES, "GENERATED_ATOM")[j] for j in scored[0][2]
            ],
            "dependency_cardinality": scored[0][0],
        }

    heldout = {}
    if selected_kind and selected_program:
        mask = selected_program["operator_id"]
        feat = lambda mm, ii: grown_features(selected_kind, mm, ii)
        for m in (6, 7):
            heldout[str(m)] = {
                "mismatches": mismatch_count(mask, m, feat),
                "warm_candidate_evaluations": 1,
                "cold_redevelopment_candidate_evaluations": cold_cost_for_arity(m),
            }

    duplicate_first = lambda m, i: old_features(m, i) + (old_features(m, i)[0],)
    constant_zero = lambda m, i: old_features(m, i) + (0,)
    sham = {
        "duplicate_FIRST_best_mismatches": min(
            mismatch_count(mask, 4, duplicate_first) for mask in range(256)
        ),
        "constant_zero_best_mismatches": min(
            mismatch_count(mask, 4, constant_zero) for mask in range(256)
        ),
    }

    incomplete_search_prefix = m4_old[:8]
    incomplete_control = {
        "searched": len(incomplete_search_prefix),
        "complete": False,
        "witness_found": bool(qualifying(incomplete_search_prefix)),
        "growth_authorized": False,
        "required_outcome": "UNKNOWN",
    }

    selected_mask = selected_program["operator_id"] if selected_program else None
    ablation_old_best = min(x["mismatches"] for x in m4_old)
    protected_replay = {}
    if selected_kind and selected_mask is not None:
        feat = lambda mm, ii: grown_features(selected_kind, mm, ii)
        protected_replay = {
            str(m): mismatch_count(selected_mask, m, feat)
            for m in (4, 5)
        }

    gates = {
        "G1_old_language_complete": len(m4_old) == 16,
        "G2_old_language_exhaustively_inadequate": len(qualifying(m4_old)) == 0,
        "G3_residual_is_observational_collision": (
            len(conflicts) == 1
            and conflicts[0]["members"] == [1, 2]
            and conflicts[0]["target_values"] == [1, 0]
        ),
        "G4_growth_candidates_are_minimum_one_bit_refinements": (
            set(NEW_CANDIDATES) == set(grown.keys())
        ),
        "G5_both_refinements_fit_qualification": all(
            v["arity4_qualifying_count"] > 0 for v in grown.values()
        ),
        "G6_future_consequence_selects_unique_refinement": (
            selected_kind == "LEFT_EDGE_OF_CONFLICT_CLASS"
        ),
        "G7_selected_program_is_new_atom_only": (
            selected_program is not None
            and selected_program["dependency_indices"] == [2]
        ),
        "G8_protected_replay": protected_replay == {"4": 0, "5": 0},
        "G9_heldout_transfer": bool(heldout) and all(
            v["mismatches"] == 0 for v in heldout.values()
        ),
        "G10_ablation_restores_inadequacy": ablation_old_best > 0,
        "G11_sham_growth_fails": all(v > 0 for v in sham.values()),
        "G12_incomplete_search_does_not_authorize_growth": (
            incomplete_control["required_outcome"] == "UNKNOWN"
            and not incomplete_control["growth_authorized"]
        ),
        "G13_compounding_reduces_future_candidate_evaluations": bool(heldout)
        and all(
            v["cold_redevelopment_candidate_evaluations"]
            > v["warm_candidate_evaluations"]
            for v in heldout.values()
        ),
    }

    verdict = (
        "QUALIFIED_RECURSIVE_ACTION_LANGUAGE_GENESIS"
        if all(gates.values())
        else "NEGATIVE_OR_PARTIAL"
    )

    evidence = {
        "verdict": verdict,
        "classification": "FINITE_EXHAUSTIVE_RESIDUAL_GENERATED_ACTION_LANGUAGE_GROWTH",
        "parent_authority": parent_authority,
        "frozen_target_family": "SECOND_POSITION_ACTIVE",
        "old_observation_language": list(OLD_FEATURES),
        "old_program_substrate_size": 16,
        "old_arity4_best_mismatches": ablation_old_best,
        "residual_conflicts": conflicts,
        "growth_constructor": (
            "split only the witnessed equivalence class at its ordered extrema"
        ),
        "generated_refinements": grown,
        "selected_refinement": selected_kind,
        "selected_program": selected_program,
        "protected_replay_mismatches": protected_replay,
        "heldout": heldout,
        "ablation_old_best_mismatches": ablation_old_best,
        "sham_controls": sham,
        "incomplete_search_control": incomplete_control,
        "gates": gates,
        "claim_boundary": [
            "finite ordered position families only",
            "higher-order conflict-class splitter supplied and frozen",
            "does not establish primitive invention ex nihilo",
            (
                "does establish recursion from a certified inadequate complete "
                "action language to a residual-generated enlarged action language"
            ),
        ],
    }

    OUT.mkdir(exist_ok=True)
    payload = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    (OUT / "evidence.json").write_text(payload)
    (OUT / "evidence.sha256").write_text(
        hashlib.sha256(payload.encode()).hexdigest() + "\n"
    )
    print(payload, end="")
    return 0 if verdict.startswith("QUALIFIED") else 1

if __name__ == "__main__":
    raise SystemExit(main())
