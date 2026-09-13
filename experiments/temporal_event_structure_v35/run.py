from __future__ import annotations
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
from basis import Machine, run_machine
from kernel import Kernel
from challenge_pack import TRAIN, INCOMPLETE, SEMANTICS, EXPECTED_STATES, TRAIN_MAX, TEST_MAX, heldout_rows, make_world

SCIENTIFIC_FREEZE_COMMIT = "17e656af253f440980fdf71588ae5b4a1c913b11"

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def safe(x):
    if isinstance(x, dict):
        return {str(k): safe(v) for k, v in x.items() if not str(k).startswith("_")}
    if isinstance(x, (list, tuple)):
        return [safe(v) for v in x]
    return x

def machine_from_result(r: dict) -> Machine:
    d = r["machine"]
    return Machine(int(d["initial"]), tuple(int(x) for x in d["outputs"]), tuple(tuple(int(z) for z in t) for t in d["transitions"]))

def exact_on(rows, machine: Machine) -> bool:
    return all(run_machine(machine, r.stream) == int(r.consequence) for r in rows)

def fixed_absolute_motif_window_fails() -> bool:
    rows = heldout_rows("motif101", flip=0, max_len=TEST_MAX)
    for start in range(TEST_MAX - 2):
        seen = {}
        ok = True
        for r in rows:
            s = tuple(r.stream)
            key = ("SHORT",) if len(s) < start + 3 else s[start:start+3]
            y = int(r.consequence)
            if key in seen and seen[key] != y:
                ok = False
                break
            seen[key] = y
        if ok:
            return False
    return True

def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    observed = {name: sha256(HERE / name) for name in freeze["scientific_core_paths"]}
    freeze_ok = observed == freeze["sha256"]

    results = {}
    heldout = {}
    structures = {}
    kernel = Kernel()
    for world in TRAIN:
        r = kernel.synthesize(world)
        results[world.world_id] = safe(r)
        if r.get("status") == "VERIFIED":
            m = machine_from_result(r)
            kind = world.world_id.split("_flip")[0]
            flip = int(world.world_id.split("_flip")[1].split("_")[0])
            hrows = heldout_rows(kind, flip=flip, max_len=TEST_MAX)
            heldout[world.world_id] = exact_on(hrows, m)
            structures[world.world_id] = Kernel.canonical_structure(m)
        else:
            heldout[world.world_id] = False

    by_kind = {kind: results[f"{kind}_flip0_L{TRAIN_MAX}"] for kind in SEMANTICS}
    machines = {kind: machine_from_result(by_kind[kind]) for kind in SEMANTICS if by_kind[kind].get("status") == "VERIFIED"}

    trigger = machines["trigger"]
    tq = trigger.initial
    trigger_shape = (
        trigger.outputs[tq] == 0 and
        trigger.transitions[tq][0] == tq and
        trigger.transitions[tq][1] != tq and
        trigger.outputs[trigger.transitions[tq][1]] == 1
    )

    parity = machines["parity"]
    pq = parity.initial
    parity_shape = (
        parity.transitions[pq][0] == pq and
        parity.transitions[pq][1] != pq and
        parity.transitions[parity.transitions[pq][1]][1] == pq
    )

    motif101 = machines["motif101"]
    variable = machines["variable_duration"]

    shifted_positions = all(run_machine(motif101, s) == 1 for s in (
        (1,0,1),
        (0,0,1,0,1),
        (1,1,1,0,1,0),
        (0,0,0,1,0,1,0,0),
    ))
    variable_durations = all(run_machine(variable, (0,) + (1,)*k + (0,)) == 1 for k in range(1, 7))
    variable_loop = any(t[1] == q and t[0] != q for q, t in enumerate(variable.transitions))

    incomplete = kernel.synthesize(INCOMPLETE)
    nover = kernel.synthesize(make_world("motif01"), verification_enabled=False)
    kernel_text = (HERE / "kernel.py").read_text().lower()

    gates = {}
    gates["E1_frozen_scientific_core_byte_identical"] = freeze_ok
    gates["E2_all_training_worlds_exact"] = all(r.get("status") == "VERIFIED" and r.get("exact_training_replay") for r in results.values())
    gates["E3_all_longer_heldout_streams_exact"] = all(heldout.values())
    gates["E4_constant_contracts_to_one_state"] = by_kind["constant"].get("state_count") == 1
    gates["E5_trigger_event_is_position_free_two_state_transition"] = by_kind["trigger"].get("state_count") == 2 and trigger_shape
    gates["E6_parity_persistence_is_two_state_recurrent_machine"] = by_kind["parity"].get("state_count") == 2 and parity_shape
    gates["E7_two_microstep_structure_requires_intermediate_residual"] = by_kind["motif01"].get("state_count") == 3 and by_kind["motif01"].get("distinguishing_horizon",0) >= 1
    gates["E8_three_microstep_structure_requires_deeper_residual"] = by_kind["motif101"].get("state_count") == 4 and by_kind["motif101"].get("distinguishing_horizon",0) >= 2
    gates["E9_variable_duration_structure_has_internal_duration_loop"] = by_kind["variable_duration"].get("state_count") == 4 and variable_loop
    gates["E10_same_structure_is_recognized_at_multiple_absolute_positions"] = shifted_positions
    gates["E11_same_structure_is_recognized_across_multiple_durations"] = variable_durations
    gates["E12_binary_relabelling_preserves_canonical_machine_structure"] = all(
        structures.get(f"{kind}_flip0_L{TRAIN_MAX}") == structures.get(f"{kind}_flip1_L{TRAIN_MAX}") for kind in SEMANTICS
    )
    gates["E13_strong_contraction_from_raw_stream_table"] = (sum(1 << k for k in range(TRAIN_MAX+1)) / by_kind["trigger"].get("state_count",999)) >= 50
    gates["E14_no_absolute_position_window_or_named_event_constructor_in_kernel"] = all(
        tok not in kernel_text for tok in ("read(", "atom(", "window", "motif", "substring", "event")
    )
    gates["E15_incomplete_authority_stays_unknown"] = incomplete.get("status") == "UNKNOWN_AUTHORITY"
    gates["E16_verifier_ablation_authorizes_no_machine"] = nover.get("status") == "UNKNOWN_NO_VERIFIER" and nover.get("state_count") == 0
    gates["E17_no_single_fixed_absolute_length3_window_solves_shifted_structure"] = fixed_absolute_motif_window_fails()
    gates["E18_training_length_six_transfers_exactly_to_length_ten"] = TRAIN_MAX == 6 and TEST_MAX == 10 and all(heldout.values())
    gates["E19_expected_minimum_state_counts_recovered"] = all(by_kind[k].get("state_count") == v for k, v in EXPECTED_STATES.items())

    evidence = {
        "experiment": "temporal_event_structure_genesis_v35",
        "scientific_freeze_commit": SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest": freeze,
        "observed_core_hashes": observed,
        "training_max_length": TRAIN_MAX,
        "heldout_max_length": TEST_MAX,
        "results": results,
        "heldout_exact": heldout,
        "gates": gates,
    }
    evidence["full_pass"] = all(gates.values())
    evidence["verdict"] = (
        "VERIFIED_TEMPORAL_EVENT_STRUCTURE_FROM_VARIABLE_LENGTH_MICROSTREAM_RESIDUALS"
        if evidence["full_pass"] else "TEMPORAL_EVENT_STRUCTURE_V35_GAPS_EXPOSED"
    )
    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
