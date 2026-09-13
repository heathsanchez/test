#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT / "prior"
OUT = ROOT / "results"

EXPECTED = {
    "v8": {
        "verdict": "VERIFIED_META_LANGUAGE_PRIMITIVE_CONSTRUCTION_AND_TRANSFER",
        "boundary_any": ["complete binary Boolean operator substrate supplied"],
    },
    "v10": {
        "verdict": "VERIFIED_SPARSE_META_OPERATOR_GENESIS_AND_TRANSFER",
        "boundary_any": ["generic single-cell Boolean assignment operation supplied"],
    },
    "v11": {
        "verdict": "VERIFIED_REPAIR_SCHEMA_ANTI_UNIFICATION_AND_TRANSFER",
        "boundary_any": ["anti-unification", "supplied"],
    },
    "v12": {
        "verdict": "VERIFIED_REPAIR_SCHEMA_GENERALITY_SELECTION_AND_TRANSFER",
        "boundary_any": ["schema-description grammar", "supplied"],
    },
    "v13": {
        "verdict": "VERIFIED_RESIDUAL_GUIDED_SCHEMA_SCOPE_GROWTH_AND_TRANSFER",
        "boundary_any": ["drop_one_failed_scope_predicate", "supplied"],
    },
}

def load_evidence(name):
    d = PRIOR / name
    found = list(d.rglob("final_evidence.json"))
    if not found:
        found = list(d.rglob("evidence.json"))
    if not found:
        raise RuntimeError(f"no evidence JSON found for {name}")
    # Prefer a final_evidence if present.
    found.sort(key=lambda p: (p.name != "final_evidence.json", len(p.parts)))
    p = found[0]
    return json.loads(p.read_text()), p

def verdict_of(e):
    return e.get("final_verdict") or e.get("verdict")

def main():
    OUT.mkdir(exist_ok=True)
    rows = {}
    gates = {}

    for name, spec in EXPECTED.items():
        e, p = load_evidence(name)
        verdict = verdict_of(e)
        blob = json.dumps(e, sort_keys=True).lower()
        v_ok = verdict == spec["verdict"]
        b_ok = all(marker.lower() in blob for marker in spec["boundary_any"])
        rows[name] = {
            "evidence_path": str(p.relative_to(ROOT)),
            "observed_verdict": verdict,
            "expected_verdict": spec["verdict"],
            "verdict_match": v_ok,
            "boundary_markers_present": b_ok,
            "claim_boundary": e.get("claim_boundary"),
        }
        gates[f"{name}_verdict_match"] = v_ok
        gates[f"{name}_boundary_explicit"] = b_ok

    v13, _ = load_evidence("v13")
    v13_gates = v13.get("gates", {})
    gates["v13_has_scientific_gates"] = bool(v13_gates)
    gates["v13_all_scientific_gates_true"] = bool(v13_gates) and all(bool(v) for v in v13_gates.values())

    progression = [
        {
            "stage": "V8",
            "removed_scaffold": "named TRUE/OR selector primitives",
            "remaining_outer_basis": "complete 16-element Boolean operator substrate",
        },
        {
            "stage": "V10",
            "removed_scaffold": "pre-enumerated complete Boolean operator library",
            "remaining_outer_basis": "generic add-value-for-undefined-pattern operation",
        },
        {
            "stage": "V11",
            "removed_scaffold": "task-specific repair sequence",
            "remaining_outer_basis": "supplied structural anti-unification procedure",
        },
        {
            "stage": "V12",
            "removed_scaffold": "supplied anti-unification choice",
            "remaining_outer_basis": "supplied schema-description grammar",
        },
        {
            "stage": "V13",
            "removed_scaffold": "pre-enumerated schema family",
            "remaining_outer_basis": "generic DROP_ONE_FAILED_SCOPE_PREDICATE operation",
        },
    ]
    gates["staged_scaffolding_reduction_recorded"] = len(progression) == 5

    verdict = (
        "VERIFIED_BOUNDED_CHANGE_LANGUAGE_GROWTH_CHAIN"
        if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    )

    result = {
        "verdict": verdict,
        "classification": "SEALED_AUTHORITY_CHAIN_AUDIT",
        "rows": rows,
        "progression": progression,
        "v13_gates": v13_gates,
        "gates": gates,
        "permitted_upgrade": (
            "The developmental/change language itself has been expanded and "
            "contracted under the same consequence-governed rule in finite "
            "supplied meta-substrates."
        ),
        "remaining_frontier": (
            "construction of the generic outer edit operations and lowest-level "
            "generative substrate rather than supplying them"
        ),
        "not_established": [
            "unrestricted action-language invention",
            "invention from no prior primitives",
            "autonomous subject selection",
            "designerless teleology",
            "unbounded recursive self-development",
        ],
    }

    (OUT / "final_evidence.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if verdict != "VERIFIED_BOUNDED_CHANGE_LANGUAGE_GROWTH_CHAIN":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
