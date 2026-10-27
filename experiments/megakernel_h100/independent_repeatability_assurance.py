"""Independent CPU replay of H100 repeated-execution BF16 outputs.

Distinguishes exact bitwise native repeatability, reference repeatability,
and top-token repeatability. Recomputes every retained logit element using
the already-tested full-vector replay. Results are diagnostic and do not
imply scheduler equivalence or authorized external actions.
"""
import argparse
import json
from pathlib import Path

from independent_consequence_assurance import load_json, PIN, FIELDS, SIZES, ATOL, RTOL
from independent_full_logit_replay import replay, N

REPS = (1, 2, 3)
SCHED = ("rr", "dag")
PLAN = tuple(f"rep{i}_{s}" for i in REPS for s in SCHED)


def require(yes, problem):
    if not yes:
        raise ValueError("REJECTED_REPEATABILITY_EVIDENCE: " + problem)


def audit(report):
    require(report.get("schema") == "mathgraph-h100-differential-v1", "schema")
    require(report.get("probe_kind") == "repeat_seed0", "probe")
    require(report.get("status") == "REPEATABILITY_OBSERVATIONS_RECORDED", "status")
    require(report.get("source_pin") == PIN and report.get("runpod_status") == "COMPLETED", "source/job")
    require(report.get("sm_count") == 132 and "H100" in str(report.get("gpu_name")), "GPU")
    require(isinstance(report.get("runpod_job_id"), str) and report["runpod_job_id"], "job ID")
    require(report.get("repetition_plan") == list(PLAN), "plan")
    checks = report.get("checks")
    require(type(checks) is dict and set(checks) == set(PLAN), "coverage")
    result = {}
    for key in PLAN:
        case = checks[key]
        sched = key.rsplit("_", 1)[1]
        require(case.get("source_commit") == PIN and case.get("tracked_worktree_clean") is True, "pinned source "+key)
        require(case.get("input_seed") == 0 and case.get("input_seed_override_calls") == 1,
                "input seed "+key)
        require(case.get("scheduler") == sched, "scheduler "+key)
        require(case.get("fixture_layers") == 16 and case.get("executed_layers") == 16, "scope "+key)
        require(case.get("lm_head_exercised") is True, "lm head "+key)
        require(case.get("fields_compared") == list(FIELDS) and
                case.get("tolerances") == {"atol": ATOL, "rtol": RTOL}, "comparison policy "+key)
        require(type(case.get("pyvm_completed_calls")) is int and case["pyvm_completed_calls"] >= 1,
                "reference "+key)
        digest = case.get("initial_state_sample_sha256")
        require(type(digest) is str and len(digest) == 64 and
                all(x in "0123456789abcdef" for x in digest), "input sample digest")
        # This independently recomputes all 128256 logits and their
        # maximum errors from exact retained BF16 bits.
        values = replay(case)
        result[key] = {
            "initial_state_sample_sha256": digest,
            "reference_raw_sha256": values["reference_raw_sha256"],
            "native_raw_sha256": values["native_raw_sha256"],
            "reference_top1": values["reference_top1"],
            "native_top1": values["native_top1"],
            "top1_equal": values["top1_equal"],
            "logit_violations": values["tolerance_violations"],
            "max_abs_logit_error": values["max_abs_error"],
            "tensor_tolerance_passed": case.get("passed") is True,
        }
    input_fps = {c["initial_state_sample_sha256"] for c in result.values()}
    ref_hashes = {c["reference_raw_sha256"] for c in result.values()}
    by_scheduler = {
        sched: {
            "distinct_native_bitstreams": len({result[f"rep{i}_{sched}"]["native_raw_sha256"] for i in REPS}),
            "native_bitwise_repeatable": len({result[f"rep{i}_{sched}"]["native_raw_sha256"] for i in REPS}) == 1,
            "distinct_native_winners": len({result[f"rep{i}_{sched}"]["native_top1"] for i in REPS}),
        }
        for sched in SCHED
    }
    all_winners = {x["native_top1"] for x in result.values()}
    status = (
        "REFERENCE_AND_INPUT_REPEATABILITY_ESTABLISHED"
        if len(input_fps) == 1 and len(ref_hashes) == 1
        else "REFERENCE_OR_SAMPLED_INPUT_NONREPEATABLE"
    )
    return {
        "schema": "mathgraph-h100-bf16-repeatability-audit-v1",
        "status": status,
        "source_pin": PIN, "cases_checked": len(PLAN),
        "input_sample_digest_distinct_count": len(input_fps),
        "reference_output_digest_distinct_count": len(ref_hashes),
        "all_six_native_winners_equal": len(all_winners) == 1,
        "all_six_reference_native_top1_agree": all(x["top1_equal"] for x in result.values()),
        "by_scheduler": by_scheduler,
        "cases": result,
        "trusted_boundary": "raw BF16 worker-emitted logit arrays checked independently; inputs checked by sampled hashes only, no independent GPU execution",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("evidence", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    out = json.dumps(audit(load_json(args.evidence)), sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(out)
    print(out, end="")


if __name__ == "__main__":
    main()
