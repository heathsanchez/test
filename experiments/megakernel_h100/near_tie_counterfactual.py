"""Finite, adversarial decision-boundary audit of retained H100 BF16 logits.

Runs NO GPU; starts with independently replayed full BF16 pairs. For each
reference/native pair with a common unique winner w, add the *same* positive
FP64 offset delta to one nonwinner logit j in both vectors. Since all other
coordinates are unchanged, the reference and GPU disagree exactly when
delta lies strictly between their respective w-vs-j gaps. Exhaustively scan
all 128255 rivals; retain the earliest split interval and confirm by
recomputing both full-vector winners at its midpoint.

This is a counterfactual postprocessing intervention, NOT executed CUDA input,
new model weights, or evidence of a naturally occurring token disagreement.
"""
import argparse
import json
import math
from pathlib import Path
from independent_consequence_assurance import load_json, PLAN
from independent_full_logit_replay import audit as replay_audit, decode, N

BUDGETS = (0.05, 0.10, 0.20, 0.25)


def require(cond, why):
    if not cond:
        raise ValueError("REJECTED_COUNTERFACTUAL_EVIDENCE: " + why)


def winner(vec):
    return max(range(N), key=vec.__getitem__)


def case_sensitivity(case):
    raw = case["raw_logits_bf16"]
    ref, gpu = decode(raw["reference"]), decode(raw["native"])
    w = winner(ref)
    require(w == winner(gpu), "input case already has different top tokens")
    rival_ref = max(v for i, v in enumerate(ref) if i != w)
    rival_gpu = max(v for i, v in enumerate(gpu) if i != w)
    ref_margin, gpu_margin = ref[w] - rival_ref, gpu[w] - rival_gpu
    require(ref_margin > 0 and gpu_margin > 0, "original winner was tied")

    # First coordinate boost that can split the two output decisions.
    # An identical positive boost to one rival j leaves all other scores as-is.
    earliest = None
    for j in range(N):
        if j == w:
            continue
        a_gap = ref[w] - ref[j]
        b_gap = gpu[w] - gpu[j]
        lower, upper = sorted((a_gap, b_gap))
        if lower == upper:
            continue
        delta = lower + (upper - lower) / 2.0
        if not (lower < delta < upper):
            continue  # no finite representable strict counterexample
        candidate = (lower, upper, j, delta, a_gap, b_gap)
        if earliest is None or candidate[:3] < earliest[:3]:
            earliest = candidate
    require(earliest is not None, "no strict shared-offset split exists")
    lower, upper, j, delta, a_gap, b_gap = earliest
    ref_modified, gpu_modified = ref[:], gpu[:]
    ref_modified[j] += delta
    gpu_modified[j] += delta
    ref_new, gpu_new = winner(ref_modified), winner(gpu_modified)
    require(ref_new != gpu_new, "claimed shared-offset split is not real")
    require({ref_new, gpu_new} == {w, j}, "perturbed winner is neither original nor challenger")
    require(lower >= min(ref_margin, gpu_margin), "split contradicts original winners")

    budget_results = {}
    for budget in BUDGETS:
        # Search for a witness at strictly positive delta < budget; at
        # equality we do not promote tied decisions.
        cap = min(budget, upper)
        exists = lower < cap and lower + (cap - lower) / 2.0 > lower
        budget_results[str(budget)] = (
            "COUNTERFACTUAL_SPLIT_EXISTS" if exists
            else "NO_STRICT_SPLIT_BELOW_BUDGET")
    return {
        "reference_top1": w,
        "native_top1": winner(gpu),
        "reference_margin": ref_margin,
        "native_margin": gpu_margin,
        "one_coordinate_shared_boost_agreement_floor": min(ref_margin, gpu_margin),
        "earliest_split_infimum": lower,
        "split_interval_upper": upper,
        "challenger_index": j,
        "challenger_reference_gap": a_gap,
        "challenger_native_gap": b_gap,
        "strict_midpoint_boost": delta,
        "boosted_reference_top1": ref_new,
        "boosted_native_top1": gpu_new,
        "boosted_winners_differ": True,
        "original_reference_raw_sha256": raw["reference"]["raw_sha256"],
        "original_native_raw_sha256": raw["native"]["raw_sha256"],
        "budgets": budget_results,
    }


def audit(report):
    baseline = replay_audit(report)
    require(baseline["cases_checked"] == len(PLAN), "incomplete full vector replay")
    require(baseline["top1_agreements"] == len(PLAN), "original outputs already disagree")
    require(baseline["exhaustive_strict_winner_certificates"] == len(PLAN),
            "unresolved original winner tie")
    cases = {key: case_sensitivity(report["checks"][key]) for key in PLAN}
    return {
        "schema": "mathgraph-h100-common-offset-near-tie-v1",
        "status": "COUNTERFACTUAL_DECISION_BOUNDARIES_NOT_GPU_REEXECUTION",
        "source_pin": baseline["source_pin"],
        "cases_checked": len(PLAN),
        "strict_split_witnesses": sum(v["boosted_winners_differ"] for v in cases.values()),
        "budget_split_counts": {
            str(budget): sum(v["budgets"][str(budget)] == "COUNTERFACTUAL_SPLIT_EXISTS"
                             for v in cases.values())
            for budget in BUDGETS
        },
        "intervention": "identical positive FP64 additive offset to exactly one challenger logit; no upstream or GPU execution",
        "budget_units": "logit-score units; strict boost less than stated budget",
        "cases": cases,
        "trusted_boundary": "original worker-emitted BF16 bits, independently replayed; hypothetical downstream logit transformations only",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("evidence", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    output = json.dumps(audit(load_json(args.evidence)), indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
