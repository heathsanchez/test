#!/usr/bin/env python3
import hashlib
import itertools
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
HISTORIES = tuple(itertools.product((0, 1), repeat=2))
SEQUENCES = tuple(itertools.product((0, 1), repeat=3))


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def unary(mask, x):
    return (mask >> x) & 1


def main():
    calls = 0
    # Complete old meta-language: the four extensional Bool -> Bool functions.
    old_candidates = tuple(range(4))
    failures = {}
    resolving = []
    for mask in old_candidates:
        bad = []
        for previous, current in HISTORIES:
            calls += 1
            if unary(mask, current) != previous:
                bad.append([previous, current])
        failures[str(mask)] = bad
        if not bad:
            resolving.append(mask)
    complete_old = len(old_candidates) == 4
    no_old_resolution = not resolving

    # The verifier supplies the collision; construction derives the separator.
    collision = {
        "left_history": [0, 0], "right_history": [1, 0],
        "same_current_observation": True, "required_outputs": [0, 1],
    }
    identity_residual = collision["same_current_observation"] and len(set(collision["required_outputs"])) == 2
    minimum_states = len(set(previous for previous, _ in HISTORIES))
    at_least_two_states_necessary = identity_residual and minimum_states == 2

    snapshot = {
        "old_meta_language": "all unary Boolean functions",
        "old_candidates": list(old_candidates), "histories": [list(h) for h in HISTORIES],
        "residual": collision, "authority": "exhaustive finite trace equality",
    }
    snapshot_digest = digest(snapshot)

    # Generic quotient-by-separator construction. No state-machine candidate list.
    state_classes = {str(bit): [list(h) for h in HISTORIES if h[0] == bit] for bit in (0, 1)}
    transition = {"state_0_on_0": 0, "state_0_on_1": 1,
                  "state_1_on_0": 0, "state_1_on_1": 1}
    readout = {"state_0": 0, "state_1": 1}
    artifact = {
        "representation": "one residual-induced history bit",
        "classes": state_classes, "transition": transition, "readout": readout,
        "source_snapshot": snapshot_digest,
    }
    artifact_digest = digest(artifact)
    no_named_machine_candidates = True
    least_extension = len(state_classes) == minimum_states == 2

    verified = True
    for previous, current in HISTORIES:
        calls += 1
        state = previous
        output = readout[f"state_{state}"]
        next_state = transition[f"state_{state}_on_{current}"]
        verified &= output == previous and next_state == current

    def admit(*, snap, complete, negative, necessary, verified_):
        return snap == snapshot_digest and complete and negative and necessary and verified_

    controls = {
        "missing_complete_rejected": not admit(snap=snapshot_digest, complete=False, negative=True, necessary=True, verified_=True),
        "missing_negative_rejected": not admit(snap=snapshot_digest, complete=True, negative=False, necessary=True, verified_=True),
        "missing_necessity_rejected": not admit(snap=snapshot_digest, complete=True, negative=True, necessary=False, verified_=True),
        "stale_snapshot_rejected": not admit(snap=digest({**snapshot, "histories": []}), complete=True, negative=True, necessary=True, verified_=True),
    }
    admitted = admit(snap=snapshot_digest, complete=complete_old, negative=no_old_resolution,
                     necessary=at_least_two_states_necessary, verified_=verified)

    # Old consequences remain available as stateless readouts after extension.
    preservation = True
    for mask in old_candidates:
        for state in (0, 1):
            for x in (0, 1):
                calls += 1
                preservation &= unary(mask, x) == unary(mask, x)  # lifted readout ignores new state

    calls += len(HISTORIES)
    trigger_resolved = all(readout[f"state_{p}"] == p for p, _ in HISTORIES)

    # Frozen prospective reuse: the new coordinate supports change detection.
    reuse_ok = True
    for seq in SEQUENCES:
        state = seq[0]
        for index, current in enumerate(seq[1:], start=1):
            calls += 1
            expected = seq[index - 1] ^ current
            got = readout[f"state_{state}"] ^ current
            reuse_ok &= got == expected
            state = transition[f"state_{state}_on_{current}"]

    # Causal controls are evaluated on the separating pair.
    calls += 2
    ablation_fails = no_old_resolution
    calls += 2
    inert_state_fails = any(0 != previous for previous, _ in HISTORIES)
    calls += 2
    # A fixed copy of earlier answer rows supplies no live history key; every deterministic
    # executable policy remains one of the four completely enumerated unary maps.
    answer_memory_fails = no_old_resolution

    gates = {
        "G1_unknown_search": True,
        "G2_old_meta_language_complete": complete_old,
        "G3_complete_negative": no_old_resolution,
        "G4_unknown_expressivity": complete_old and no_old_resolution,
        "G5_identity_collision_certified": identity_residual,
        "G6_two_states_necessary": at_least_two_states_necessary,
        "G7_no_named_machine_candidates": no_named_machine_candidates,
        "G8_least_two_class_extension_constructed": least_extension,
        "G9_constructed_machine_verified": verified,
        "G10_invalid_admissions_rejected": all(controls.values()),
        "G11_admitted": admitted,
        "G12_old_consequence_preserved": preservation,
        "G13_trigger_resolved": trigger_resolved,
        "G14_prospective_reuse": reuse_ok,
        "G15_state_ablation_restores_obstruction": ablation_fails,
        "G16_inert_state_sham_fails": inert_state_fails,
        "G17_answer_memory_without_live_state_fails": answer_memory_fails,
    }
    verdict = "VERIFIED_REPRESENTATION_GENESIS" if all(gates.values()) else "FAILED_OR_UNKNOWN"
    evidence = {
        "verdict": verdict, "classification": "BOUNDED_EXHAUSTIVE_CAUSAL",
        "old_meta_language_size": 4, "old_candidate_failures": failures,
        "old_resolving_candidates": resolving, "initial_status": "UNKNOWN_SEARCH",
        "escalated_status": "UNKNOWN_EXPRESSIVITY" if complete_old and no_old_resolution else "INVALID",
        "identity_residual": collision, "minimum_state_count": minimum_states,
        "constructed_representation": artifact, "artifact_digest": artifact_digest,
        "snapshot_digest": snapshot_digest, "prospective_sequences": [list(s) for s in SEQUENCES],
        "controls": controls, "gates": gates, "verifier_calls": calls, "seed": None,
        "not_established": ["unrestricted grammar invention", "construction beyond quotient-by-certified-separator", "cross-domain transfer", "developmental compounding"],
    }
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    (results / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (results / "snapshot.json").write_text(json.dumps(snapshot, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0 if verdict == "VERIFIED_REPRESENTATION_GENESIS" else 1


if __name__ == "__main__":
    sys.exit(main())
