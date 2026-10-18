#!/usr/bin/env python3
"""Source-disjoint post-result audit of one frozen first-native-failure pool run.

Never executes arbitrary target source and never accesses source-sealed future.
No claim of new method acquisition or agent advantage.
"""
import hashlib,json,sys,xml.etree.ElementTree as ET,zipfile
from pathlib import Path

DIGEST="d22dbfe163dd96f9f837ea295cfc6ff52e6d0a47284ae13993fb1e1b293b202f"
PRE="research/unified_consequence_runtime/"
ART="evidence/g2-pool-v2/"

def require(value,message):
    if not value:raise AssertionError(message)

def main(p):
    b=p.read_bytes()
    require(hashlib.sha256(b).hexdigest()==DIGEST,"archive digest differs from exact original experiment")
    with zipfile.ZipFile(p) as z:
        require(z.testzip() is None,"archive member CRC failed")
        get=lambda name:json.loads(z.read(ART+name))
        lock=json.loads(z.read(PRE+"G2_NATIVE_FIRST_FAIL_POOL_V2_ROLE_FREEZE.json"))
        old=json.loads(z.read(PRE+"G2_NATIVE_FIRST_FAIL_POOL_V1_METADATA_STOP.json"))
        a=get("admission/RESULT.json")
        m=get("frozen-method-application/RESULT.json")
        independent=get("INDEPENDENT_BOUNDARY.json")
        assert old["status"]=="V1_METADATA_POOL_INCOMPLETE_UNKNOWN_BEFORE_NATIVE"
        assert old["found"]==6 and old["required_total"]==7
        assert len(lock["training_candidates"])==5 and len(lock["sealed_futures"])==1
        assert lock["sealed_futures"][0]["repo"]=="pypa/packaging"
        assert a["status"]=="QUALIFIED_TRAINING_FAILURE_FUTURE_SEALED"
        assert len(a["admissions"])==1
        s=a["selected"]
        assert s==a["admissions"][0]
        assert s["repo"]=="pallets/werkzeug" and s["pr"]==3215 and s["order"]==0
        assert s["source_sha256"]=="02c0bbdf7c9254021b10ce296e8e9545cd60779b94053c4cf595790b868a47fd"
        assert s["head_test_git_blob"]=="107f79c65e0783c7c866b72651c4d47e04aa6ebc"
        assert s["test_supplement"]=="GROUP:tests"
        assert s["protected_nodes"]==[
          "tests/test_routing.py::TestNoDomainMatching::test_build_external",
          "tests/test_routing.py::TestNoDomainMatching::test_build_relative",
        ]
        data=z.read(ART+"admission/admission-00/native.xml")
        root=ET.fromstring(data)
        cases=list(root.iter("testcase"))
        assert len(cases)==2
        failed=[x for x in cases if list(x.iter("failure"))]
        assert len(failed)==1 and "test_build_relative" in failed[0].attrib.get("name","")
        msg="".join(failed[0].itertext())
        assert "http://app.test/" in msg and "assert" in msg
        native=s["native"]
        assert native["returncode"]==1 and native["counts"]=={
            "tests":2,"failures":1,"errors":0,"skipped":0}
        assert m["status"]=="UNKNOWN_NO_VERIFIED_FIXED_METHOD_TRAINING_REPAIR"
        assert m["training"]=="pallets/werkzeug#3215"
        assert m["methods"]["mutable"]=={"patterns":0,"status":"UNKNOWN_NO_PATTERN"}
        assert m["methods"]["projection"]["status"]=="UNKNOWN_SOURCE_PATTERN_NOT_APPLICABLE"
        assert "TEST_FUNCTION_NOT_FOUND:test_is_class_var" in m["methods"]["projection"]["reason"]
        assert m["trained_methods"]==[] and m["applied_methods"]==0
        assert m["future_native"]=="NOT_EXECUTED"
        assert m["ledger_comparator"]=="NOT_EXECUTED"
        assert m["agent_comparator"]=="NOT_EXECUTED"
        assert m["heldout"]=="SEALED_UNOPENED"
        assert m["G2"]=="UNKNOWN"
        assert independent["selected"]=="pallets/werkzeug" and independent["admissions"]==1
        assert independent["fixed_method_status"]==m["status"]
        assert independent["future"]=="SEALED_UNOPENED"
        assert "pypa/packaging PR1446 SOURCE_UNOPENED" in z.read(ART+"FUTURE_SEAL.txt").decode()
    out={"status":"INDEPENDENTLY_VERIFIED_BOUNDED_NATIVE_FIRST_FAIL_AND_METHOD_INAPPLICABILITY",
        "archive_sha256":DIGEST,"training":"pallets/werkzeug#3215",
        "native_tests":2,"native_fail":1,"native_pass":1,
        "qualified_mutable_patterns":0,"qualified_projection_method":"INAPPLICABLE_TEST_SHAPE",
        "generated_repairs":0,"future":"SEALED_UNOPENED","G2":"UNKNOWN",
        "limit":"Original external native git/test hashes are source-controller receipts; complete source bytes not contained in this ZIP. Prior-art method inventory inapplicable on this task, not a universal no-go."}
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: verify_pool_artifact.py ORIGINAL_ARCHIVE")
    main(Path(sys.argv[1]))
