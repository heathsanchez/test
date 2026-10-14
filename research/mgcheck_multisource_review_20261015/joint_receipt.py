#!/usr/bin/env python3
"""Consequence-scoped consumer of two EXISTING, independently qualified receipts.

DOES NOT rerun models, generate tests, execute target repair code, or infer
contract truth from review prose. Imports the original source-qualified Go and
Python consumers byte-identically, then tests joint selective revocation.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/"research/reviewer_receipt_projection_20261015"))
import project_receipt as PYTHON_READER

GO9={
    "repo":"k1LoW/gh-copilot-review",
    "pr":9,
    "base":"5f3765a9ef25d9c5a57699418bed105d9ac54691",
    "head":"f98281938e63acd1d2df9b89d6af98dcf58c9fa8",
    "original_manifest_sha256":"758733a0ca2d0d531b01f550ecf97cee6a74279c6194db696888679ffa4ab7c5",
    "original_reader_git_blob":"fb75fd28d08edb6b5a79ed2bb4c053dfea20f500",
}
PYTHON={
    "repo":"allan-mobley-jr/gimmes",
    "pr":468,
    "head":"e1477f8b3f18c1de6ff87dbca9465a7b106dc193",
    "original_reader_git_blob":"79f72f72885d6a7cf9ebd3105107fc9ade1ee4b2",
    "review_input_git_blob":"aa08f762e4894ce92778964935d7cca1d54304dc",
}

def sha(b):return hashlib.sha256(b).hexdigest()
def git_blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def ensure(b,msg):
    if not b:raise AssertionError(msg)

def git(*args,cwd=None):
    v=subprocess.run(["git",*args],cwd=cwd,text=True,capture_output=True)
    if v.returncode:raise RuntimeError("SOURCE_GIT_FAIL "+v.stderr[-500:])
    return v.stdout.strip()

def import_go_reader(source):
    raw=Path(source).read_bytes()
    ensure(git_blob(raw)==GO9["original_reader_git_blob"],
           "UNQUALIFIED_GO_READER_SOURCE")
    spec=importlib.util.spec_from_file_location("original_go9_trusted_native",source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def changed_lines(repo,base,head,file):
    diff=git("diff","--unified=0",base,head,"--",file,cwd=repo)
    out=set()
    for line in diff.splitlines():
        m=re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@",line)
        if m:
            start=int(m.group(1));count=int(m.group(2) or 1)
            out.update(range(start,start+count))
    return out

def read_go(go_reader,go_root,source,pr=None,anchor=None):
    if git("rev-parse","HEAD",cwd=source)!=GO9["head"]:
        return [],{"status":"UNKNOWN_SOURCE_HEAD_MOVED"}
    try:
        out,state=go_reader.admit(
            source,
            pr or {"nwo":GO9["repo"],"pr_number":GO9["pr"]},
            GO9["base"],GO9["head"],["internal/github/github.go"],
            changed_lines,go_root,
            GO9["original_manifest_sha256"] if anchor is None else anchor)
        return out,state
    except Exception as e:
        return [],{"status":"UNKNOWN_GO_EVIDENCE_"+type(e).__name__}

def read_python(py_root,doc=None,receipt=None,logs=None):
    original,raw,files=PYTHON_READER.load(py_root)
    statement=doc if doc is not None else original
    native=receipt if receipt is not None else raw
    native_logs=logs if logs is not None else files
    return PYTHON_READER.project(statement,native,native_logs)

def assert_isolated(go_status,py_status,expected_go,expected_python):
    ensure(int(go_status.startswith("WARRANTED"))==expected_go,
           "GO_WRONG_PROMOTION_"+go_status)
    ensure(py_status["native_findings_promoted"]==expected_python,
           "PY_WRONG_PROMOTION")

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--go-root",type=Path,required=True)
    pa.add_argument("--go-source",type=Path,required=True)
    pa.add_argument("--go-reader",type=Path,required=True)
    pa.add_argument("--python-root",type=Path,required=True)
    pa.add_argument("--out",type=Path,required=True)
    a=pa.parse_args()
    ensure(git_blob((ROOT/"research/reviewer_receipt_projection_20261015/project_receipt.py").read_bytes())==
           PYTHON["original_reader_git_blob"],"UNQUALIFIED_PYTHON_READER_SOURCE")
    ensure(git_blob((ROOT/"research/reviewer_receipt_projection_20261015/review_input.json").read_bytes())==
           PYTHON["review_input_git_blob"],"UNQUALIFIED_REVIEW_INPUT")
    go_reader=import_go_reader(a.go_reader)
    go_root=a.go_root/"research/reviewbench_20261015/native_evidence"
    go_finding,go_state=read_go(go_reader,go_root,a.go_source)
    ensure(len(go_finding)==1 and go_state["status"]==
           "WARRANTED_BOUNDED_SUBJECT_BOUND_NATIVE_WITNESS",
           "ORIGINAL_GO9_PROOF_NOT_ADMITTED_"+str(go_state))
    py_result=read_python(a.python_root)
    ensure(py_result["subject"]["repo"]==PYTHON["repo"] and
           py_result["subject"]["head"]==PYTHON["head"] and
           py_result["native_findings_promoted"]==1 and
           py_result["unknown_or_withheld"]==2 and
           not py_result["admission_errors"],"ORIGINAL_PYTHON_PROOF_NOT_ADMITTED")
    ensure(len(py_result["records"])==3 and
           all(v["status"]=="UNKNOWN_NORMATIVE_CONTRACT"
               for v in py_result["records"] if not v["status"].startswith("WARRANTED")),
           "NORMATIVE_POLICY_WAS_LAUNDERED")

    controls=[]
    def save(name,gostate,pyvalue,native_gofindings,expected_go,expected_py):
        assert_isolated(gostate,pyvalue,expected_go,expected_py)
        controls.append({"control":name,"go_status":gostate,
                         "go_admitted":len(native_gofindings),
                         "python_admitted":pyvalue["native_findings_promoted"],
                         "python_unknown":pyvalue["unknown_or_withheld"]})
    save("both_unmodified",go_state["status"],py_result,go_finding,1,1)

    g,gs=read_go(go_reader,go_root,a.go_source,
                 pr={"nwo":"allan-mobley-jr/gimmes","pr_number":9})
    save("go_wrong_subject",gs["status"],py_result,g,0,1)

    g,gs=read_go(go_reader,go_root,a.go_source,anchor="0"*64)
    save("go_wrong_trust_anchor",gs["status"],py_result,g,0,1)

    with tempfile.TemporaryDirectory(prefix="qualified-receipt-") as td:
        shadow=Path(td)/"go-evidence"
        shutil.copytree(go_root,shadow)
        (shadow/"original.log").write_bytes((shadow/"original.log").read_bytes()+b"\nFORGED\n")
        g,gs=read_go(go_reader,shadow,a.go_source)
        save("go_corrupt_native_log",gs["status"],py_result,g,0,1)

        (shadow/"original.log").unlink()
        g,gs=read_go(go_reader,shadow,a.go_source)
        save("go_physically_missing_native_log",gs["status"],py_result,g,0,1)

        py_doc,py_receipt,py_logs=PYTHON_READER.load(a.python_root)

        bad=copy.deepcopy(py_doc)
        bad["subject"]["head"]="0"*40
        save("python_stale_head",go_state["status"],
             read_python(a.python_root,doc=bad),go_finding,1,0)

        bad=copy.deepcopy(py_receipt)
        bad["candidate_native_observer_and_old_suite"]["exit"]=1
        save("python_invalid_repair",go_state["status"],
             read_python(a.python_root,receipt=bad),go_finding,1,0)

        bad=dict(py_logs)
        bad["original_review_witness.log"]+=b"\nFORGED\n"
        save("python_corrupt_native_log",go_state["status"],
             read_python(a.python_root,logs=bad),go_finding,1,0)

        bad=dict(py_logs)
        del bad["original_review_witness.log"]
        save("python_missing_native_log",go_state["status"],
             read_python(a.python_root,logs=bad),go_finding,1,0)

        bad=copy.deepcopy(py_receipt)
        bad["final_exact_original_source_restored"]=False
        save("python_removed_source_authority",go_state["status"],
             read_python(a.python_root,receipt=bad),go_finding,1,0)

    # After all adversarial controls, both original independent consumers must
    # readmit EXACT original bytes and match the initial two qualified decisions.
    later_go,later_state=read_go(go_reader,go_root,a.go_source)
    later_py=read_python(a.python_root)
    save("both_recovered_from_exact_bytes",later_state["status"],later_py,later_go,1,1)

    result={
        "status":"WARRANTED_BOUNDED_TWO_SOURCE_REVIEW_PROPOSAL_TO_NATIVE_CONSEQUENCE",
        "source_qualification":"REUSED_UNCHANGED_PRIOR_GO_AND_PYTHON_EXECUTABLE_CONSUMERS",
        "review_source_boundary":"1_AUTHOR_CONTRACT_PLUS_3_PREEXISTING_STRONG_MODEL_PROPOSALS",
        "historical_subjects":{
            GO9["repo"]:{"pr":9,"head":GO9["head"],
                         "bounded_native_warrants":1,"unknowns":0},
            PYTHON["repo"]:{"pr":468,"head":PYTHON["head"],
                            "bounded_native_warrants":1,"unknowns":2}
        },
        "review_or_contract_candidates":4,
        "native_causal_warrants":2,
        "unresolved_normative_claims":2,
        "independent_source_partial_revocation_controls":controls,
        "safe_merge":"UNKNOWN",
        "live_strong_equal_info_coding_agent":"NOT_RUN",
        "new_defect_discovery":"NOT_CLAIMED",
        "new_native_method_generator":"NOT_CLAIMED",
        "no_new_source_exec":"TRUE_ORIGINAL_ARCHIVED_EVIDENCE_ONLY",
        "cross_subject_support_mixing":"REJECTED_BY_CONTROLS",
        "marketing_superiority":"UNKNOWN",
        "source_issued_actions":"ADVISORY_ONLY_NO_MERGE_OR_FIX",
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"candidates":4,"warrants":2,
                      "unknown":2,"controls":len(controls),
                      "warranted_bounded":True},sort_keys=True))
if __name__=="__main__":main()
