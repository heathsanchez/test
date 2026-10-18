#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys

ALLOWED={
 "WARRANTED_BOUNDED_PROSPECTIVE_TRAINING_ACQUISITION_FUTURE_STILL_SEALED",
 "UNKNOWN_NO_QUALIFIED_MUTABLE_CLOSURE_PATTERN",
 "UNKNOWN_NO_NATIVE_STALE_CLOSURE_CAPTURE",
 "REJECTED_NO_NATIVE_TRAINING_REPAIR",
 "UNKNOWN_NO_AUTHENTIC_TRAINING_PROTECTED_FAILURE",
 "UNKNOWN_NO_MECHANICALLY_DERIVED_AUTHOR_TEST_NODE",
}

def main(result_path:Path,world:Path,out:Path):
    r=json.loads(result_path.read_text())
    assert r["schema"]=="UDM_G2_PROSPECTIVE_SOURCE_DISTINCT_V3_TRAINING"
    assert r["status"] in ALLOWED, r["status"]
    assert r["training_repository"]=="python-trio/trio" and r["training_pr"]==3525
    assert r["training_base"]=="ada9c778c86f35c62e68bae8284ca652ea2b23c2"
    assert r["future_repository"]=="pytest-dev/pluggy"
    assert r["future_source"]=="SEALED_UNOPENED"
    assert r["G2"]=="UNKNOWN"
    assert r["method_authority_commit"]=="094e2ddc3ba601a00eaf368151172a361e5542da"
    assert r["baseline"]["counts"]["tests"]>0 if "baseline" in r else True
    if r["status"]=="WARRANTED_BOUNDED_PROSPECTIVE_TRAINING_ACQUISITION_FUTURE_STILL_SEALED":
        assert r["training_repair"]["causal_withdrawal"] is True
        assert r["training_repair"]["restoration"] is True
        assert r["withdrawal"]["counts"]["failures"]>0
        assert r["restoration"]["counts"]["failures"]==0
        assert (result_path.parent/"GENERATED_REPAIR.py").is_file()
    # Head remains base commit; only author test overlay plus possible current generated
    # training production edit may be dirty. Future repo is not present in this gate.
    head=subprocess.check_output(["git","-C",str(world),"rev-parse","HEAD"],text=True).strip()
    assert head=="ada9c778c86f35c62e68bae8284ca652ea2b23c2"
    payload={
      "schema":"UDM_G2_PROSPECTIVE_SOURCE_DISTINCT_V3_TRAINING_INDEPENDENT_CHECK",
      "status":"PASS",
      "scientific_status":r["status"],
      "training":"python-trio/trio#3525",
      "future":"pytest-dev/pluggy#755",
      "future_source":"SEALED_UNOPENED",
      "method_authority_commit":r["method_authority_commit"],
      "G2":"UNKNOWN",
    }
    out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps(payload,sort_keys=True))

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: qualify_g2_prospective_source_distinct_v3_training.py RESULT WORLD OUT")
    main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),Path(sys.argv[3]).resolve())
