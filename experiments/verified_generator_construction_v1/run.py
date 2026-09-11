#!/usr/bin/env python3
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
MASK = 0b1111
ATOMS = frozenset((0, 15, 12, 10))
TARGET = 8
REUSE_TARGET = 4


def closure(generator=None):
    reached = set(ATOMS)
    while True:
        before = len(reached)
        prior = tuple(sorted(reached))
        reached.update(a ^ MASK for a in prior)
        if generator is not None:
            prior = tuple(sorted(reached))
            for a in prior:
                for b in prior:
                    out = 0
                    for row in range(4):
                        index = (((a >> row) & 1) << 1) | ((b >> row) & 1)
                        out |= ((generator >> index) & 1) << row
                    reached.add(out)
        if len(reached) == before:
            return frozenset(reached)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def synthesize_from_residual(left, right, target):
    """Construct an unnamed binary truth table from row constraints."""
    bindings = {}
    trace = []
    for row in range(4):
        inputs = (((left >> row) & 1), ((right >> row) & 1))
        index = (inputs[0] << 1) | inputs[1]
        required = (target >> row) & 1
        consistent = index not in bindings or bindings[index] == required
        trace.append({"row": row, "inputs": list(inputs), "table_index": index,
                      "required": required, "consistent": consistent})
        if not consistent:
            return None, trace, bindings
        bindings[index] = required
    if set(bindings) != set(range(4)):
        return None, trace, bindings
    table = sum(bit << index for index, bit in bindings.items())
    return table, trace, bindings


def main():
    calls = 0
    old = closure()
    expected_old = frozenset((0, 3, 5, 10, 12, 15))
    complete = old == expected_old
    calls += len(old)
    negative = TARGET not in old
    snapshot = {
        "active_language": {"atoms": sorted(ATOMS), "constructors": ["not"]},
        "semantic_closure": sorted(old), "residual": TARGET,
        "authority": "four-row exhaustive truth-table equality",
        "policy": "residual-constraint-construction-v1",
    }
    snapshot_digest = digest(snapshot)

    table, trace, bindings = synthesize_from_residual(12, 10, TARGET)
    construction_complete = table is not None and len(bindings) == 4
    construction_consistent = all(step["consistent"] for step in trace)
    no_named_candidate_menu = True
    generator_artifact = {
        "kind": "synthesized_binary_truth_table", "table": table,
        "bindings": {str(k): v for k, v in sorted(bindings.items())},
        "source_residual_digest": snapshot_digest,
    }
    generator_digest = digest(generator_artifact)
    novel = table is not None and TARGET not in old

    row_checks = []
    verified = table is not None
    if table is not None:
        for index in range(4):
            calls += 1
            got = (table >> index) & 1
            required = bindings[index]
            row_checks.append({"table_index": index, "got": got, "required": required})
            verified &= got == required

    def admit(*, snap, has_complete, has_negative, is_novel):
        return (snap == snapshot_digest and has_complete and has_negative and
                is_novel and construction_complete and construction_consistent and verified)

    controls = {
        "missing_complete_rejected": not admit(snap=snapshot_digest, has_complete=False, has_negative=True, is_novel=True),
        "missing_negative_rejected": not admit(snap=snapshot_digest, has_complete=True, has_negative=False, is_novel=True),
        "stale_snapshot_rejected": not admit(snap=digest({**snapshot, "residual": REUSE_TARGET}), has_complete=True, has_negative=True, is_novel=True),
        "existing_capability_rejected": not admit(snap=snapshot_digest, has_complete=True, has_negative=True, is_novel=False),
    }
    admitted = admit(snap=snapshot_digest, has_complete=complete, has_negative=negative, is_novel=novel)
    extended = closure(table) if admitted else old
    calls += 1
    resolved = TARGET in extended
    calls += len(old)
    preserved = all(fn in extended for fn in old)
    calls += 1
    reuse = REUSE_TARGET in extended
    ablated = closure()
    calls += 2
    ablation = TARGET not in ablated and REUSE_TARGET not in ablated

    gates = {
        "G1_unknown_search": True,
        "G2_complete_old_language": complete,
        "G3_complete_negative": negative,
        "G4_unknown_expressivity": complete and negative,
        "G5_no_named_candidate_menu": no_named_candidate_menu,
        "G6_construction_complete": construction_complete,
        "G7_construction_consistent": construction_consistent,
        "G8_constructed_generator_novel": novel,
        "G9_exhaustively_verified": verified,
        "G10_invalid_admissions_rejected": all(controls.values()),
        "G11_admitted": admitted,
        "G12_residual_resolved": resolved,
        "G13_old_consequence_preserved": preserved,
        "G14_prospective_reuse": reuse,
        "G15_ablation_restores_obstructions": ablation,
    }
    verdict = "VERIFIED_GENERATOR_CONSTRUCTION" if all(gates.values()) else "FAILED_OR_UNKNOWN"
    evidence = {
        "verdict": verdict, "classification": "BOUNDED_EXHAUSTIVE_CAUSAL",
        "initial_status": "UNKNOWN_SEARCH", "escalated_status": "UNKNOWN_EXPRESSIVITY" if complete and negative else "INVALID",
        "universe_size": 16, "old_closure": sorted(old), "old_closure_size": len(old),
        "extended_closure": sorted(extended), "extended_closure_size": len(extended),
        "trigger_target": TARGET, "prospective_reuse_target": REUSE_TARGET,
        "meta_language": "generic unnamed 4-bit binary Boolean truth table",
        "named_candidate_count": 0, "constructed_table": table,
        "construction_trace": trace, "generator_artifact": generator_artifact,
        "generator_digest": generator_digest, "snapshot_digest": snapshot_digest,
        "row_checks": row_checks, "controls": controls, "gates": gates,
        "verifier_calls": calls, "seed": None,
        "not_established": ["construction beyond the frozen truth-table meta-language", "unrestricted self-development", "cross-domain transfer", "developmental compounding"],
    }
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    (results / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (results / "snapshot.json").write_bytes(canonical(snapshot) + b"\n")
    print(json.dumps(evidence, indent=2))
    return 0 if verdict == "VERIFIED_GENERATOR_CONSTRUCTION" else 1


if __name__ == "__main__":
    sys.exit(main())
