#!/usr/bin/env python3
"""
ACC Residual Constraint Extraction V1

Implements the CONSTRAIN step of the frozen Minimal Developmental Algorithm v5
without proposing a new mechanism.

Input authority is the completed 5-capability x 12-target boundary
qualification.  The script:
  * preserves the five certified saturated residuals;
  * derives only necessary outcome/architecture constraints supported by the
    frozen evidence;
  * separates upstream quotient-search obligations from downstream compiler
    obligations;
  * freezes the smallest finite current-Reach closure obtained by recombining
    parameter VALUES that were already admitted in the declared portfolio;
  * identifies untested equivalence classes inside that frozen closure.

It does not certify unrestricted expressive inadequacy and it does not license
a new search language.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


CAPABILITY_SPEC = {
    "gssub_basic": {
        "max_nodes": 150000,
        "reverse_depth": 0,
        "reverse_cap": 1,
        "compiler_beam": 1,
        "depth_weight": 0.0,
        "max_quotient_total": 72,
    },
    "reverse_augmented": {
        "max_nodes": 150000,
        "reverse_depth": 7,
        "reverse_cap": 250000,
        "compiler_beam": 1,
        "depth_weight": 0.0,
        "max_quotient_total": 72,
    },
    "compiler_beam": {
        "max_nodes": 150000,
        "reverse_depth": 7,
        "reverse_cap": 250000,
        "compiler_beam": 16,
        "depth_weight": 0.0,
        "max_quotient_total": 72,
    },
    "depth_weighted": {
        "max_nodes": 150000,
        "reverse_depth": 7,
        "reverse_cap": 250000,
        "compiler_beam": 16,
        "depth_weight": 0.25,
        "max_quotient_total": 72,
    },
    "full_current": {
        "max_nodes": 500000,
        "reverse_depth": 7,
        "reverse_cap": 250000,
        "compiler_beam": 16,
        "depth_weight": 0.0,
        "max_quotient_total": 100,
    },
}


def load(path):
    return json.loads(Path(path).read_text())


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True)
    ap.add_argument("--typed-results", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--runs-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--solver-sha", default="11fce564ed871a33fef8fa67dbd7394b0b9bb1fa")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    targets = load(args.targets)
    target_map = {
        (r["challenge_id"] if isinstance(r, dict) else str(r)): r
        for r in targets
    }
    typed = load(args.typed_results)
    report = load(args.report)

    if not report.get("declared_portfolio_complete"):
        raise SystemExit("refusing CONSTRAIN: declared portfolio is not complete")

    capabilities = report.get("declared_capabilities") or list(CAPABILITY_SPEC)
    if capabilities != list(CAPABILITY_SPEC):
        raise SystemExit(
            f"unexpected declared capability order/set: {capabilities}; "
            f"expected {list(CAPABILITY_SPEC)}"
        )

    runs = {}
    for cap in capabilities:
        p = Path(args.runs_root) / cap / "search_results.json"
        rows = load(p)
        runs[cap] = {r["challenge_id"]: r for r in rows}

    saturated = [
        r["challenge_id"]
        for r in typed
        if r.get("typed_result") == "UNKNOWN_SEARCH_BOUNDARY_SATURATED"
    ]
    verified_noncompetitive = [
        r["challenge_id"]
        for r in typed
        if r.get("typed_result") == "VERIFIED_BUT_NONCOMPETITIVE"
    ]
    if not saturated:
        raise SystemExit("no certified saturated residuals to constrain")

    residuals = []
    observed_pre_signatures = defaultdict(set)

    for cid in saturated:
        cap_evidence = []
        frozen_best = (target_map.get(cid) or {}).get("frozen_best")
        for cap in capabilities:
            row = runs[cap].get(cid)
            if row is None:
                raise SystemExit(f"missing completed evidence: {cap} {cid}")
            cap_evidence.append({
                "capability": cap,
                "nodes": row.get("nodes"),
                "max_nodes": row.get("max_nodes"),
                "quotient_found": bool(row.get("quotient_found")),
                "verified": bool((row.get("ac_verdict") or {}).get("ok")),
                "atomic_length": row.get("atomic_length"),
                "initial_total": row.get("initial_total"),
                "effective_quotient_total_cap": row.get("quotient_total_cap"),
                "compiler_beam": row.get("compiler_beam"),
                "depth_weight": row.get("depth_weight"),
            })

        # Boundary saturation is stronger here than a mere typed label:
        # all admitted executions ended at their node boundary and none reached
        # a quotient witness.
        if not all((e["nodes"] or 0) >= (e["max_nodes"] or 10**30) for e in cap_evidence):
            raise SystemExit(f"{cid} is typed saturated but has a non-saturated capability")
        if any(e["quotient_found"] for e in cap_evidence):
            raise SystemExit(f"{cid} is typed saturated but has a quotient witness")
        if any(e["verified"] for e in cap_evidence):
            raise SystemExit(f"{cid} is typed saturated but has a verified witness")

        full = runs["full_current"][cid]
        qcap = full["quotient_total_cap"]
        initial_total = full["initial_total"]

        for cap in capabilities:
            spec = CAPABILITY_SPEC[cap]
            row = runs[cap][cid]
            sig = (
                int(spec["max_nodes"]),
                float(spec["depth_weight"]),
                int(row["quotient_total_cap"]),
            )
            observed_pre_signatures[cid].add(sig)

        residuals.append({
            "challenge_id": cid,
            "frozen_best": frozen_best,
            "initial_total": initial_total,
            "effective_quotient_total_cap": qcap,
            "full_current_nodes": full["nodes"],
            "full_current_max_nodes": full["max_nodes"],
            "capability_evidence": cap_evidence,
            "constraints": [
                {
                    "id": "C_VERIFY",
                    "statement": "Any adequate continuation must produce an official-verifier-clean AC certificate.",
                    "basis": "Competition authority and protected consequence rule.",
                },
                {
                    "id": "C_STRICT_CONSEQUENCE",
                    "statement": (
                        f"To settle the frozen competitive encounter, a verified certificate must have "
                        f"length < {frozen_best}."
                        if isinstance(frozen_best, int)
                        else "To settle the competitive encounter, a verified certificate must improve the frozen consequence threshold."
                    ),
                    "basis": "Frozen incumbent consequence.",
                },
                {
                    "id": "C_PRE_QUOTIENT",
                    "statement": (
                        "A compiler-only or terminal-bridge-only change that leaves the quotient-search "
                        "trajectory unchanged cannot resolve this residual, because every admitted execution "
                        "failed before any quotient path existed."
                    ),
                    "basis": "All five capabilities have quotient_found=false; compilation is conditional on a quotient path in the pinned solver.",
                },
                {
                    "id": "C_RESOURCE_OR_REACH",
                    "statement": (
                        f"With the current depth-0 ordering and effective quotient cap {qcap}, "
                        f"500000 explored nodes were insufficient. An adequate continuation must therefore "
                        "either cross that resource boundary or alter/bypass pre-quotient constructive reach."
                    ),
                    "basis": "full_current exhausted 500000 nodes without quotient witness.",
                },
                {
                    "id": "C_REPLAY",
                    "statement": "Any admitted restructuring must preserve protected prior verifier-clean consequences.",
                    "basis": "Minimal Developmental Algorithm v5 protected-replay invariant.",
                },
            ],
            "not_established": [
                "representation inadequacy",
                "need for a new operator",
                "sufficiency of a larger node budget",
                "existence of one common repair for all saturated residuals",
                "unrestricted expressive inadequacy",
            ],
        })

    # Causal contrast: increasing the same depth-0 search budget from 150k to
    # 500k resolved quotient reach on some controls, proving that budget can
    # matter while also showing the five saturated cases remain beyond that
    # admitted budget boundary.
    budget_responders = []
    compiler_responders = []
    for cid in verified_noncompetitive:
        base = runs["compiler_beam"][cid]
        full = runs["full_current"][cid]
        if (
            not base.get("quotient_found")
            and full.get("quotient_found")
            and int(base.get("max_nodes") or 0) == 150000
            and int(full.get("max_nodes") or 0) == 500000
        ):
            budget_responders.append({
                "challenge_id": cid,
                "nodes_150k": base.get("nodes"),
                "nodes_full": full.get("nodes"),
                "full_atomic_length": full.get("atomic_length"),
            })

        greedy = runs["gssub_basic"][cid]
        beam = runs["compiler_beam"][cid]
        if (
            greedy.get("quotient_found")
            and beam.get("quotient_found")
            and greedy.get("atomic_length") is not None
            and beam.get("atomic_length") is not None
            and beam["atomic_length"] < greedy["atomic_length"]
        ):
            compiler_responders.append({
                "challenge_id": cid,
                "beam1_length": greedy["atomic_length"],
                "beam16_length": beam["atomic_length"],
                "saved": greedy["atomic_length"] - beam["atomic_length"],
                "same_search_nodes": greedy.get("nodes") == beam.get("nodes"),
            })

    # Freeze the smallest finite Reach closure justified without inventing a new
    # parameter value: Cartesian recombination of VALUES already admitted by
    # the declared portfolio.  For no-quotient residuals, reverse/compile
    # settings are downstream-equivalent; max_quotient_total 72 vs 100 is also
    # observationally equal because the solver's effective qcap is initial+36
    # for these targets.  Thus the only missing pre-quotient equivalence class
    # is 500k nodes with depth_weight 0.25.
    admitted_node_values = sorted({v["max_nodes"] for v in CAPABILITY_SPEC.values()})
    admitted_depth_values = sorted({v["depth_weight"] for v in CAPABILITY_SPEC.values()})

    reach_targets = []
    for r in residuals:
        cid = r["challenge_id"]
        qcap = r["effective_quotient_total_cap"]
        closure = {
            (int(n), float(dw), int(qcap))
            for n in admitted_node_values
            for dw in admitted_depth_values
        }
        observed = observed_pre_signatures[cid]
        missing = sorted(closure - observed)
        reach_targets.append({
            "challenge_id": cid,
            "effective_quotient_total_cap": qcap,
            "observed_prequotient_signatures": [
                {"max_nodes": n, "depth_weight": dw, "effective_quotient_total_cap": q}
                for n, dw, q in sorted(observed)
            ],
            "missing_prequotient_signatures": [
                {"max_nodes": n, "depth_weight": dw, "effective_quotient_total_cap": q}
                for n, dw, q in missing
            ],
        })

    unique_missing = {
        (m["max_nodes"], m["depth_weight"])
        for t in reach_targets
        for m in t["missing_prequotient_signatures"]
    }
    if unique_missing != {(500000, 0.25)}:
        raise SystemExit(f"unexpected missing pre-quotient closure: {sorted(unique_missing)}")

    candidate_targets = [
        {
            "challenge_id": r["challenge_id"],
            "frozen_best": r["frozen_best"],
            "max_nodes": 500000,
            "depth_weight": 0.25,
            # Use already-admitted best downstream settings. These do not
            # affect quotient proposal search and only become active after a hit.
            "reverse_depth": 7,
            "reverse_cap": 250000,
            "compiler_beam": 16,
            "max_quotient_total": 100,
        }
        for r in residuals
    ]

    # Current-observable residual classes.  This does not assert semantic
    # identity; it records indistinguishability under the admitted telemetry.
    classes = defaultdict(list)
    for r in residuals:
        signature = (
            r["initial_total"],
            r["effective_quotient_total_cap"],
            tuple(
                (e["capability"], e["nodes"], e["max_nodes"], e["quotient_found"])
                for e in r["capability_evidence"]
            ),
        )
        classes[str(signature)].append(r["challenge_id"])

    constraints_doc = {
        "experiment": "ACC_RESIDUAL_CONSTRAINT_EXTRACTION_V1",
        "source_algorithm": "Minimal Developmental Algorithm 2026-09-13 v5 Frozen Canonical",
        "solver_blob_sha": args.solver_sha,
        "object_level_obstruction_certified": True,
        "declared_portfolio_complete": True,
        "saturated_residual_count": len(residuals),
        "saturated_residuals": residuals,
        "causal_contrasts": {
            "budget_responders_150k_to_500k": budget_responders,
            "compiler_beam_responders": compiler_responders,
        },
        "constitutional_status": {
            "constrain_step": "AUTHORIZED_AND_EXECUTED",
            "restructure_within_frozen_reach_v1": "AUTHORIZED",
            "change_or_expand_reach_v1": "NOT_YET_AUTHORIZED",
            "unrestricted_expressive_inadequacy": False,
        },
    }

    reach_doc = {
        "reach_id": "ACC_REACH_V1_EXISTING_VALUE_CLOSURE",
        "definition": (
            "Finite Cartesian closure of max_nodes and depth_weight VALUES already admitted "
            "in the five-capability portfolio, quotiented by settings that are downstream-inert "
            "before quotient discovery on the saturated residuals."
        ),
        "admitted_max_nodes_values": admitted_node_values,
        "admitted_depth_weight_values": admitted_depth_values,
        "downstream_settings_fixed_for_execution": {
            "reverse_depth": 7,
            "reverse_cap": 250000,
            "compiler_beam": 16,
            "max_quotient_total": 100,
        },
        "target_closure": reach_targets,
        "only_missing_prequotient_equivalence_class": {
            "max_nodes": 500000,
            "depth_weight": 0.25,
        },
        "candidate_targets": candidate_targets,
        "completeness_claim_scope": (
            "If the missing class is executed on every saturated residual, the pre-quotient "
            "closure of these already-admitted parameter VALUES is complete. This is not a "
            "completeness claim over arbitrary numeric values or new search mechanisms."
        ),
    }

    class_doc = {
        "experiment": "ACC_RESIDUAL_OBSERVABLE_CLASSES_V1",
        "classes": [
            {"members": members, "size": len(members)}
            for members in sorted(classes.values(), key=lambda xs: (-len(xs), xs))
        ],
        "warning": (
            "These are equality classes only under currently recorded observables; they are "
            "not claims of mathematical or Andrews-Curtis equivalence."
        ),
    }

    summary = {
        "experiment": "ACC_RESIDUAL_CONSTRAINT_EXTRACTION_V1",
        "saturated_residuals": saturated,
        "object_level_obstruction_certified": True,
        "constraint_extraction_complete": True,
        "frozen_reach_v1": reach_doc["reach_id"],
        "missing_equivalence_class_count": 1,
        "missing_equivalence_class": reach_doc["only_missing_prequotient_equivalence_class"],
        "candidate_target_count": len(candidate_targets),
        "next_action": (
            "Execute only the missing 500000-node, depth_weight=0.25 pre-quotient class "
            "on the five saturated residuals; do not invent a new mechanism."
        ),
    }

    dump(out / "constraints.json", constraints_doc)
    dump(out / "reach_v1.json", reach_doc)
    dump(out / "residual_classes.json", class_doc)
    dump(out / "candidate_targets.json", candidate_targets)
    dump(out / "report.json", summary)
    print("RESIDUAL_CONSTRAINT_EXTRACTION", json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
