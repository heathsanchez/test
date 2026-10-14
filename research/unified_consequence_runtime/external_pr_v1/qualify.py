#!/usr/bin/env python3
"""Independent PR-native regression qualification on original upstream source.

Discovery of new tests is AST-based and independent of test/class names.
The *original PR head* supplies its tests and proposed implementation fix.
The baseline counterfactual substitutes the **original pinned base implementation**
under the same byte-identical PR tests.  Nothing in this program synthesizes
a source-code repair, and no theorem about arbitrary PRs is claimed.

The reusable capability is to identify which existing authored regressions
constitute source-native red(base)->green(head) evidence and preserve all
original source digests, old accepted tests, budgets, and failures.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time


def fail(reason):
    raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+"\n"


def git(root,*args):
    return subprocess.check_output(
        ["git","-C",str(root),*args],text=True
    ).strip()


def verify_repo(root,revision,script_blob,test_blob):
    if git(root,"rev-parse","HEAD")!=revision:
        fail("EXACT_EXTERNAL_REPOSITORY_REVISION_MISMATCH")
    for filename,expected in (("scripts/ieantn.py",script_blob),
                              ("tests/test_ieantn.py",test_blob)):
        actual=git(root,"hash-object",filename)
        if actual!=expected:
            fail("EXTERNAL_NATIVE_SOURCE_BLOB_MISMATCH:"+filename)


def discovered_test_methods(test_source):
    """Read the *existing* original test suite, not PR prose or diff solution."""
    tree=ast.parse(test_source)
    found={}
    for cls in tree.body:
        if isinstance(cls,ast.ClassDef):
            for method in cls.body:
                if isinstance(method,(ast.FunctionDef,ast.AsyncFunctionDef)) and method.name.startswith("test_"):
                    name=cls.name+"."+method.name
                    found[name]=digest(
                        ast.dump(method,annotate_fields=True,include_attributes=False).encode()
                    )
    return found


def discover_new_tests(pristine_source,pr_tests):
    before=discovered_test_methods(pristine_source)
    after=discovered_test_methods(pr_tests)
    introduced=sorted(name for name in after if name not in before)
    changed=sorted(name for name in before if name in after and before[name]!=after[name])
    if changed:
        # Mutating existing tests is not a fresh blind heldout test and must
        # be separately reviewed; do not silently classify it as added.
        fail("MUTATED_PRIOR_PROTECTED_TEST:"+",".join(changed))
    if not introduced:
        fail("UNKNOWN_NO_NEW_NATIVE_REGRESSION_TEST")
    return introduced


def prepare_overlay(out,original_script,head_tests):
    (out/"scripts").mkdir(parents=True,exist_ok=True)
    (out/"tests").mkdir(parents=True,exist_ok=True)
    shutil.copyfile(original_script,out/"scripts"/"ieantn.py")
    shutil.copyfile(head_tests,out/"tests"/"test_ieantn.py")
    return out


def run_unittest(overlay,selectors,timeout):
    command=[sys.executable,"-m","unittest","-v"]+[
        "test_ieantn."+name for name in selectors
    ]
    env=os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"]="1"
    started=time.monotonic()
    try:
        process=subprocess.run(
            command,cwd=overlay/"tests",capture_output=True,text=True,
            timeout=timeout,env=env,check=False)
        ret=process.returncode
        output=process.stdout+process.stderr
    except subprocess.TimeoutExpired:
        ret=124
        output="NATIVE_TEST_TIMEOUT"
    match=re.search(r"Ran\s+(\d+)\s+tests?\b",output)
    return {
        "native_command":"python -m unittest -v <AST-discovered-source-methods>",
        "exit_code":ret,
        "test_count":int(match.group(1)) if match else 0,
        "wall_s":round(time.monotonic()-started,4),
        "output_sha256":digest(output.encode()),
        "test_stdout_stderr_tail":output[-6000:],
    }


def run_full_suite(overlay,timeout):
    command=[sys.executable,"-m","unittest","discover","-s","tests","-p","test_ieantn.py","-v"]
    env=os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"]="1"
    start=time.monotonic()
    try:
        p=subprocess.run(command,cwd=overlay,capture_output=True,text=True,
                         env=env,timeout=timeout,check=False)
        stdout=p.stdout+p.stderr
        ret=p.returncode
    except subprocess.TimeoutExpired:
        stdout="FULL_SUITE_TIMEOUT"
        ret=124
    m=re.search(r"Ran\s+(\d+)\s+tests?\b",stdout)
    return {
        "exit_code":ret,"test_count":int(m.group(1)) if m else 0,
        "wall_s":round(time.monotonic()-start,4),
        "output_sha256":digest(stdout.encode()),
        "stdout_stderr_tail":stdout[-1500:],
    }


def verify_api_metadata(spec,metadata,base):
    if (metadata.get("number")!=spec["pr"] or
        metadata.get("head",{}).get("sha")!=spec["head"] or
        metadata.get("base",{}).get("sha")!=base or
        metadata.get("base",{}).get("repo",{}).get("full_name")!="teorth/IEANTN" or
        metadata.get("head",{}).get("repo",{}).get("full_name")!="teorth/IEANTN"):
        fail("LIVE_EXTERNAL_PR_SOURCE_REVISION_DRIFT")
    # An already merged PR is not forbidden, but a closed/unknown one should
    # not be passed off as currently open for maintainer decision support.
    if metadata.get("state")!="open":
        fail("PR_NOT_CURRENTLY_OPEN")


def run(protocol_path,root_base,roots,metadata_dir,out):
    frozen_raw=protocol_path.read_bytes()
    protocol=json.loads(frozen_raw)
    if protocol["schema"]!="metalogic.external-pr-native-regression.v1":
        fail("UNEXPECTED_PROTOCOL")
    if protocol["upstream"]!="teorth/IEANTN":
        fail("NOT_THE_FROZEN_NATIVE_REPOSITORY")
    base=protocol["common_base"]
    verify_repo(root_base,base,protocol["common_base_blob"],protocol["pristine_test_blob"] if "pristine_test_blob" in protocol else "7a4fb44630145f5d1ba7776867eb14f32ab41ad8")
    old_native_tests=(root_base/"tests/test_ieantn.py").read_text()
    out.mkdir(parents=True,exist_ok=True)
    reports=[]
    for spec in protocol["cases"]:
        pr=str(spec["pr"])
        head=roots/pr
        metadata=json.loads((metadata_dir/(pr+".json")).read_bytes())
        verify_api_metadata(spec,metadata,base)
        verify_repo(head,spec["head"],spec["script_blob"],spec["tests_blob"])
        original_head_tests=(head/"tests/test_ieantn.py").read_text()
        found=discover_new_tests(old_native_tests,original_head_tests)
        # The protocol only checks counts; the discovered selectors are
        # neither hand-authored nor provided as a list of winners.
        if len(found)!=spec["expected_new_tests"]:
            fail("INTRODUCED_TEST_COUNT_CHANGED:"+pr)
        base_overlay=prepare_overlay(
            out/"overlays"/pr/"base",
            root_base/"scripts/ieantn.py",head/"tests/test_ieantn.py")
        head_overlay=prepare_overlay(
            out/"overlays"/pr/"head",
            head/"scripts/ieantn.py",head/"tests/test_ieantn.py")
        # The head test source bytes are identical in both arms;
        # the only intervention is choosing old/new production source.
        tbase=(base_overlay/"tests/test_ieantn.py").read_bytes()
        thead=(head_overlay/"tests/test_ieantn.py").read_bytes()
        if tbase!=thead:
            fail("COUNTERFACTUAL_TEST_FILES_DIVERGED")
        before=run_unittest(base_overlay,found,90)
        after=run_unittest(head_overlay,found,90)
        base_suite=run_full_suite(
            prepare_overlay(out/"full"/pr/"base",
                            root_base/"scripts/ieantn.py",
                            root_base/"tests/test_ieantn.py"),90)
        head_suite=run_full_suite(head_overlay,90)
        qualified=(
            before["exit_code"]!=0 and before["exit_code"]!=124 and
            before["test_count"]==len(found) and
            after["exit_code"]==0 and after["test_count"]==len(found) and
            base_suite["exit_code"]==0 and head_suite["exit_code"]==0 and
            head_suite["test_count"]>=base_suite["test_count"]
        )
        report={
          "pr":spec["pr"],"source":"https://github.com/teorth/IEANTN/pull/"+pr,
          "base_sha":base,"head_sha":spec["head"],
          "original_pr_metadata_sha256":digest((metadata_dir/(pr+".json")).read_bytes()),
          "script_blobs":{"before":protocol["common_base_blob"],"after":spec["script_blob"]},
          "native_tests_blobs":{"original_base":"7a4fb44630145f5d1ba7776867eb14f32ab41ad8",
                                "same_head_tests_both_arms":spec["tests_blob"]},
          "AST_derived_new_test_methods":found,
          "before_source_with_head_tests":before,
          "after_source_with_head_tests":after,
          "old_full_suite_on_base":base_suite,
          "full_suite_on_head":head_suite,
          "result":"WARRANTED_BOUNDED_REAL_PR_NATIVE_REGRESSION" if qualified else "UNKNOWN_NO_QUALIFIED_PR_CAUSAL_SEPARATION",
          "correspondence":"PR authors supplied changed original code and new regression tests; this consumer independently evaluates them. No generated patch is claimed.",
          "source_behavioral_proof":"RED_BASE_GREEN_HEAD_NATIVE_TESTS" if qualified else "UNKNOWN",
          "independent_native_language":"Python stdlib unittest",
          "general_generator_self_invention":"UNKNOWN",
          "application_to_external_owner":"READ_ONLY_NOT_INSTALLED",
        }
        reports.append(report)
        print(f"PR_{pr}="+report["result"]+" introduced="+str(len(found))+
              " base_exit="+str(before["exit_code"])+" head_exit="+str(after["exit_code"]))
    qualified_count=sum(r["result"]=="WARRANTED_BOUNDED_REAL_PR_NATIVE_REGRESSION"
                        for r in reports)
    receipt={
      "schema":"metalogic.real-external-pr-native-evidence.v1",
      "protocol_sha256":digest(frozen_raw),
      "source":"Independent native test replay of unmodified author PR test files",
      "original_external_repo":"teorth/IEANTN",
      "qualified_count":qualified_count,
      "cases":reports,
      "advisory_conclusion":"NEUTRAL_REVIEW_EVIDENCE_ONLY" if qualified_count==len(protocol["cases"]) else "UNKNOWN",
      "evidence_scope":"Exact tests on exact source versions; not an exhaustive source correctness proof",
      "method_generator":"Reusable AST new-test discovery plus source-exact native counterfactual",
      "method_generator_software_authorship":"HUMAN_WRITTEN",
      "code_repair_generated":"NO",
      "new_generator_self_modification":"UNKNOWN",
      "scientific_L7":"UNKNOWN",
      "action_authorization":"NONE"
    }
    (out/"receipt.json").write_text(canonical(receipt))
    (out/"case-summaries.json").write_text(canonical([
        {k:v for k,v in case.items() if k not in (
          "before_source_with_head_tests","after_source_with_head_tests",
          "old_full_suite_on_base","full_suite_on_head"
        )} for case in reports]))
    if qualified_count!=len(reports):
        raise SystemExit("SOURCE_NATIVE_EXTERNAL_PR_EVIDENCE_NOT_QUALIFIED")
    print("PASS_REAL_EXTERNAL_PR_NATIVE_COUNTERFACTUALS="+str(qualified_count))
    print("AUTONOMOUS_REPAIR_METHOD_INVENTION=UNKNOWN")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=pathlib.Path,required=True)
    p.add_argument("--base",type=pathlib.Path,required=True)
    p.add_argument("--head-158",type=pathlib.Path,required=True)
    p.add_argument("--head-155",type=pathlib.Path,required=True)
    p.add_argument("--metadata-dir",type=pathlib.Path,required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    args=p.parse_args()
    run(args.protocol.resolve(),args.base.resolve(),
        {"158":args.head_158.resolve(),"155":args.head_155.resolve()},
        args.metadata_dir.resolve(),args.out.resolve())


if __name__=="__main__":
    main()
