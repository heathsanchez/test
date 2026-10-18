#!/usr/bin/env python3
"""Independent read-only V5 artifact audit; NEVER executes untrusted tests or opens the future."""
from __future__ import annotations
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

P = "research/unified_consequence_runtime/"
SOURCE_RUN = 39111397991
ARTIFACT = 12130707189
DIGEST = "eee09325230545e4b577d154be141b9a38ec2dc272bbb4e281f13279c6f46e1c"
ROLE_COMMIT = "d96833fa8a41b4e5b67d5a9498ee1b1607c476e2"
PREQUERY_COMMIT = "fc3177b20e7508d511c32a9ec6c76d711cc8389d"
METHODS = [
    ("mutable", "094e2ddc3ba601a00eaf368151172a361e5542da", "g2_anyio_mutable_closure_equivalence_fix_v2.py"),
    ("projection", "d83de24d3b5bb4352cd6991a85a0fbc1e72f6deb", "residual_projection_method_v1.py"),
    ("projection_support", "b9d175d0b129c843bc5885aec77082f07f2b0601", "attrs_residual_observation_genesis_v1.py"),
]
FILES = {
    "g2-v5-native/PROGRESS.json",
    "g2-v5-native/RESULT.json",
    "g2-v5-native/admission-0/PIP_FREEZE.txt",
    "g2-v5-native/admission-0/RESULT.json",
    "g2-v5-native/admission-0/native.xml",
    "g2-v5-method/RESULT.json",
}

def sha(b):
    return hashlib.sha256(b).hexdigest()

def show(repo, revision, path):
    return subprocess.check_output(["git", "-C", str(repo), "show", revision+":"+path], timeout=65)

def eq(got, expected, label):
    if got != expected:
        raise AssertionError(label+": "+repr(got)[:130]+" != "+repr(expected)[:130])

