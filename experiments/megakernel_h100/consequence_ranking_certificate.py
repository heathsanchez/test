"""CPU-only conditional token ranking certificate for H100 evidence.

For reference winner w, second-best reference score r, global claimed
error bound eps=max_j|GPU_j-ref_j| and observed GPU winner score g_w:
    g_w > r + eps
implies GPU winner is w for the full vector, *conditional on those global
worker-reported summaries being accurate*. This checker does not replay full
logit arrays and explicitly refuses unconditional proof claims.
"""
import argparse
import json
from pathlib import Path

from independent_consequence_assurance import audit as audit_witnesses, load_json, PLAN


def certify(report):
    prior = audit_witnesses(report)
    entries = {}
    robust = 0
    for key in PLAN:
        case = report["checks"][key]
        choice = case["logit_choice"]
        winner = choice["reference_top1"]
        candidate = next(c for c in choice["candidate_logits"] if c["index"] == winner)
        ref_w = candidate["reference"]
        gpu_w = candidate["native"]
        margin = choice["reference_top1_margin"]
        max_error = case["fields"]["logits"]["max_abs_diff"]
        second_ref = ref_w - margin
        # Strict bound: for every j != w,
        # GPU_j <= REF_j + eps <= REF_second + eps < GPU_w.
        threshold = second_ref + max_error
        slack = gpu_w - threshold
        sufficient = slack > 0
        if sufficient and not choice["top1_equal"]:
            raise ValueError("Reported winner conflicts with proven conditional inequality")
        robust += int(sufficient)
        entries[key] = {
            "reference_winner": winner,
            "native_winner": choice["native_top1"],
            "reference_runner_up_score": second_ref,
            "reference_top1_score": ref_w,
            "native_winner_score": gpu_w,
            "claimed_global_max_logit_error": max_error,
            "sufficient_margin_slack": slack,
            "conditional_stability_certificate": sufficient,
            "conservative_two_epsilon_test": margin > 2 * max_error,
            "observed_top1_equal": choice["top1_equal"],
            "tensor_tolerance_passed": case["passed"],
        }
    return {
        "schema": "mathgraph-h100-conditional-ranking-certificate-v1",
        "status": "CONDITIONAL_RANKING_CERTIFICATES_RECORDED_NOT_RAW_REVERIFIED",
        "source_pin": prior["source_pin"],
        "cases_checked": len(PLAN),
        "cases_with_sufficient_ranking_margin": robust,
        "cases_with_observed_token_disagreement": prior["top_token_differences"],
        "formula": "GPU_w > (REF_w - REF_top1_margin) + max_j|GPU_j - REF_j|",
        "assumptions": [
            "worker-computed reference top-two scores are global across entire logits",
            "worker-computed maximum absolute logit error is global across entire logits",
            "GPU winner paired score is accurately retained",
            "the reference and GPU use the same input and pinned model"
        ],
        "raw_full_tensor_independently_replayed": False,
        "cases": entries,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("evidence", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = certify(load_json(args.evidence))
    serialized = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(serialized)
    print(serialized, end="")


if __name__ == "__main__":
    main()
