"""Independent, CPU-only audit of retained H100 depth-scan summaries.

Audits the *reported evidence contract*, not the raw CUDA tensor arithmetic:
the run artifact does not retain raw tensors. No credentials or GPU required.
"""
import argparse
import json
import math
from pathlib import Path
import zipfile

PIN = "7309cec801537b61fea3b50d7dfe454a6cde578e"
PLAN = ("rr_1", "rr_2", "rr_4", "rr_8", "rr_12", "rr_16", "dag_16")
ELEMENTS = {"hidden_states": 2048, "k_cache": 134217728,
            "v_cache": 134217728, "logits": 128256}
TOLERANCE = {"atol": 0.05, "rtol": 0.10}


def reject(message):
    raise ValueError("REJECTED_EVIDENCE: " + message)


def no_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            reject("duplicate JSON property " + key)
        obj[key] = value
    return obj


def read_evidence(path):
    if str(path).endswith(".zip"):
        with zipfile.ZipFile(path) as archive:
            if archive.namelist().count("remote_result.json") != 1:
                reject("expected one remote_result.json in ZIP")
            data = archive.read("remote_result.json")
    else:
        data = Path(path).read_bytes()
    return json.loads(data, object_pairs_hook=no_duplicate_keys)


def require(condition, message):
    if not condition:
        reject(message)


def finite_number(value):
    return type(value) in (float, int) and math.isfinite(value)


def audit(data):
    require(isinstance(data, dict), "expected object")
    require(data.get("schema") == "mathgraph-h100-differential-v1", "schema")
    require(data.get("status") == "DIAGNOSTIC_RECORDED", "diagnostic status")
    require(data.get("probe_kind") == "depth_diagnostic", "probe kind")
    require(data.get("source_pin") == PIN, "source pin")
    require(data.get("sm_count") == 132, "H100 SM count")
    require("H100" in str(data.get("gpu_name", "")), "GPU identity")
    require(data.get("runpod_status") == "COMPLETED", "remote completion")
    require(isinstance(data.get("runpod_job_id"), str) and bool(data["runpod_job_id"]), "job identity")
    require(data.get("diagnostic_plan") == list(PLAN), "registered seven-case plan")
    checks = data.get("checks")
    require(isinstance(checks, dict) and set(checks) == set(PLAN), "missing or extra cases")
    result = {}
    for key in PLAN:
        case = checks[key]
        depth = int(key.split("_")[1])
        fields = ("hidden_states", "k_cache", "v_cache") + (("logits",) if depth == 16 else ())
        require(case.get("source_commit") == PIN, "case source pin " + key)
        require(case.get("tracked_worktree_clean") is True, "dirty source " + key)
        require(case.get("fixture_layers") == 16 and case.get("executed_layers") == depth,
                "depth scope " + key)
        require(case.get("lm_head_exercised") is (depth == 16), "LM-head coverage " + key)
        require(case.get("fields_compared") == list(fields), "active output fields " + key)
        require(case.get("tolerances") == TOLERANCE, "changed tolerance " + key)
        require(type(case.get("pyvm_completed_calls")) is int and case["pyvm_completed_calls"] >= 1,
                "reference execution " + key)
        metrics = case.get("fields")
        require(isinstance(metrics, dict) and set(metrics) == set(fields), "field completeness " + key)
        failures = []
        for name in fields:
            m = metrics[name]
            require(m.get("elements") == ELEMENTS[name], "tensor shape " + key + "/" + name)
            require(type(m.get("violations")) is int and 0 <= m["violations"] <= m["elements"], "violation count")
            require(type(m.get("nonfinite")) is int and m["nonfinite"] == 0, "nonfinite output")
            require(finite_number(m.get("max_abs_diff")) and m["max_abs_diff"] >= 0, "difference statistic")
            if m["violations"]:
                failures.append("mismatch:" + name)
                witnesses = m.get("first_violations")
                require(isinstance(witnesses, list) and 1 <= len(witnesses) <= 8,
                        "missing bounded mismatch witnesses " + key + "/" + name)
                for w in witnesses:
                    require(type(w.get("flat_index")) is int and 0 <= w["flat_index"] < m["elements"],
                            "witness index")
                    require(all(finite_number(w.get(x)) for x in
                                ("reference", "gpu", "abs_error", "allowed_error")),
                            "witness nonfinite")
                    require(abs(abs(w["reference"]-w["gpu"])-w["abs_error"]) < 1e-5,
                            "witness arithmetic")
                    expected_allowance = TOLERANCE["atol"] + TOLERANCE["rtol"] * abs(w["reference"])
                    require(abs(w["allowed_error"] - expected_allowance) < 1e-5,
                            "witness allowance is not derived from reference")
                    require(w["abs_error"] > w["allowed_error"], "witness not violating bound")
        require(case.get("reasons") == failures, "reasons disagree with observed violations " + key)
        require(case.get("passed") is (len(failures) == 0), "reported verdict inconsistent " + key)
        choice = case.get("logit_choice")
        if depth == 16:
            require(isinstance(choice, dict), "missing top-token observation")
            require(type(choice.get("reference_top1")) is int and
                    type(choice.get("native_top1")) is int, "top-token identity")
            require(0 <= choice["reference_top1"] < ELEMENTS["logits"] and
                    0 <= choice["native_top1"] < ELEMENTS["logits"], "top-token range")
            require(choice.get("top1_equal") is
                    (choice["reference_top1"] == choice["native_top1"]), "top-token consistency")
            require(finite_number(choice.get("reference_top1_margin")) and
                    choice["reference_top1_margin"] >= 0, "token margin")
        else:
            require(choice is None, "unexecuted LM-head token claim")
        result[key] = {"passed": case["passed"],
                       "violations": {name: metrics[name]["violations"] for name in fields},
                       "top1_equal": choice["top1_equal"] if choice else None}
    first_failed = next((int(x.split("_")[1]) for x in PLAN if x.startswith("rr_") and
                         not result[x]["passed"]), None)
    return {
        "schema": "mathgraph-h100-independent-summary-audit-v1",
        "status": "SUMMARY_CONSISTENT_NOT_RAW_NUMERICALLY_REVERIFIED",
        "source_pin": PIN,
        "cases_checked": len(PLAN),
        "first_observed_rr_failure_depth": first_failed,
        "full16_top1_equal": {name: result[name]["top1_equal"] for name in ("rr_16", "dag_16")},
        "cases": result,
        "trusted_boundary": "device-generated tensor summaries; raw numerical arrays not retained",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("artifact", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = audit(read_evidence(args.artifact))
    serialized = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(serialized)
    print(serialized, end="")


if __name__ == "__main__":
    main()
