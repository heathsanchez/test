#!/usr/bin/env python3
"""Independent read-only audit of an original author-protected native future.

The audit never imports the producer nor executes the original external project.
It separately checks the original provider ZIP, native JUnit and exact upstream
BASE production / HEAD author-test blobs. A green audit is not G2 warrant.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
SHA256="6c563187693f6996de55b708eb3385a94d07d965c439fd49a68d2f5625c91d96"
ARTIFACT=12149513902
RUN=39163870757
FREEZE="a75a1914a00059a66c96f334bdbe9085a4eeb0e2"
AMENDMENT="8cdabbb936ee0d9fb5045beac923e776dab1450a"
SHIM="fd932d730744b0fb5528f74caeafe99ab13bf9fa"
BASE="e2feca1e567d9bafce657de8ad8bc668bd7ad513"
HEAD="cd9c12bb89c0c9d727a348b5fba3bd95730a9186"
SOURCE="backend/app/gateway/routers/agents.py"
TEST="backend/tests/test_custom_agent.py"

def h(raw):return hashlib.sha256(raw).hexdigest()
def run(cmd,timeout=140):
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
    assert p.returncode==0,("GIT_AUTHORITY_FAILURE",p.stderr[-700:])
    return p.stdout.strip()
def data(rev,path,repo=ROOT):
    return subprocess.check_output(["git","-C",str(repo),"show",rev+":"+path],timeout=80)
def require(actual,expected,label):
    if actual!=expected:
        raise AssertionError(label+": "+repr(actual)[:140]+" != "+repr(expected)[:140])

def check(archive):
    require(h(archive.read_bytes()),SHA256,"original_zip_sha256")
    with zipfile.ZipFile(archive) as z:
        require(z.testzip(),None,"all_member_crc")
        require(set(z.namelist()),{
            "RESULT.json","original-author-admission/RESULT.json",
            "original-author-admission/native.xml"},"exact_archive_names")
        science=json.loads(z.read("RESULT.json"))
        rec=json.loads(z.read("original-author-admission/RESULT.json"))
        x=ET.fromstring(z.read("original-author-admission/native.xml"))
    require(science["status"],"UNKNOWN_FUTURE_PROTECTED_CASE_MAPPING","correct_stop")
    require(science["G2"],"UNKNOWN","G2_not_promoted")
    require(science["future_opened"],True,"future_is_opened_not_sealed")
    require(science["future_causal_gain_verified"],False,"no_causal_transfer")
    require(science["freeze_commit"],FREEZE,"original_freeze_kept")
    require(science["original_native_admission"],{k:v for k,v in rec.items() if k!="provisioning"},"summary_matches_native_record")
    assert "new_composition" not in science and "unchanged_single_primitive" not in science
    require(science["Lean"],"NOT_EXECUTED","Lean_nonclaim")
    require(science["CLC"],"NOT_EXECUTED","CLC_nonclaim")
    require(science["FLASH"],"NOT_EXECUTED","FLASH_nonclaim")
    require(rec["environment_amendment"],"SOURCE_OWNED_UV_WORKSPACE_V11","owner_environment")
    require(rec["status"],"ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE","original_fail")
    require([rec["repo"],rec["pr"]],["bytedance/deer-flow",5960],"role_identity")
    require(rec["project_root"],"backend","source_project")
    require(rec["uv_version"]["stdout_tail"].strip(),"uv 0.11.1 (x86_64-unknown-linux-gnu)","owner_uv_version")
    require(rec["source_declared_dependency_sync"]["returncode"],0,"original_uv_lock")
    require(rec["native"]["returncode"],1,"authentic_native_exit")
    require(rec["native"]["counts"],{"tests":4,"failures":2,"errors":0,"skipped":0},"original_native_counts")
    require(rec["protected_nodes"],[
        TEST+"::TestAgentsAPI::test_trailing_newline_in_agent_name_is_rejected",
        TEST+"::test_agent_name_validation_rejects_trailing_newline"],"changed_author_AST_nodes")
    cases=list(x.iter("testcase"))
    require(len(cases),4,"actual_4_native_cases")
    names=[q.attrib["name"] for q in cases]
    require(len(set(names)),4,"no_double_counting")
    fails=[q for q in cases if q.find("failure") is not None]
    require(len(fails),2,"actual_2_failures")
    assert all(q.find("skipped") is None and q.find("error") is None for q in cases)
    require({q.attrib["name"].split("[")[0] for q in cases},{
        "test_trailing_newline_in_agent_name_is_rejected",
        "test_agent_name_validation_rejects_trailing_newline"},"native_case_owners")
    assert all("[reviewer\\n]" in q.attrib["name"] for q in fails),"terminal_newline_failure"
    assert sum("[" in q.attrib["name"] for q in cases)==4
    original_manifest_path=U+"G2_FINITE_COMPOSITION_FUTURE_FREEZE_V1.json"
    orig_manifest=data(FREEZE,original_manifest_path)
    require((ROOT/original_manifest_path).read_bytes(),orig_manifest,"original_science_freeze_immutable")
    amendment_path=U+"G2_FINITE_COMPOSITION_ENV_AMENDMENT_V11.json"
    require((ROOT/amendment_path).read_bytes(),data(AMENDMENT,amendment_path),"environment_amendment_immutable")
    shim_path=U+"g2_source_owned_uv_admission_v11.py"
    require((ROOT/shim_path).read_bytes(),data(SHIM,shim_path),"environment_shim_immutable")
    original_frozen=json.loads(orig_manifest)
    subject=original_frozen["future"]
    for k,v in (("repo","bytedance/deer-flow"),("pr",5960),("base",BASE),("head",HEAD),
                ("production",SOURCE),("author_test",TEST)):
        require(subject[k],v,"frozen_future_"+k)
    # Verify pristine actual Git object bytes, never read the author's fixed HEAD production.
    with tempfile.TemporaryDirectory(prefix="g2_deerflow_independent_") as td:
        work=Path(td)
        run(["git","init","-q",str(work)])
        run(["git","-C",str(work),"remote","add","origin",
             "https://github.com/bytedance/deer-flow.git"])
        for rev in (BASE,HEAD):
            run(["git","-C",str(work),"fetch","-q","--depth=1","--filter=blob:none",
                "--no-tags","origin",rev],180)
        src=data(BASE,SOURCE,work)
        test_base=data(BASE,TEST,work)
        test_head=data(HEAD,TEST,work)
        project=data(BASE,"backend/pyproject.toml",work)
        lock=data(BASE,"backend/uv.lock",work)
    require(h(src),rec["source_sha256"],"pinned_original_production")
    require(h(test_base),rec["base_test_sha256"],"pinned_original_author_test")
    require(h(test_head),rec["head_test_sha256"],"pinned_author_head_test")
    require(h(project),rec["original_project_pyproject_sha256"],"original_project_metadata")
    require(h(lock),rec["original_project_lock_sha256"],"original_project_lock")
    actual_blob=hashlib.sha1(("blob "+str(len(test_head))+"\0").encode()+test_head).hexdigest()
    require(actual_blob,rec["head_test_git_blob"],"author_test_git_blob")
    return {
        "schema":"G2_SOURCE_DISTINCT_NATIVE_FUTURE_INDEPENDENT_AUDIT_V1",
        "status":"WARRANTED_BOUNDED_AUTHENTIC_FUTURE_FAILURE_WITH_UNRUN_METHOD",
        "original_run":RUN,"original_artifact_id":ARTIFACT,"original_zip_sha256":SHA256,
        "project":"bytedance/deer-flow#5960",
        "native_tests":4,"original_passes":2,"original_failures":2,"errors":0,"skips":0,
        "changed_author_test_nodes":2,
        "parameterized_case_count":4,
        "method_applicability":"NOT_EXECUTED_BECAUSE_PRE_FROZEN_ONE_TO_ONE_CASE_BOUNDARY",
        "new_method_or_fix":"NOT_GENERATED","G2":"UNKNOWN",
        "future_source":"OPENED","Lean":"NOT_EXECUTED","CLC":"NOT_EXECUTED","FLASH":"NOT_EXECUTED",
        "source_ownership_checked":True,"original_native_tests_reexecuted":False
    }

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: auditor ORIGINAL.zip OUT.json")
    result=check(Path(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("INDEPENDENT_DEER_FLOW",result["status"],"G2",result["G2"])
