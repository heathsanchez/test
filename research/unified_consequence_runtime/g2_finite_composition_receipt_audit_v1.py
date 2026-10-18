#!/usr/bin/env python3
"""Independent replay of source identity and all native finite masks, not new testing.

Inputs are archived GitHub-native JUnit XML and logs plus upstream exact Git SHAs.
The checker does not trust source-run "status"/booleans as evidence.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

BASE="737215ece92b530204c8ccd68b63c60943ce5a79"
HEAD="3c4a07922fa3bd2f5fbcff8d73ddf7a0190c7b98"
SOURCE="src/mistral_common/protocol/instruct/validator.py"
TEST="tests/validation/test_validation.py"
EXPECTED_SOURCE_SHA="547eab1366fad5b7a452d957f3921b7fa1db14ef691a8d4a5760b269502fc63f"
EXPECTED_TEST_SHA="c7c9ae577b8454467517fd0547e4f72760e261815647e02c1ee4168429fe70bf"
EXPECTED_PROTECTED={
    "test_function_call_name_trailing_newline_rejected",
    "test_function_name_trailing_newline_rejected",
    "test_tool_call_id_trailing_newline_rejected",
    "test_tool_message_name_trailing_newline_rejected"
}

def digest(b): return hashlib.sha256(b).hexdigest()
def sha(path):return digest(Path(path).read_bytes())
def command(args,timeout=120):
    r=subprocess.run(args,text=True,capture_output=True,timeout=timeout)
    assert r.returncode==0, "GIT_SOURCE_REPLAY:"+r.stderr[-450:]
    return r.stdout.strip()

def checkout_original():
    work=Path("/tmp/g2-finite-mistral-independent-source-audit")
    assert not work.exists(),"DIRTY_CHECKOUT_PRECONDITION"
    command(["git","init","-q",str(work)])
    command(["git","-C",str(work),"remote","add","origin",
             "https://github.com/mistralai/mistral-common.git"])
    for rev in (BASE,HEAD):
        command(["git","-C",str(work),"fetch","-q","--depth=1","--filter=blob:none","--no-tags","origin",rev],160)
    command(["git","-C",str(work),"checkout","-q","--detach",BASE])
    test=(work/TEST)
    b=subprocess.check_output(["git","-C",str(work),"show",HEAD+":"+TEST],timeout=50)
    test.write_bytes(b)
    assert sha(test)==EXPECTED_TEST_SHA
    assert sha(work/SOURCE)==EXPECTED_SOURCE_SHA
    assert command(["git","-C",str(work),"diff","--name-only"]).splitlines()==[TEST]
    return work

def native_receipt(e,label,expected_test_names=None):
    log=e/(label+".log")
    junit=e/(label+".xml")
    assert log.exists() and junit.exists(),"MISSING_NATIVE_RECEIPT:"+label
    raw=json.loads(log.read_text())
    assert isinstance(raw["argv"],list) and "-m" in raw["argv"] and "pytest" in raw["argv"]
    assert raw["argv"][1:4]==["-m","pytest","-q"]
    assert raw["argv"][4].startswith("--junitxml=")
    tests={}
    for node in ET.parse(junit).getroot().iter("testcase"):
        name=node.attrib.get("name")
        assert name and name not in tests,"DUPLICATE_CASE"
        tags={v.tag for v in node}
        tests[name]=("ERROR" if "error" in tags else "SKIP" if "skipped" in tags
                     else "FAIL" if "failure" in tags else "PASS")
    assert tests and all(x in ("PASS","FAIL") for x in tests.values()),"INCONCLUSIVE_TEST"
    if expected_test_names is not None:assert set(tests)==expected_test_names
    return {"tests":tests,"log_sha256":sha(log),"junit_sha256":sha(junit),
            "exit":raw.get("exit",raw.get("returncode"))}

def composed(src,lines_for_bits,mask):
    s=src.splitlines(keepends=True)
    for bit,line in enumerate(lines_for_bits):
        if not (mask & (1<<bit)):continue
        ix=line-1
        current=s[ix]
        match=list(re.finditer(r"(?<!\\)\$([\"'])",current))
        assert len(match)==1,("EXACT_ONE_TERMINAL_LITERAL_PER_SELECTED_LINE",line)
        p=match[0]
        s[ix]=current[:p.start()]+r"\Z"+current[p.end()-1:]
    return "".join(s).encode()

def main(e):
    report=json.loads((e/"RESULT.json").read_text())
    r={"schema":"G2_FINITE_COMPOSITION_MISTRAL_NATIVE_INDEPENDENT_AUDIT_V1",
       "status":"UNKNOWN_NOT_QUALIFIED","G2":"UNKNOWN",
       "source_identities_checked":False,"native_subsets_checked":0}
    assert report["status"]=="CANDIDATE_FINITE_MONOTONE_COMPOSITION_AWAITING_INDEPENDENT_AUDIT"
    assert report["G2"]=="UNKNOWN" and report["future"]=="DEER_FLOW_SOURCE_SEALED_UNOPENED"
    assert report["candidate_count"]==4 and report["trial_count"]==10
    assert report["original_admission"]["status"]=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE"
    assert report["original_admission"]["source_sha256"]==EXPECTED_SOURCE_SHA
    assert report["original_admission"]["head_test_sha256"]==EXPECTED_TEST_SHA
    assert report["original_admission"]["native"]["counts"]=={"tests":4,"failures":4,"errors":0,"skipped":0}
    original_xml=e/"original-admission/native.xml"
    x=list(ET.parse(original_xml).getroot().iter("testcase"))
    assert len(x)==4 and {v.attrib["name"] for v in x}==EXPECTED_PROTECTED
    assert all(any(c.tag=="failure" for c in test) for test in x)
    work=checkout_original()
    original=(work/SOURCE).read_bytes()
    source=original.decode("utf-8")
    selected=report["selected"]
    assert [s["index"] for s in selected]==[0,1,2,3]
    catalog=report["candidate_catalog"]
    selected_lines=[catalog[item["index"]]["line"] for item in selected]
    assert len(set(selected_lines))==4
    assert all(catalog[i]["candidate_sha256"]==digest(composed(source,[catalog[i]["line"]],1))
               for i in range(4))
    # The full patch must exactly reproduce the source-native generated edits.
    generated=composed(source,selected_lines,15)
    assert digest(generated)==report["full_source_sha256"]
    patch=(e/"COMPOSED_GENERATED_PATCH.diff").resolve()
    assert patch.read_text().startswith("--- original/"+SOURCE+"\n+++ generated/"+SOURCE+"\n")
    assert sha(patch)==report["composed_patch_sha256"]
    command(["git","-C",str(work),"apply","--check","-p1",str(patch)])
    command(["git","-C",str(work),"apply","-p1",str(patch)])
    assert (work/SOURCE).read_bytes()==generated
    assert command(["git","-C",str(work),"diff","--name-only"]).splitlines()==sorted([SOURCE,TEST])
    r["source_identities_checked"]=True
    cases={}
    for mask in range(16):
        entry=report["subsets"][str(mask)]
        assert entry["mask"]==mask
        expected_indices=[selected[j]["index"] for j in range(4) if mask&(1<<j)]
        assert entry["applied_original_candidate_indices"]==expected_indices
        assert entry["source_sha256"]==digest(composed(source,selected_lines,mask))
        receipt=native_receipt(e,"subset-%02d"%mask,EXPECTED_PROTECTED)
        assert entry["receipt"]["log_sha256"]==receipt["log_sha256"]
        assert entry["receipt"]["junit_sha256"]==receipt["junit_sha256"]
        assert receipt["tests"]==entry["verdicts"]
        assert receipt["exit"]==(0 if mask==15 else 1)
        assert entry["passing"]==sorted(k for k,v in receipt["tests"].items() if v=="PASS")
        assert len(entry["passing"])==mask.bit_count(),"NON_ADDITIVE_NATIVE_CONSEQUENCE"
        cases[mask]=set(entry["passing"])
        r["native_subsets_checked"]+=1
    independent_singletons=[cases[1<<j] for j in range(4)]
    assert all(len(x)==1 for x in independent_singletons)
    assert len(set.union(*independent_singletons))==4
    assert cases[0]==set() and cases[15]==EXPECTED_PROTECTED
    for mask in range(16):
        expected_union=set.union(set(),*(independent_singletons[j] for j in range(4) if mask&(1<<j)))
        assert cases[mask]==expected_union,("FAILURE_TO_COMPOSE",mask)
    r["independent_singleton_outcome_to_site"]={
        str(j):list(next(iter(independent_singletons[j])) for _ in range(1)) for j in range(4)}
    for key,spec in (("withdrawal",("physical-all-withdrawal",0)),
                     ("restoration",("physical-all-restoration",4))):
        label,want=spec
        receipt=native_receipt(e,label,EXPECTED_PROTECTED)
        assert sum(v=="PASS" for v in receipt["tests"].values())==want
        assert report[key]["log_sha256"]==receipt["log_sha256"]
        assert report[key]["junit_sha256"]==receipt["junit_sha256"]
        assert receipt["exit"]==(0 if want==4 else 1)
    full=native_receipt(e,"full-author-suite")
    assert len(full["tests"])==17 and all(v=="PASS" for v in full["tests"].values())
    assert full["log_sha256"]==report["full_author_suite"]["log_sha256"]
    assert full["junit_sha256"]==report["full_author_suite"]["junit_sha256"]
    assert full["exit"]==0
    for item in report["candidate_trials"]:
        lab="search-step%02d-candidate%02d"%(item["step"],item["index"])
        receipt=native_receipt(e,lab,EXPECTED_PROTECTED)
        assert item["receipt"]["log_sha256"]==receipt["log_sha256"]
        assert item["receipt"]["junit_sha256"]==receipt["junit_sha256"]
        assert item["native_vector"]==receipt["tests"]
        assert item["counts"]["failures"]==sum(v=="FAIL" for v in receipt["tests"].values())
    r.update({"status":"WARRANTED_BOUNDED_FINITE_COMPOSITION_NATIVE_RECEIPTS",
              "full_source_sha256":digest(generated),
              "original_source_sha256":EXPECTED_SOURCE_SHA,
              "original_protected_failures":4,
              "repaired_protected_passes":4,
              "full_author_tests_passed":17,
              "subset_states":16,"candidate_trials":10,
              "physical_withdrawal_restoration_verified":True,
              "independent_additive_boolean_consequence_lattice":True,
              "native_to_world_truth_assumption_not_proved":True,
              "new_source_distinct_future_success":False})
    (e/"INDEPENDENT_AUDIT.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:r.get(k) for k in ("status","G2","native_subsets_checked",
           "full_author_tests_passed","independent_additive_boolean_consequence_lattice")},sort_keys=True))

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: g2_finite_composition_audit_v1.py EVIDENCE_ROOT")
    main(Path(sys.argv[1]))
