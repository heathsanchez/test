#!/usr/bin/env python3
"""Conservative cross-source G2 evidence gate; this NEVER issues a scientific warrant."""
import json
import sys

REQUIRED = (
"training_native_failure","training_generated_method","training_native_repair",
"training_withdrawal_restoration","method_frozen_before_future_open",
"future_native_failure","future_method_unchanged","future_native_repair",
"future_withdrawal_restoration","equal_information_comparator",
"lean_certificate_verified","clc_transport_verified","flash_revocation_verified",
"restart_replay_verified","independent_artifact_audit"
)
def classify(d):
    if not isinstance(d,dict): return {"status":"REJECTED_INVALID_INPUT"}
    if d.get("training_repo")==d.get("future_repo") and d.get("training_repo"):
        return {"status":"REJECTED_NOT_SOURCE_DISTINCT"}
    missing=[k for k in REQUIRED if k not in d]
    if missing: return {"status":"UNKNOWN_MISSING_OBLIGATIONS","missing":missing}
    if any(type(d[k]) is not bool for k in REQUIRED):
        return {"status":"REJECTED_INVALID_EVIDENCE_TYPES"}
    false=[k for k in REQUIRED if not d[k]]
    if false: return {"status":"UNKNOWN_UNQUALIFIED_OBLIGATIONS","unmet":false}
    if not (isinstance(d.get("baseline_native_passes"),int) and isinstance(d.get("acquired_native_passes"),int)):
        return {"status":"UNKNOWN_COMPARATOR_NOT_QUANTIFIED"}
    if d["acquired_native_passes"] <= d["baseline_native_passes"]:
        return {"status":"REJECTED_NO_FUTURE_GAIN_OVER_BASELINE"}
    return {"status":"CANDIDATE_AWAITING_INDEPENDENT_EVIDENCE_REPLAY",
            "warning":"Self-asserted flags are not external proof or WARRANTED status"}

if __name__=="__main__":
    obj=json.load(open(sys.argv[1],encoding="utf-8"))
    result=classify(obj)
    print(json.dumps(result,sort_keys=True,indent=2))
    sys.exit(0 if result["status"].startswith("CANDIDATE_") else 2)
