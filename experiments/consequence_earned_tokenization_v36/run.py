from __future__ import annotations
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent

from basis import Machine, parse_prefix_free, run_machine, token_sequences
from kernel import Kernel
from challenge_pack import (
    TRAIN, INCOMPLETE, SEMANTICS, EXPECTED_STATES,
    TRAIN_TOKENS, TEST_TOKENS, heldout_rows,
    hidden_codebook_strings, boundary_positions, make_world,
)

SCIENTIFIC_FREEZE_COMMIT = "00045bf2fc8441742d3a86946a327e490c7a89c9"

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

def machine_from_result(r: dict) -> Machine:
    d = r["machine"]
    return Machine(
        int(d["initial"]),
        tuple(int(x) for x in d["outputs"]),
        tuple(tuple(int(z) for z in t) for t in d["transitions"]),
    )

def exact_raw(rows, codebook, machine: Machine) -> bool:
    for row in rows:
        seq = parse_prefix_free(tuple(row.raw), codebook)
        if seq is None:
            return False
        if run_machine(machine, seq) != int(row.consequence):
            return False
    return True

def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    observed_blobs = {
        name: git_blob_sha(HERE / name)
        for name in freeze["scientific_core_paths"]
    }
    freeze_ok = observed_blobs == freeze["git_blob_sha"]

    kernel = Kernel()
    results = {}
    heldout_exact = {}
    recovered = {}
    structures = {}

    for world in TRAIN:
        r = kernel.synthesize(world)
        results[world.world_id] = safe(r)
        if r.get("status") != "VERIFIED":
            heldout_exact[world.world_id] = False
            recovered[world.world_id] = False
            continue
        kind = world.world_id.split("_flip")[0]
        flip = int(world.world_id.split("_flip")[1].split("_")[0])
        cb = codebook_from_result(r)
        m = machine_from_result(r)
        heldout_exact[world.world_id] = exact_raw(
            heldout_rows(kind, flip=flip, max_tokens=TEST_TOKENS), cb, m
        )
        recovered[world.world_id] = set(r["codebook"]) == hidden_codebook_strings(kind, flip)
        structures[world.world_id] = Kernel.canonical_structure(m)

    by_kind = {
        kind: results[f"{kind}_flip0_T{TRAIN_TOKENS}"]
        for kind in SEMANTICS
    }

    incomplete = kernel.synthesize(INCOMPLETE)
    nover = kernel.synthesize(make_world("relation2"), verification_enabled=False)

    variable_boundary = {}
    for kind in SEMANTICS:
        first_boundary_positions = set()
        for seq in token_sequences(2, 3):
            if len(seq) >= 2:
                first_boundary_positions.add(boundary_positions(kind, seq)[0])
        variable_boundary[kind] = len(first_boundary_positions) > 1

    kernel_text = (HERE / "kernel.py").read_text().lower()
    forbidden = (
        "constant", "last", "parity", "relation2", "relation3", "mod3",
        "motif", "absolute position", "absolute_position", "hidden_codebook",
    )

    raw_count = sum(2**n for n in range(TRAIN_TOKENS + 1))
    contraction_ratios = {
        kind: raw_count / max(1, int(by_kind[kind].get("state_count", raw_count)))
        for kind in SEMANTICS
    }

    gates = {}
    gates["T1_frozen_scientific_core_byte_identical"] = freeze_ok
    gates["T2_all_postfreeze_training_worlds_exact"] = all(
        r.get("status") == "VERIFIED" and r.get("exact_training_replay")
        for r in results.values()
    )
    gates["T3_all_learned_tokenizers_transfer_to_longer_heldout_sequences"] = all(heldout_exact.values())
    gates["T4_hidden_variable_length_codebooks_recovered"] = all(recovered.values())
    gates["T5_constant_consequence_contracts_to_one_recurrent_state"] = by_kind["constant"].get("state_count") == 1
    gates["T6_last_token_consequence_is_two_state_machine"] = by_kind["last"].get("state_count") == 2
    gates["T7_token_parity_is_two_state_persistent_machine"] = by_kind["parity"].get("state_count") == 2
    gates["T8_two_token_relation_is_three_state_machine"] = by_kind["relation2"].get("state_count") == 3
    gates["T9_three_token_relation_is_four_state_machine"] = by_kind["relation3"].get("state_count") == 4
    gates["T10_mod3_persistence_is_three_state_machine"] = by_kind["mod3"].get("state_count") == 3
    gates["T11_raw_bit_complement_worlds_transfer_exactly"] = all(
        heldout_exact.get(f"{kind}_flip1_T{TRAIN_TOKENS}", False)
        for kind in SEMANTICS
    )
    gates["T12_canonical_machine_structure_invariant_to_raw_bit_relabelling"] = all(
        structures.get(f"{kind}_flip0_T{TRAIN_TOKENS}") ==
        structures.get(f"{kind}_flip1_T{TRAIN_TOKENS}")
        for kind in SEMANTICS
    )
    gates["T13_semantic_token_boundaries_move_in_absolute_raw_offset"] = all(variable_boundary.values())
    gates["T14_no_verified_fixed_width_tokenizer_matches_primary_worlds"] = all(
        int(by_kind[kind].get("fixed_width_verified_count", 1)) == 0
        for kind in SEMANTICS
    )
    gates["T15_complete_raw_encounter_tables_contract_at_least_15x"] = min(contraction_ratios.values()) >= 15.0
    gates["T16_incomplete_authority_stays_unknown"] = incomplete.get("status") == "UNKNOWN_AUTHORITY"
    gates["T17_verifier_ablation_authorizes_no_tokenizer_or_machine"] = (
        nover.get("status") == "UNKNOWN_NO_VERIFIER" and nover.get("state_count") == 0
    )
    gates["T18_frozen_kernel_has_no_hidden_event_or_semantic_names"] = all(x not in kernel_text for x in forbidden)
    gates["T19_training_through_five_tokens_transfers_through_eight"] = (
        TRAIN_TOKENS == 5 and TEST_TOKENS == 8 and all(heldout_exact.values())
    )
    gates["T20_expected_minimum_recurrent_state_counts_recovered"] = all(
        by_kind[kind].get("state_count") == expected
        for kind, expected in EXPECTED_STATES.items()
    )

    evidence = {
        "experiment": "consequence_earned_tokenization_v36",
        "scientific_freeze_commit": SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest": freeze,
        "observed_core_git_blob_sha": observed_blobs,
        "training_token_depth": TRAIN_TOKENS,
        "heldout_token_depth": TEST_TOKENS,
        "results": results,
        "heldout_exact": heldout_exact,
        "hidden_codebook_recovered": recovered,
        "variable_boundary_evidence": variable_boundary,
        "contraction_ratios": contraction_ratios,
        "gates": gates,
    }
    evidence["full_pass"] = all(gates.values())
    evidence["verdict"] = (
        "VERIFIED_CONSEQUENCE_EARNED_VARIABLE_LENGTH_EVENT_TOKENIZATION"
        if evidence["full_pass"] else
        "CONSEQUENCE_EARNED_TOKENIZATION_V36_GAPS_EXPOSED"
    )
    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