def verify(archive_path, checkout):
    archive_bytes = archive_path.read_bytes()
    eq(sha(archive_bytes), DIGEST, "original_artifact_sha256")
    with zipfile.ZipFile(archive_path) as z:
        eq(z.testzip(), None, "zip_crc")
        names = z.namelist()
        eq(len(names), len(set(names)), "no_duplicate_zip_paths")
        eq(set(names), FILES, "exact_archived_members")
        a = json.loads(z.read("g2-v5-native/RESULT.json"))
        one = json.loads(z.read("g2-v5-native/admission-0/RESULT.json"))
        m = json.loads(z.read("g2-v5-method/RESULT.json"))
        xml = ET.fromstring(z.read("g2-v5-native/admission-0/native.xml"))
    role_path = P+"G2_OBSERVATION_CHOICE_V5_ROLE_FREEZE.json"
    pre_path = P+"G2_OBSERVATION_CHOICE_V5_PREQUERY.json"
    frozen = show(checkout, ROLE_COMMIT, role_path)
    eq((checkout/role_path).read_bytes(), frozen, "role_freeze_immutable")
    eq((checkout/pre_path).read_bytes(), show(checkout, PREQUERY_COMMIT, pre_path), "prequery_immutable")
    roles = json.loads(frozen)["roles"]
    eq([x["role"] for x in roles], ["TRAINING_0","TRAINING_1","TRAINING_2","SEALED_FUTURE"], "role_order")
    eq([x["repo"] for x in roles], ["pallets/flask","Textualize/textual","python-poetry/poetry-core","marshmallow-code/marshmallow"], "repository_order")
    role = roles[0]
    eq(a["role_freeze_commit"], ROLE_COMMIT, "role_identity")
    eq(a["status"], "ADMITTED_FIRST_NEW_PROTECTED_FAILURE_FUTURE_SEALED", "admission_status")
    eq(a["selected"], one, "selected_is_original_attempt")
    eq(a["admissions"], [one], "only_first_training_reached")
    eq(a["future"], "SEALED_UNOPENED", "future_not_opened_in_admission")
    eq(a["G2"], "UNKNOWN", "native_no_g2")
    eq((one["repo"],one["pr"],one["order"]), (role["repo"],role["number"],0), "training_role")
    eq(one["status"], "ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE", "original_failure")
    eq(one["protected_nodes"], ["tests/test_basic.py::test_method_route"], "changed_author_assertion")
    eq(one["future_source"], "SEALED_UNOPENED", "future_not_opened_in_attempt")
    eq(one["native"]["returncode"], 1, "native_returncode")
    eq(one["native"]["counts"], {"tests":6,"failures":1,"errors":0,"skipped":0}, "runner_counts")
    cases = list(xml.iter("testcase"))
    eq(len(cases), 6, "native_xml_cases")
    eq({x.attrib["name"] for x in cases}, {"test_method_route["+x+"]" for x in ("get","query","post","put","delete","patch")}, "original_native_cases")
    failed = [c for c in cases if c.find("failure") is not None]
    eq(len(failed), 1, "xml_actual_failure_count")
    eq(failed[0].attrib["name"], "test_method_route[query]", "real_original_obligation")
    assert "'Flask' object has no attribute 'query'" in failed[0].find("failure").attrib["message"]
    assert not list(xml.iter("error")) and not list(xml.iter("skipped")), "zero_import_error_and_skips"
    eq(m["status"], "UNKNOWN_NO_APPLICABLE_FROZEN_METHOD", "method_science")
    eq(m["decision"], "UNKNOWN_NO_APPLICABLE_FROZEN_METHOD", "method_decision")
    eq(m["candidate_results"], [], "no_repair_attempts")
    eq(m["future"], "SEALED_UNOPENED", "future_not_opened_in_method")
    eq(m["G2"], "UNKNOWN", "method_no_g2")
    eq(m["applicability"]["mutable"]["source_patterns"], 0, "no_mutable_closure")
    eq(m["applicability"]["mutable"]["qualified_patterns"], 0, "no_qualified_mutable_closure")
    eq(m["applicability"]["projection"]["negative_reason"], "NO_DIRECT_PARAMETRIZED_BOOLEAN_RESIDUAL", "no_boolean_projection")
    eq(m["applicability"]["projection"]["observation_classes"], 0, "no_observation_class")
    eq(m["training"]["source_sha256"], one["source_sha256"], "unchanged_source_bound_to_method")
    eq(m["training"]["test_sha256"], one["head_test_sha256"], "original_author_test_bound_to_method")
    eq(m["ledger_comparator"], "NOT_EXECUTED", "ledger_not_run")
    eq(m["agent_comparator"], "NOT_EXECUTED", "agent_not_run")
    for label, revision, filename in METHODS:
        raw = show(checkout, revision, P+filename)
        eq((checkout/(P+filename)).read_bytes(), raw, "method_immutable_"+label)
        eq(sha(raw), m["method_sha256"][label], "method_digest_"+label)
    # Re-read ONLY the already exposed original Flask training source/test. This
    # independently binds the archived hashes to immutable public source commits.
    with tempfile.TemporaryDirectory(prefix="v5_readonly_audit_") as tmp:
        root = pathlib.Path(tmp)
        subprocess.run(["git","init","-q",str(root)], check=True)
        subprocess.run(["git","-C",str(root),"remote","add","origin","https://github.com/pallets/flask.git"],check=True)
        for revision in (role["base"],role["author_head"]):
            subprocess.run(["git","-C",str(root),"fetch","-q","--depth=1","--filter=blob:none","origin",revision],check=True,timeout=120)
        original_source = show(root,role["base"],role["production"])
        original_test = show(root,role["base"],role["author_test"])
        author_test = show(root,role["author_head"],role["author_test"])
        eq(sha(original_source), one["source_sha256"], "actual_original_production_hash")
        eq(sha(original_test), one["base_test_sha256"], "actual_original_test_hash")
        eq(sha(author_test), one["head_test_sha256"], "actual_author_head_test_hash")
        blob_oid = hashlib.sha1(("blob "+str(len(author_test))+"\0").encode()+author_test).hexdigest()
        eq(blob_oid, one["head_test_git_blob"], "actual_author_head_git_blob")
    return {
        "schema":"UDM_V5_INDEPENDENT_SOURCE_BOUND_NATIVE_EVIDENCE_AUDIT",
        "status":"INDEPENDENTLY_VERIFIED_BOUNDED_NATIVE_FAILURE_AND_METHOD_INAPPLICABILITY",
        "original_run":SOURCE_RUN,
        "original_artifact":ARTIFACT,
        "original_artifact_sha256":sha(archive_bytes),
        "role_freeze":ROLE_COMMIT,
        "training":"pallets/flask#6133",
        "protected_native":{"passed":5,"failed":1,"errors":0,"skipped":0},
        "failure":"AttributeError: 'Flask' object has no attribute 'query'",
        "fixed_method_repair_candidates":0,
        "future":"SEALED_UNOPENED",
        "G2":"UNKNOWN",
        "G3":"UNKNOWN",
        "G4":"UNKNOWN",
        "audit_executed_target_tests":False
    }

def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py EVIDENCE.zip CHECKOUT OUT.json")
    answer = verify(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
    pathlib.Path(sys.argv[3]).write_text(json.dumps(answer,sort_keys=True,indent=2)+"\n")
    print("INDEPENDENT_V5_AUDIT",answer["status"],"G2",answer["G2"],"FUTURE",answer["future"])

if __name__ == "__main__":
    main()
