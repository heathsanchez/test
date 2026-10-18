#!/usr/bin/env python3
"""Independent original Git/JUnit/native-scoped method negative for third-source V1.1.

NO imports from the V1/V1.1 experimental method or admission implementation.
No source/test execution. A separate Git checkout of exact original upstream
BASE and contributor HEAD test anchors original source and test reality.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
PROTO="research/unified_consequence_runtime/G2_THIRD_SOURCE_V11_INDEPENDENT_AUDIT_FREEZE.json"
PROTO_COMMIT="c89482bd84b3493d96ec6e72ef2959e397e53158"
SCHEMA="G2_THIRD_SOURCE_V11_INDEPENDENT_ORIGINAL_NATIVE_NEGATIVE_AUDIT"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(work,*args,raw=False,check=True):
    p=subprocess.run(["git","-C",str(work),"--no-replace-objects",*args],
        capture_output=True,check=check,timeout=70)
    return p.stdout if raw else p.stdout.decode().strip()


def manifest():
    current=(ROOT/PROTO).read_bytes()
    old=subprocess.check_output(["git","-C",str(ROOT),"show",
                                 PROTO_COMMIT+":"+PROTO],timeout=40)
    if current!=old:
        raise ValueError("UNKNOWN_INDEPENDENT_AUDIT_PROTOCOL_MUTATED")
    return json.loads(current)


def original_tree(repo,base,head):
    """Read source from pinned Git original, never author-fixed production."""
    with tempfile.TemporaryDirectory(prefix="g2-third-independent-git-") as d:
        work=Path(d)
        git(work,"init","-q")
        git(work,"remote","add","origin","https://github.com/"+repo+".git")
        for commit in (base,head):
            git(work,"fetch","-q","--depth=1","--filter=blob:none",
                "--no-tags","origin",commit)
        paths=git(work,"ls-tree","-r","--name-only",base).splitlines()
        return {
          "tracked":paths,
          "base":base,"head":head,
          "read_base":lambda path:None,
        }


def original_two_source_repos(cfg):
    """Re-fetch both original Git provenance pairs, returning immutable bytes.

    Stage all Git bytes while the temporary original Git repository exists.
    """
    sources={}
    for repo,base,head,production,test in (
        ("psf/requests","7bc45877a86192af77645e156eb3744f95b47dae",
         "92bab7d1142db0c807060577233568e5f7734c9b",
         "src/requests/utils.py","tests/test_utils.py"),
        ("urllib3/urllib3","bcf84e6815f623521e1ffe3e6ab0224d778929c0",
         "4aa45cd210ebb19559d505d73c8d05a541314e2f",
         "src/urllib3/http2/probe.py","test/test_http2_probe.py"),
    ):
        with tempfile.TemporaryDirectory(prefix="g2-third-auditor-") as d:
            work=Path(d)
            git(work,"init","-q")
            git(work,"remote","add","original","https://github.com/"+repo+".git")
            for commit in (base,head):
                git(work,"fetch","-q","--depth=1","--filter=blob:none",
                    "--no-tags","original",commit)
            source=git(work,"show",base+":"+production,raw=True)
            new_test=git(work,"show",head+":"+test,raw=True)
            def mode_for(commit,path):
                line=git(work,"ls-tree",commit,"--",path)
                if not line:return None
                parts=line.split()
                if len(parts)!=4 or parts[-1]!=path or parts[1]!="blob":
                    raise ValueError("UNKNOWN_GIT_MODE_OR_PATH")
                return parts[0]
            actual_mode=mode_for(base,production)
            head_mode=mode_for(head,test)
            base_test=mode_for(base,test)
            if actual_mode not in ("100644","100755") or head_mode not in ("100644","100755"):
                raise ValueError("UNKNOWN_SOURCE_OR_TEST_NOT_REGULAR_GIT")
            if repo=="urllib3/urllib3" and base_test is not None:
                raise ValueError("UNKNOWN_EXPECTED_ORIGINAL_NEW_AUTHOR_TEST_NOT_ACTUALLY_NEW")
            tracked=git(work,"ls-tree","-r","--name-only",base).splitlines()
            sources[repo]={"source":source,"test":new_test,
                           "source_mode":actual_mode,"test_mode":head_mode,
                           "base_test_exists":base_test is not None,
                           "tracked_paths":tracked,
                           "production_path":production,"author_test_path":test}
    return sources


def native_original_test(xml_bytes,expected_case_count,expected_fail_count,fn_prefix):
    root=ET.fromstring(xml_bytes)
    cases=list(root.iter("testcase"))
    if len(cases)!=expected_case_count:
        raise ValueError("UNKNOWN_JUNIT_CASE_COUNT")
    fail=0
    name_ids=[]
    for node in cases:
        name=node.get("name","");classname=node.get("classname","")
        if not name or not classname:
            raise ValueError("UNKNOWN_JUNIT_CASE_ID")
        if any(child.tag not in ("failure",) for child in list(node)):
            raise ValueError("UNKNOWN_JUNIT_ERRORS_SKIPS_OR_XFAIL")
        if fn_prefix not in name:
            raise ValueError("UNKNOWN_PROTECTED_AUTHOR_TEST_NAME")
        fail+=int(any(c.tag=="failure" for c in node))
        name_ids.append(classname+"::"+name)
    if fail!=expected_fail_count or len(set(name_ids))!=len(name_ids):
        raise ValueError("UNKNOWN_JUNIT_INCONSISTENT_FAILURE_VECTOR")
    return {"cases":len(cases),"passed":len(cases)-fail,"failed":fail,
            "case_ids":sorted(name_ids)}


def independent_scope(test_bytes,tracked,declared_production):
    """Recreate frozen source-neutral AST import projection without producer."""
    tree=ast.parse(test_bytes)
    imported=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            imported.update(alias.name for alias in node.names)
        if isinstance(node,ast.ImportFrom) and node.level==0 and node.module:
            imported.add(node.module)
    scope={declared_production}
    for module in sorted(imported):
        parts=module.split(".")
        if len(parts)<2 or parts[0] in sys.stdlib_module_names:
            continue
        if not all(part.isidentifier() for part in parts):
            continue
        suffix=parts[:-1]+[parts[-1]+".py"]
        candidates=[p for p in tracked
                    if p.endswith(".py") and
                    len(p.split("/"))>=len(suffix) and
                    p.split("/")[-len(suffix):]==suffix]
        if len(candidates)>1:
            raise ValueError("UNKNOWN_AMBIGUOUS_SOURCE_IMPORT")
        if candidates:
            scope.add(candidates[0])
    if len(scope)>8:
        raise ValueError("UNKNOWN_SOURCE_IMPORT_SCOPE_ABOVE_FROZEN_CAP")
    return sorted(scope)


def independent_strict_candidates(source_bytes):
    """Recognize ONLY source-neutral originally admitted strict regex AST sites."""
    src=source_bytes.decode("utf-8")
    tree=ast.parse(src)
    found=[]
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call) or not node.args:
            continue
        callee=node.func
        if not (isinstance(callee,ast.Attribute)
                and isinstance(callee.value,ast.Name)
                and callee.value.id=="re" and
                callee.attr in ("compile","match","search")):
            continue
        arg=node.args[0]
        if not isinstance(arg,ast.Constant) or not isinstance(arg.value,str):
            continue
        literal=ast.get_source_segment(src,arg)
        if not (literal and len(literal)>=4 and
                literal[0] in ("r","R") and literal[1] in ("'",'"')
                and literal[-1]==literal[1] and literal[-2]=="$"):
            continue
        if (len(arg.value[:-1])-len(arg.value[:-1].rstrip("\\")))%2:
            continue
        found.append({"line":arg.lineno,"kind":"strict_terminal_anchor"})
    return found


def audit(folder,originals):
    folder=Path(folder)
    cfg=manifest();goal=cfg["expected"]
    r=json.loads((folder/"RESULT.json").read_text())
    if (r.get("schema")!="G2_FROZEN_THIRD_SOURCE_REAL_NATIVE_FINITE_TRANSFER_V1"
            or r.get("status")!=goal["status"]
            or r.get("eligible")!=goal["second"]
            or any(r.get(k)!="UNKNOWN" for k in ("G2","G4"))
            or r.get("natives_after_admission")!=0
            or r.get("primitive_count")!=0
            or r.get("actual_agent")!="NOT_EXECUTED"
            or r.get("matched_ledger")!="NO_CANDIDATES_IN_EQUAL_INFO_UNIVERSE"):
        raise ValueError("UNAUTHORIZED_SCIENCE_OR_CANDIDATE_STATUS")
    if len(r.get("source_outcomes",[]))!=2:
        raise ValueError("UNKNOWN_FROZEN_SOURCE_FIRST_FAIL_ORDER")
    first,second=r["source_outcomes"]
    if (first.get("repo")!="psf/requests" or first.get("status")!="NOT_ELIGIBLE_NO_PROTECTED_FAILURE"
            or second.get("repo")!="urllib3/urllib3" or
            second.get("status")!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE" or
            second.get("author_test_kind")!="AUTHOR_HEAD_ADDED_TEST"):
        raise ValueError("UNKNOWN_SOURCE_ADMISSION_OR_ORIGINAL_AUTHOR_NEW_TEST")
    requests=originals["psf/requests"]
    urllib=originals["urllib3/urllib3"]
    for row,src in ((first,requests),(second,urllib)):
        if row["source_sha256"]!=digest(src["source"]) or row["head_test_sha256"]!=digest(src["test"]):
            raise ValueError("UNKNOWN_ORIGINAL_GIT_SOURCE_OR_AUTHOR_HEAD_TEST_HASH")
    if (second["source_sha256"]!=goal["source_sha256"] or
            second["head_test_sha256"]!=goal["author_test_sha256"]):
        raise ValueError("UNKNOWN_PRECOMMITTED_SOURCE_IDENTITY")
    first_xml=(folder/"admission-00/native.xml").read_bytes()
    first_native=native_original_test(first_xml,2,0,"test_")
    second_xml=(folder/"admission-01/native.xml").read_bytes()
    if digest(second_xml)!=goal["original_native_junit_sha256"]:
        raise ValueError("UNKNOWN_NATIVE_ORIGINAL_JUNIT_TAMPER")
    second_native=native_original_test(second_xml,1,1,goal["protected_case"])
    if ("release" not in second_xml.decode(errors="replace")):
        raise ValueError("UNKNOWN_ORIGINAL_PROTECTED_FAILURE_SEMANTIC_RECEIPT")
    for row,rec in ((first,first_native),(second,second_native)):
        c=row["native"]["counts"]
        if c!={"tests":rec["cases"],"failures":rec["failed"],"errors":0,"skipped":0}:
            raise ValueError("UNKNOWN_ORIGINAL_RECEIPT_JUNIT_COUNT_MISMATCH")
    expect_source=goal["source_file"]
    if (r.get("original_native",{}).get("protected_cases")!=1
            or r["original_native"]["failed"]!=1
            or r["original_native"]["junit_sha256"]!=digest(second_xml)):
        raise ValueError("UNKNOWN_ORIGINAL_NATIVE_SOURCE_REPORTED_WRONG")
    computed=independent_scope(urllib["test"],urllib["tracked_paths"],expect_source)
    if computed!=goal["method_scope_files"] or (
         sorted(r.get("scope",{}).get("files",[]))!=computed):
        raise ValueError("UNKNOWN_FROZEN_ORIGINAL_SOURCE_SCOPE_NOT_REPLAYABLE")
    if any(r["scope"]["source_sha256"][s]!=digest(urllib["source"])
           for s in computed if s==expect_source):
        raise ValueError("UNKNOWN_SOURCE_SCOPE_DIGEST")
    candidates=independent_strict_candidates(urllib["source"])
    if candidates:
        raise ValueError("UNKNOWN_PROSPECTIVE_SOURCE_HAS_APPLICABLE_STRICT_OPERATOR")
    if ((folder/"CANDIDATES_BEFORE_NATIVE.json").exists() or
            any(f.name.startswith("mask-") or f.name.startswith("candidate-")
                for f in folder.iterdir())):
        raise ValueError("UNKNOWN_PROPOSED_NATIVE_OUTCOME_SHOULD_NOT_HAVE_RUN")
    if any(x["repo"]=="pydantic/pydantic" for x in r["source_outcomes"]):
        raise ValueError("UNKNOWN_FUTURE_SOURCE_OPENED_AFTER_FIRST_NATIVE_FAIL")
    return {
        "schema":SCHEMA,
        "status":"WARRANTED_BOUNDED_FIRST_REAL_NATIVE_FAIL_AND_FROZEN_METHOD_INAPPLICABILITY",
        "G2":"UNKNOWN","G4":"UNKNOWN","source":"urllib3/urllib3#5254",
        "original_production_sha256":digest(urllib["source"]),
        "head_author_new_test_sha256":digest(urllib["test"]),
        "first_requests_author_native":first_native,
        "second_urllib3_author_native":second_native,
        "original_author_test_new_in_base":not urllib["base_test_exists"],
        "source_scope":computed,"independent_eligible_strict_primitive_count":0,
        "candidate_native_repairs":0,
        "ledger":"SAME_ZERO_CANDIDATE_UNIVERSE_NO_COMPARATOR_RACE",
        "native_source_truth":"ORIGINAL_GIT_PRODUCTION_PLUS_HEAD_AUTHOR_TEST",
        "remaining_candidate_not_reopened_in_v11":"pydantic/pydantic#13980",
        "remaining_candidate_globally_unopened":False,
        "prior_v1_attempt":"Pydantic original source/test already accessed in V1 but zero native collected; do not treat it as untouched",
        "method_transfer":"REJECTED_FROZEN_GRAMMAR_INAPPLICABLE_NOT_UNIVERSAL_FAILURE",
        "future_scope":"ONE_AUTHENTIC_ORIGINAL_SOURCE_DISTINCT_TASK_ONLY"}


if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python -m research.unified_consequence_runtime.g2_third_v11_independent_native_negative_audit ORIGINAL_ARCHIVE_EXTRACT_DIR")
    folder=Path(sys.argv[1]).resolve(strict=True)
    result=audit(folder,original_two_source_repos(manifest()))
    dest=folder/"INDEPENDENT_AUDIT.json"
    if dest.exists():
        raise SystemExit("REFUSE_OVERWRITE_EXISTING_INDEPENDENT_AUDIT")
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:result[k] for k in ("status","source","independent_eligible_strict_primitive_count","G2","G4")},sort_keys=True))
