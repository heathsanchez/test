from __future__ import annotations
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent

from basis import PartialMachine, parse_prefix_free, run_partial
from kernel import Kernel
from challenge_pack import (
    WORLDS, INCOMPLETE, EXPECTED, heldout_rows,
    hidden_codebook_strings, make_world,
)

SCIENTIFIC_FREEZE_COMMIT = "8d7325a3eacf348510e220477fbd11ae57fa3511"

def git_blob_sha(p: Path) -> str:
    data = p.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def safe(x):
    if isinstance(x, dict):
        return {str(k): safe(v) for k, v in x.items() if not str(k).startswith("_")}
    if isinstance(x, (list, tuple)):
        return [safe(v) for v in x]
    return x

def codebook_from_result(r: dict) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(ch) for ch in word) for word in r["codebook"])

def machine_from_result(r: dict) -> PartialMachine:
    d = r["machine"]
    return PartialMachine(
        int(d["initial"]),
        tuple(int(x) for x in d["outputs"]),
        tuple(
            tuple(None if z is None else int(z) for z in row)
            for row in d["transitions"]
        ),
        tuple(tuple(int(x) for x in sig) for sig in d["signatures"]),
    )

def exact_heldout(rows, codebook, machine: PartialMachine) -> bool:
    for row in rows:
        seq = parse_prefix_free(tuple(row.raw), codebook)
        if seq is None:
            return False
        y = run_partial(machine, seq)
        if y is None or int(y) != int(row.consequence):
            return False
    return True

def signature_set(r: dict) -> set[tuple[int, ...]]:
    return {tuple(int(x) for x in sig) for sig in r["signature_set"]}

def result(results: dict, kind: str, flip: int, depth: int) -> dict:
    return results[f"{kind}_flip{flip}_D{depth}"]

def provisional_frontier_is_positive_terminal(r: dict) -> bool:
    if r.get("provisional_state_count") != 1:
        return False
    m = machine_from_result(r)
    q = int(r["provisional_state_ids"][0])
    return (
        int(m.outputs[q]) == 1 and
        all(z is None for z in m.transitions[q])
    )

