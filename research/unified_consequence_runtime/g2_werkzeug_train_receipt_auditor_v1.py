#!/usr/bin/env python3
"""Independent bounded receipt auditor; never certifies prospective G2."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as pool

EXPECTED = "02c0bbdf7c9254021b10ce296e8e9545cd60779b94053c4cf595790b868a47fd"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main(out):
    report=json.loads((out/"RESULT.json").read_text())
    result={"schema":"G2_WERKZEUG_TRAIN_NATIVE_INDEPENDENT_RECEIPT_AUDIT_V1",
            "status":"UNKNOWN_TRAINING_UNQUALIFIED","G2":"UNKNOWN","future":"SEALED_UNOPENED"}
    a=report.get("original_admission") or {}
    if report["status"]!="CANDIDATE_TRAINING_NATIVE_GREEN_AWAITING_INDEPENDENT_AUDIT":
        result["status"]="NOT_QUALIFIED_"+report["status"]
        (out/"INDEPENDENT_AUDIT.json").write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result))
        return
    assert a["repo"]=="pallets/werkzeug" and a["pr"]==3215
    assert a["status"]=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE"
    assert a["source_sha256"]==EXPECTED
    assert report["G2"]=="UNKNOWN" and report["future"]=="SEALED_UNOPENED"
    protected=a["protected_nodes"]
    assert len(protected)==2
    work=Path(a["work_dir"])
    source=work/"src/werkzeug/routing/map.py"
    author=work/a["protected_nodes"][0].split("::")[0]
    assert sha(source)==EXPECTED, "SOURCE_NOT_RESTORED"
    assert sha(author)==a["head_test_sha256"], "AUTHOR_TEST_BYTES_CHANGED"
    assert pool.git(work,"rev-parse","HEAD")== "1b00618e787f40dfb21eba29caf8f8be7c8e1d93"
    assert pool.git(work,"diff","--name-only").splitlines()==["tests/test_routing.py"]
    orig=out/"original-admission/native.xml"
    assert orig.exists()
    assert pool.junit(orig)=={"tests":2,"failures":1,"errors":0,"skipped":0}
    assert a["native"]["counts"]==pool.junit(orig)
    trials=report["candidate_trials"]
    accepted=[t for t in trials if "restoration" in t]
    assert len(accepted)==1, "AMBIGUOUS_CANDIDATE_SELECTION"
    t=accepted[0]
    index=t["rank"]
    assert 0<=index<report["candidate_count"]<=16
    assert all(not isinstance(x,dict) or "restoration" not in x for x in trials[index+1:]),"LATE_TRIAL"
    prefix="candidate-%02d-"%index
    for label,suffix,n in (("protected","protected",2),
                           ("routing_full","full",None),
                           ("withdrawal","withdrawal",2),
                           ("restoration","restored",2)):
        path=out/(prefix+suffix+".xml")
        log=out/(prefix+suffix+".log")
        assert path.exists() and log.exists(), "MISSING_ACTUAL_NATIVE_LOG"
        row=t[label]
        assert row["junit_sha256"]==sha(path) and row["log_sha256"]==sha(log)
        actual=pool.junit(path)
        assert row["counts"]==actual
        if label=="withdrawal":
            assert row["exit"]==1 and actual=={"tests":2,"failures":1,"errors":0,"skipped":0}
        elif label=="routing_full":
            assert row["exit"]==0 and actual["tests"]>2 and not any(actual[k] for k in ("failures","errors","skipped"))
        else:
            assert row["exit"]==0 and actual=={"tests":2,"failures":0,"errors":0,"skipped":0}
        parsed=json.loads(log.read_text())
        assert parsed["exit"]==row["exit"]
        argv=parsed["argv"]
        assert argv[1:4]==["-m","pytest","-q"]
        assert argv[4].startswith("--junitxml=")
        assert argv[-n:]==protected if n is not None else argv[-1]=="tests/test_routing.py"
        if n is not None:
            xml=ET.parse(path).getroot()
            got=[node.attrib["name"] for node in xml.iter("testcase")]
            expected=[node.split("::")[-1] for node in protected]
            assert sorted(got)==sorted(expected), "MISSING_PROTECTED_NATIVE_NODES"
    op=json.loads((out/"ACQUIRED_OPERATOR.json").read_text())
    assert op["training_source_sha256"]==EXPECTED
    assert op["training_patched_source_sha256"]==t["source_sha256"]
    assert op["selected_rank"]==index
    assert op["future"]=="SEALED_UNOPENED" and op["future_candidate_not_evaluated"] is True
    diff=out/"TRAINING_GENERATED_PATCH.diff"
    txt=diff.read_text()
    assert txt.startswith("--- original/src/werkzeug/routing/map.py\n+++ generated/src/werkzeug/routing/map.py\n")
    assert txt.count("\n--- ")==0 and txt.count("\n+++ ")==0, "UNAUTHORIZED_PATCH_TARGET"
    r=subprocess.run(["git","-C",str(work),"apply","--check","-p1",str(diff)],
                     capture_output=True,text=True,timeout=25)
    assert r.returncode==0, "PATCH_NOT_APPLICABLE:"+r.stderr[-300:]
    r=subprocess.run(["git","-C",str(work),"apply","-p1",str(diff)],
                     capture_output=True,text=True,timeout=25)
    assert r.returncode==0, "PATCH_REPLAY_FAILED"
    try:
        assert sha(source)==op["training_patched_source_sha256"],"PATCH_REPLAY_DIGEST_MISMATCH"
    finally:
        source.write_bytes(subprocess.check_output(["git","-C",str(work),"show","HEAD:src/werkzeug/routing/map.py"],timeout=25))
    assert sha(source)==EXPECTED
    result.update({"status":"WARRANTED_BOUNDED_TRAINING_OPERATOR_NATIVE_ONLY",
                   "original_protected":{"tests":2,"failures":1},
                   "candidate_protected":{"tests":2,"failures":0},
                   "candidate_full_count":t["routing_full"]["counts"]["tests"],
                   "generated_patch_sha256":sha(diff),
                   "operator_sha256":sha(out/"ACQUIRED_OPERATOR.json"),
                   "candidate_source_sha256":t["source_sha256"],
                   "native_withdrawal_restoration_verified":True,
                   "future_native_executions":0,"g2_warrant":False})
    (out/"INDEPENDENT_AUDIT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: independent_audit.py OUTPUT_DIR")
    main(Path(sys.argv[1]))
