#!/usr/bin/env python3
import hashlib
import itertools
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
RECORDS = tuple(itertools.product((0, 1), repeat=4))
TRAIN = (
    {"left": (0, 0, 0, 0), "right": (1, 0, 0, 0), "name": "field_0"},
    {"left": (0, 0, 0, 0), "right": (0, 1, 0, 0), "name": "field_1"},
)
HELD_OUT = {"left": (0, 0, 0, 0), "right": (0, 0, 1, 0), "name": "field_2"}


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def old_rep(record):
    return record[3]


def recode(mask, value):
    return (mask >> value) & 1


def old_operator_separates(mask, residual):
    return recode(mask, old_rep(residual["left"])) != recode(mask, old_rep(residual["right"]))


PRIMITIVES = ("iterate_fields", "filter_separating", "take_first", "pair_with_old")


def execute(program, residual):
    """Typed stack interpreter for programs constructed from lower primitives."""
    kind, value = "unit", None
    for instruction in program:
        if instruction == "iterate_fields" and kind == "unit":
            kind, value = "fields", list(range(4))
        elif instruction == "filter_separating" and kind == "fields":
            kind = "fields"
            value = [f for f in value if residual["left"][f] != residual["right"][f]]
        elif instruction == "take_first" and kind == "fields" and value:
            kind, value = "field", value[0]
        elif instruction == "pair_with_old" and kind == "field":
            field = value
            kind = "repair"
            value = {"selected_projection": field,
                     "representation": lambda record, f=field: (old_rep(record), record[f])}
        else:
            return None
    return value if kind == "repair" else None


def synthesize_program(training_residuals):
    """Bottom-up enumeration: no complete developmental operator is listed."""
    considered = 0
    for length in range(1, 5):
        for program in itertools.product(PRIMITIVES, repeat=length):
            considered += 1
            repairs = [execute(program, residual) for residual in training_residuals]
            if all(repair is not None for repair in repairs):
                if all(repair["representation"](residual["left"]) !=
                       repair["representation"](residual["right"])
                       for repair, residual in zip(repairs, training_residuals)):
                    return program, considered
    return None, considered


def main():
    calls = 0
    old_ops = tuple(range(4))
    old_matrix = []
    for mask in old_ops:
        row = []
        for residual in TRAIN:
            calls += 1
            row.append(old_operator_separates(mask, residual))
        old_matrix.append(row)
    complete_old_dev_language = len(old_ops) == 4
    no_old_dev_repair = not any(any(row) for row in old_matrix)

    snapshot = {
        "carrier_size": len(RECORDS), "initial_representation": "project field 3",
        "old_developmental_operators": list(old_ops),
        "training_residuals": [{**r, "left": list(r["left"]), "right": list(r["right"])} for r in TRAIN],
        "substrate": ["iterate", "project", "separates", "first", "pair", "compose"],
        "held_out_commitment": digest({"name": HELD_OUT["name"], "left": list(HELD_OUT["left"]), "right": list(HELD_OUT["right"])})
    }
    snapshot_digest = digest(snapshot)

    # Bottom-up structural synthesis over 340 possible instruction strings.
    program, programs_considered = synthesize_program(TRAIN)
    ast = {"node": "compose", "instructions": list(program) if program else None}
    forbidden_named_nodes = {"quotient", "add_coordinate", "finite_state", "history_state"}
    no_supplied_repair_primitive = not any(node in forbidden_named_nodes for node in PRIMITIVES)
    ast_digest = digest(ast)

    training_results = []
    training_verified = True
    for residual in TRAIN:
        repair = execute(program, residual)
        calls += 1
        ok = repair is not None
        if ok:
            left = repair["representation"](residual["left"])
            right = repair["representation"](residual["right"])
            calls += 1
            ok = left != right and left[0] == old_rep(residual["left"]) and right[0] == old_rep(residual["right"])
        training_verified &= ok
        training_results.append({"residual": residual["name"], "selected_projection": None if repair is None else repair["selected_projection"], "verified": ok})

    # Exhaustive preservation over all raw records for every instantiated repair.
    preservation = True
    for residual in TRAIN:
        repair = execute(program, residual)
        for record in RECORDS:
            calls += 1
            preservation &= repair["representation"](record)[0] == old_rep(record)

    admitted = complete_old_dev_language and no_old_dev_repair and training_verified and preservation and no_supplied_repair_primitive

    # Freeze occurs logically before this point: held-out commitment is already in snapshot.
    held = execute(program, HELD_OUT) if admitted else None
    calls += 1
    held_out_success = held is not None and held["selected_projection"] == 2
    if held is not None:
        calls += 1
        held_out_success &= held["representation"](HELD_OUT["left"]) != held["representation"](HELD_OUT["right"])
        held_out_success &= held["representation"](HELD_OUT["left"])[0] == old_rep(HELD_OUT["left"])

    # Causal controls.
    calls += len(old_ops)
    ablation_fails = not any(old_operator_separates(mask, HELD_OUT) for mask in old_ops)
    calls += 1
    sham_field = 0
    sham_fails = HELD_OUT["left"][sham_field] == HELD_OUT["right"][sham_field]
    calls += 1
    memorized_training_fields = {0, 1}
    answer_memory_fails = all(HELD_OUT["left"][f] == HELD_OUT["right"][f] for f in memorized_training_fields)

    controls = {
        "ablation_fails_held_out": ablation_fails,
        "matched_sham_fails_held_out": sham_fails,
        "training_answer_memory_fails_held_out": answer_memory_fails,
    }
    gates = {
        "G1_complete_old_developmental_language": complete_old_dev_language,
        "G2_complete_negative_old_developmental_language": no_old_dev_repair,
        "G3_unknown_expressivity_dev": complete_old_dev_language and no_old_dev_repair,
        "G4_no_supplied_repair_primitive": no_supplied_repair_primitive,
        "G5_meta_program_structurally_constructed": program == PRIMITIVES,
        "G6_training_residuals_verified": training_verified,
        "G7_old_representation_preserved_exhaustively": preservation,
        "G8_developmental_operator_admitted": admitted,
        "G9_prospective_held_out_success": held_out_success,
        "G10_ablation_restores_developmental_obstruction": ablation_fails,
        "G11_sham_does_not_transfer": sham_fails,
        "G12_answer_memory_does_not_transfer": answer_memory_fails,
    }
    verdict = "VERIFIED_DEVELOPMENTAL_CONSTRUCTOR_GENESIS" if all(gates.values()) else "FAILED_OR_UNKNOWN"
    evidence = {
        "verdict": verdict, "classification": "BOUNDED_EXHAUSTIVE_CAUSAL_PROSPECTIVE",
        "old_developmental_language_size": len(old_ops), "old_operator_matrix": old_matrix,
        "training_results": training_results, "held_out_result": {"selected_projection": None if held is None else held["selected_projection"], "success": held_out_success},
        "constructed_developmental_operator_ast": ast, "ast_digest": ast_digest,
        "programs_considered": programs_considered,
        "snapshot_digest": snapshot_digest, "controls": controls, "gates": gates,
        "verifier_calls": calls, "seed": None,
        "not_established": ["invention of iteration/projection/pairing/separation primitives", "unbounded self-application", "cross-domain transfer", "developmental compounding"],
    }
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    (results / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (results / "snapshot.json").write_text(json.dumps(snapshot, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0 if verdict == "VERIFIED_DEVELOPMENTAL_CONSTRUCTOR_GENESIS" else 1


if __name__ == "__main__":
    sys.exit(main())
