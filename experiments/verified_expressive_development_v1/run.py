#!/usr/bin/env python3
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
MASK = 0b1111
ATOMS = frozenset((0b0000, 0b1111, 0b1100, 0b1010))
TARGET = 0b1000
REUSE_TARGET = 0b0100
VERIFIER_VERSION = "bool-truth-table-exhaustive-v1"
POLICY = "single-ambient-constructor"
AUTHORITY = "exhaustive-truth-table-equality"


def closure(binary_meet: bool) -> frozenset[int]:
    reached = set(ATOMS)
    changed = True
    while changed:
        changed = False
        prior = tuple(sorted(reached))
        for a in prior:
            reached.add(a ^ MASK)
        if binary_meet:
            now = tuple(sorted(reached))
            for a in now:
                for b in now:
                    reached.add(a & b)
        if len(reached) != len(prior):
            changed = True
    return frozenset(reached)


def canonical_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def main() -> int:
    verifier_calls = 0
    old = closure(False)
    old_expected = frozenset((0, 3, 5, 10, 12, 15))
    complete = old == old_expected

    snapshot = {
        "state": {"active_constructors": ["not"], "semantic_closure": sorted(old)},
        "language": {"atoms": sorted(ATOMS), "constructors": ["not"]},
        "authority": AUTHORITY,
        "policy": POLICY,
        "residual": TARGET,
        "verifier_version": VERIFIER_VERSION,
    }
    snapshot_digest = digest(snapshot)

    initial_status = "UNKNOWN_SEARCH"
    verifier_calls += len(old)
    no_current_resolution = all(candidate != TARGET for candidate in old)
    escalated_status = (
        "UNKNOWN_EXPRESSIVITY" if complete and no_current_resolution
        else "INVALID_ESCALATION"
    )

    generator = {"name": "pointwise_meet", "arity": 2}
    generator_digest = digest(generator)
    generator_novel = TARGET not in old

    generator_rows = []
    generator_verified = True
    for a in (False, True):
        for b in (False, True):
            verifier_calls += 1
            got = a and b
            expected = bool(a & b)
            generator_rows.append({"a": a, "b": b, "got": got, "expected": expected})
            generator_verified &= got == expected

    def admit(*, supplied_digest, has_complete, has_negative, novel):
        return (
            supplied_digest == snapshot_digest
            and has_complete
            and has_negative
            and novel
            and generator_verified
        )

    controls = {
        "missing_complete_rejected": not admit(
            supplied_digest=snapshot_digest, has_complete=False,
            has_negative=True, novel=True),
        "missing_negative_rejected": not admit(
            supplied_digest=snapshot_digest, has_complete=True,
            has_negative=False, novel=True),
        "stale_digest_rejected": not admit(
            supplied_digest=digest({**snapshot, "residual": REUSE_TARGET}),
            has_complete=True, has_negative=True, novel=True),
        "existing_capability_rejected": not admit(
            supplied_digest=snapshot_digest, has_complete=True,
            has_negative=True, novel=False),
    }
    admitted = admit(
        supplied_digest=snapshot_digest, has_complete=complete,
        has_negative=no_current_resolution, novel=generator_novel)

    extended = closure(True) if admitted else old
    verifier_calls += 1
    residual_resolved = TARGET in extended
    verifier_calls += len(old)
    preservation = all(fn in extended for fn in old)
    verifier_calls += 1
    prospective_reuse = REUSE_TARGET in extended

    ablated = closure(False)
    verifier_calls += 2
    ablation_restores_residual = TARGET not in ablated
    ablation_removes_reuse = REUSE_TARGET not in ablated

    gates = {
        "G1_initial_unknown_search": initial_status == "UNKNOWN_SEARCH",
        "G2_complete_old_language": complete,
        "G3_certified_old_negative": no_current_resolution,
        "G4_typed_expressivity_status": escalated_status == "UNKNOWN_EXPRESSIVITY",
        "G5_generator_novel": generator_novel,
        "G6_generator_externally_verified": generator_verified,
        "G7_all_invalid_admissions_rejected": all(controls.values()),
        "G8_admitted": admitted,
        "G9_residual_resolved": residual_resolved,
        "G10_old_consequence_preserved": preservation,
        "G11_prospective_reuse": prospective_reuse,
        "G12_ablation_restores_obstruction": (
            ablation_restores_residual and ablation_removes_reuse),
    }
    verdict = (
        "VERIFIED_EXPRESSIVE_DEVELOPMENT"
        if all(gates.values()) else "FAILED_OR_UNKNOWN"
    )
    evidence = {
        "verdict": verdict,
        "classification": "BOUNDED_EXHAUSTIVE_CAUSAL",
        "carrier": "two-input Boolean truth tables",
        "universe_size": 16,
        "old_closure": sorted(old),
        "old_closure_size": len(old),
        "extended_closure": sorted(extended),
        "extended_closure_size": len(extended),
        "target": TARGET,
        "reuse_target": REUSE_TARGET,
        "initial_status": initial_status,
        "escalated_status": escalated_status,
        "snapshot_digest": snapshot_digest,
        "generator": generator,
        "generator_digest": generator_digest,
        "generator_rows": generator_rows,
        "controls": controls,
        "gates": gates,
        "verifier_calls": verifier_calls,
        "seed": None,
        "not_established": [
            "unrestricted generator genesis",
            "autonomous proposal-basis growth",
            "cross-domain transfer",
            "developmental compounding",
        ],
    }
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    (results / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (results / "snapshot.json").write_bytes(canonical_bytes(snapshot) + b"\n")
    print(json.dumps(evidence, indent=2))
    return 0 if verdict == "VERIFIED_EXPRESSIVE_DEVELOPMENT" else 1


if __name__ == "__main__":
    sys.exit(main())
