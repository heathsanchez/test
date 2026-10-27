"""CPU-only witness assurance for H100 consequence-variant reports.

Checks bounded paired scalar values, tolerances, seed and model scope,
and top-token claims against their retained candidate logits. It cannot
independently reconstruct unretained full tensors or establish global maxima.
"""
import argparse
import json
import math
import re
from pathlib import Path

PIN = "7309cec801537b61fea3b50d7dfe454a6cde578e"
SEEDS = (0, 7, 21)
SCHEDULERS = ("rr", "dag")
PLAN = tuple(f"seed{seed}_{sched}" for seed in SEEDS for sched in SCHEDULERS)
FIELDS = ("hidden_states", "k_cache", "v_cache", "logits")
SIZES = {"hidden_states": 2048, "k_cache": 134217728, "v_cache": 134217728,
         "logits": 128256}
ATOL = 0.05
RTOL = 0.10


def require(condition, message):
    if not condition:
        raise ValueError("REJECTED_CONSEQUENCE_EVIDENCE: " + message)


def numerical(x):
    return type(x) in (int, float) and math.isfinite(x)


def load_json(path):
    def unique(pairs):
        out = {}
        for name, value in pairs:
            require(name not in out, "duplicate JSON property " + name)
            out[name] = value
        return out
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def audit(report):
    require(report.get("schema") == "mathgraph-h100-differential-v1", "schema")
    require(report.get("source_pin") == PIN, "source pin")
    require(report.get("probe_kind") == "consequence_variants", "probe kind")
    require(report.get("status") == "CONSEQUENCE_VARIANTS_RECORDED", "status")
    require(report.get("runpod_status") == "COMPLETED", "job status")
    require(isinstance(report.get("runpod_job_id"), str) and bool(report["runpod_job_id"]), "job id")
    require(report.get("sm_count") == 132 and "H100" in str(report.get("gpu_name")), "GPU identity")
    require(report.get("diagnostic_plan") == list(PLAN), "diagnostic plan")
    checks = report.get("checks")
    require(type(checks) is dict and set(checks) == set(PLAN), "case coverage")
    checked = {}
    for seed in SEEDS:
        for sched in SCHEDULERS:
            key = f"seed{seed}_{sched}"
            case = checks[key]
            require(case.get("source_commit") == PIN and case.get("tracked_worktree_clean") is True, "source " + key)
            require(case.get("input_seed") == seed and type(case.get("input_seed")) is int, "seed " + key)
            require(case.get("input_seed_override_calls") == 1, "seed hook " + key)
            require(isinstance(case.get("initial_state_sample_sha256"), str) and
                    re.fullmatch(r"[0-9a-f]{64}", case["initial_state_sample_sha256"]) is not None,
                    "initial-state fingerprint " + key)
            require(case.get("scheduler") == sched, "scheduler " + key)
            require(case.get("fixture_layers") == 16 and case.get("executed_layers") == 16, "architecture " + key)
            require(case.get("lm_head_exercised") is True, "LM head scope " + key)
            require(case.get("fields_compared") == list(FIELDS), "tensor scope " + key)
            require(case.get("tolerances") == {"atol": ATOL, "rtol": RTOL}, "tolerances " + key)
            require(type(case.get("pyvm_completed_calls")) is int and case["pyvm_completed_calls"] >= 1, "reference " + key)
            fields = case.get("fields")
            require(type(fields) is dict and set(fields) == set(FIELDS), "fields " + key)
            failures = []
            for name in FIELDS:
                f = fields[name]
                require(f.get("elements") == SIZES[name], "shape " + key + "/" + name)
                violations = f.get("violations")
                require(type(violations) is int and 0 <= violations <= SIZES[name], "violations")
                require(f.get("nonfinite") == 0, "nonfinite")
                require(numerical(f.get("max_abs_diff")) and f["max_abs_diff"] >= 0, "max abs")
                if violations:
                    failures.append("mismatch:" + name)
                    w = f.get("first_violations")
                    require(type(w) is list and 1 <= len(w) <= min(8, violations), "bounded witnesses")
                    indices = set()
                    for a in w:
                        idx = a.get("flat_index")
                        require(type(idx) is int and 0 <= idx < SIZES[name] and idx not in indices, "index")
                        indices.add(idx)
                        require(all(numerical(a.get(k)) for k in ("reference", "gpu", "abs_error", "allowed_error")), "numeric values")
                        expected_error = abs(a["reference"] - a["gpu"])
                        expected_allowed = ATOL + RTOL * abs(a["reference"])
                        require(abs(a["abs_error"] - expected_error) <= 1e-5, "raw error mismatch")
                        require(abs(a["allowed_error"] - expected_allowed) <= 1e-5, "allowance mismatch")
                        require(a["abs_error"] > a["allowed_error"], "nonviolating witness")
                        require(a["abs_error"] <= f["max_abs_diff"] + 1e-6,
                                "claimed global max error smaller than retained witness")
            require(case.get("reasons") == failures, "reason list " + key)
            require(case.get("passed") is (len(failures) == 0), "case verdict " + key)
            choice = case.get("logit_choice")
            require(type(choice) is dict, "missing choice")
            require(type(choice.get("reference_top1")) is int and type(choice.get("native_top1")) is int, "choice types")
            require(choice.get("top1_equal") is (choice["reference_top1"] == choice["native_top1"]), "choice agreement")
            require(all(numerical(choice.get(k)) and choice[k] >= 0 for k in
                        ("reference_top1_margin", "native_top1_margin")), "margins")
            ref5, native5 = choice.get("reference_top5"), choice.get("native_top5")
            require(type(ref5) is list and type(native5) is list and len(ref5) == 5 and len(native5) == 5, "top5 count")
            for ids in (ref5, native5):
                require(all(type(i) is int and 0 <= i < SIZES["logits"] for i in ids)
                        and len(set(ids)) == 5, "top5 ids")
            require(ref5[0] == choice["reference_top1"] and native5[0] == choice["native_top1"], "top1/top5")
            candidates = choice.get("candidate_logits")
            require(type(candidates) is list and 5 <= len(candidates) <= 10, "candidate size")
            require([c.get("index") for c in candidates] == sorted(set(ref5) | set(native5)), "candidate indices")
            pairs = {}
            for c in candidates:
                require(type(c.get("index")) is int and all(numerical(c.get(k)) for k in ("reference", "native")), "candidate values")
                pairs[c["index"]] = c
            for ids, field, margin_name in ((ref5, "reference", "reference_top1_margin"),
                                            (native5, "native", "native_top1_margin")):
                vals = [pairs[i][field] for i in ids]
                require(all(vals[i] >= vals[i+1] for i in range(4)), "top5 ordering")
                require(abs((vals[0] - vals[1]) - choice[margin_name]) <= 1e-5, "top1 margin mismatch")
                require(vals[0] >= max(c[field] for c in candidates), "candidate top1 mismatch")
            checked[key] = {"passed": case["passed"], "top1_equal": choice["top1_equal"],
                            "initial_state_sample_sha256": case["initial_state_sample_sha256"],
                            "reference_top1": choice["reference_top1"], "native_top1": choice["native_top1"],
                            "violations": {k: fields[k]["violations"] for k in FIELDS}}
    for seed in SEEDS:
        require(checks[f"seed{seed}_rr"]["initial_state_sample_sha256"] ==
                checks[f"seed{seed}_dag"]["initial_state_sample_sha256"],
                "RR and DAG initialized input samples differ")
    require(len({checks[f"seed{seed}_rr"]["initial_state_sample_sha256"]
                 for seed in SEEDS}) == len(SEEDS),
            "distinct input seeds produced identical sampled states")
    return {"schema": "mathgraph-h100-consequence-witness-audit-v1",
            "status": "BOUNDED_WITNESSES_CONSISTENT_NOT_RAW_FULL_TENSOR_REPLAY",
            "source_pin": PIN, "cases_checked": len(PLAN),
            "top_token_differences": sum(not v["top1_equal"] for v in checked.values()),
            "cases": checked,
            "trusted_boundary": "paired scalar witnesses originate on GPU worker; entire arrays not independently replayed"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("evidence", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = audit(load_json(args.evidence))
    serialized = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(serialized)
    print(serialized, end="")


if __name__ == "__main__":
    main()