def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    observed = {
        name: git_blob_sha(HERE / name)
        for name in freeze["scientific_core_paths"]
    }
    freeze_ok = observed == freeze["git_blob_sha"]

    kernel = Kernel()
    results = {}
    structures = {}

    for world in WORLDS:
        r = kernel.synthesize(world)
        results[world.world_id] = safe(r)
        if r.get("status") in ("VERIFIED_PROVISIONAL", "VERIFIED_STABLE"):
            structures[world.world_id] = Kernel.canonical_structure(
                machine_from_result(r)
            )

    p3_shallow = {f: result(results, "p3", f, 5) for f in (0,1)}
    p3_deep = {f: result(results, "p3", f, 6) for f in (0,1)}
    p4_shallow = {f: result(results, "p4", f, 7) for f in (0,1)}
    p4_deep = {f: result(results, "p4", f, 8) for f in (0,1)}
    p2 = {f: result(results, "p2", f, 4) for f in (0,1)}
    cycle = {f: result(results, "cycle", f, 3) for f in (0,1)}

    p3_transfer = {}
    p4_transfer = {}
    for f in (0,1):
        r3 = p3_deep[f]
        r4 = p4_deep[f]
        p3_transfer[f] = (
            r3.get("status") == "VERIFIED_STABLE" and
            exact_heldout(
                heldout_rows("p3", 9, flip=f),
                codebook_from_result(r3),
                machine_from_result(r3),
            )
        )
        p4_transfer[f] = (
            r4.get("status") == "VERIFIED_STABLE" and
            exact_heldout(
                heldout_rows("p4", 10, flip=f),
                codebook_from_result(r4),
                machine_from_result(r4),
            )
        )

    all_named = [
        ("p2",4), ("p3",5), ("p3",6),
        ("p4",7), ("p4",8), ("cycle",3),
    ]

    codebook_recovery = {}
    for kind, depth in all_named:
        for f in (0,1):
            r = result(results, kind, f, depth)
            codebook_recovery[f"{kind}_{depth}_{f}"] = (
                r.get("status") in ("VERIFIED_PROVISIONAL","VERIFIED_STABLE") and
                set(r.get("codebook", [])) == hidden_codebook_strings(kind, f)
            )

    complement_invariance = {}
    for kind, depth in all_named:
        a = result(results, kind, 0, depth)
        b = result(results, kind, 1, depth)
        complement_invariance[f"{kind}_{depth}"] = (
            a.get("status") == b.get("status") and
            a.get("state_count") == b.get("state_count") and
            a.get("provisional_state_count") == b.get("provisional_state_count") and
            a.get("distinguishing_horizon") == b.get("distinguishing_horizon") and
            structures.get(f"{kind}_flip0_D{depth}") ==
            structures.get(f"{kind}_flip1_D{depth}")
        )

    incomplete = kernel.synthesize(INCOMPLETE)
    nover = kernel.synthesize(make_world("p3", 5), verification_enabled=False)

    kernel_text = (HERE / "kernel.py").read_text().lower()
    forbidden = (
        "p2", "p3", "p4", "cycle",
        "101", "1011", "pattern", "parity",
        "depth 5", "depth 6", "depth 7", "depth 8",
    )

    gates = {}
    gates["G1_frozen_scientific_core_byte_identical"] = freeze_ok
    gates["G2_three_token_shallow_is_verified_provisional"] = all(
        p3_shallow[f].get("status") == "VERIFIED_PROVISIONAL"
        for f in (0,1)
    )
    gates["G3_three_token_shallow_already_has_four_residual_states"] = all(
        p3_shallow[f].get("state_count") == 4
        for f in (0,1)
    )
    gates["G4_exactly_frontier_born_state_lacks_recurrence"] = all(
        provisional_frontier_is_positive_terminal(p3_shallow[f])
        for f in (0,1)
    )
    gates["G5_one_more_authority_depth_stabilizes_same_three_token_family"] = all(
        p3_deep[f].get("status") == "VERIFIED_STABLE" and
        p3_deep[f].get("state_count") == 4 and
        p3_deep[f].get("provisional_state_count") == 0
        for f in (0,1)
    )
    gates["G6_three_token_residual_signature_set_preserved_across_stabilization"] = all(
        signature_set(p3_shallow[f]) == signature_set(p3_deep[f])
        for f in (0,1)
    )
    gates["G7_stabilized_three_token_machine_transfers_to_depth9"] = all(p3_transfer.values())
    gates["G8_hidden_tokenizer_is_unchanged_and_recovered_across_stages"] = all(codebook_recovery.values())
    gates["G9_four_token_family_repeats_provisional_then_stable_sequence"] = all(
        p4_shallow[f].get("status") == "VERIFIED_PROVISIONAL" and
        p4_deep[f].get("status") == "VERIFIED_STABLE"
        for f in (0,1)
    )
    gates["G10_four_token_shallow_already_has_five_residual_states"] = all(
        p4_shallow[f].get("state_count") == 5 and
        p4_shallow[f].get("provisional_state_count") == 1
        for f in (0,1)
    )
    gates["G11_stabilized_four_token_machine_transfers_to_depth10"] = all(p4_transfer.values())
    gates["G12_parity_control_is_already_stable"] = all(
        cycle[f].get("status") == "VERIFIED_STABLE" and
        cycle[f].get("state_count") == 2
        for f in (0,1)
    )
    gates["G13_shorter_two_token_relation_stabilizes_earlier"] = all(
        p2[f].get("status") == "VERIFIED_STABLE" and
        p2[f].get("state_count") == 3
        for f in (0,1)
    )
    gates["G14_provisional_results_are_not_reported_executable"] = all(
        not p3_shallow[f].get("stable_executable", True) and
        not p4_shallow[f].get("stable_executable", True) and
        p3_deep[f].get("stable_executable") is True and
        p4_deep[f].get("stable_executable") is True
        for f in (0,1)
    )
    gates["G15_raw_bit_complement_preserves_status_and_structure"] = all(complement_invariance.values())
    gates["G16_incomplete_authority_stays_unknown"] = incomplete.get("status") == "UNKNOWN_AUTHORITY"
    gates["G17_verifier_ablation_authorizes_no_residual_construction"] = (
        nover.get("status") == "UNKNOWN_NO_VERIFIER" and
        nover.get("state_count") == 0
    )
    gates["G18_frozen_kernel_has_no_hidden_family_or_depth_names"] = all(
        token not in kernel_text for token in forbidden
    )
    gates["G19_minimum_distinguishing_horizons_scale_with_relational_depth"] = all(
        cycle[f].get("distinguishing_horizon") == EXPECTED["cycle"]["horizon"] and
        p2[f].get("distinguishing_horizon") == EXPECTED["p2"]["horizon"] and
        p3_shallow[f].get("distinguishing_horizon") == EXPECTED["p3"]["horizon"] and
        p3_deep[f].get("distinguishing_horizon") == EXPECTED["p3"]["horizon"] and
        p4_shallow[f].get("distinguishing_horizon") == EXPECTED["p4"]["horizon"] and
        p4_deep[f].get("distinguishing_horizon") == EXPECTED["p4"]["horizon"]
        for f in (0,1)
    )
    gates["G20_birth_and_stabilization_thresholds_are_distinct_in_two_families"] = (
        all(p3_shallow[f].get("status") == "VERIFIED_PROVISIONAL" and
            p3_deep[f].get("status") == "VERIFIED_STABLE" for f in (0,1))
        and
        all(p4_shallow[f].get("status") == "VERIFIED_PROVISIONAL" and
            p4_deep[f].get("status") == "VERIFIED_STABLE" for f in (0,1))
    )

    evidence = {
        "experiment": "provisional_state_stabilization_v37",
        "scientific_freeze_commit": SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest": freeze,
        "observed_core_git_blob_sha": observed,
        "results": results,
        "codebook_recovery": codebook_recovery,
        "complement_invariance": complement_invariance,
        "three_token_transfer_to_depth9": p3_transfer,
        "four_token_transfer_to_depth10": p4_transfer,
        "gates": gates,
    }
    evidence["full_pass"] = all(gates.values())
    evidence["verdict"] = (
        "VERIFIED_PROVISIONAL_STATE_GENESIS_AND_CONSEQUENCE_EARNED_STABILIZATION"
        if evidence["full_pass"] else
        "PROVISIONAL_STATE_STABILIZATION_V37_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
