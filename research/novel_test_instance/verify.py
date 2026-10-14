#!/usr/bin/env python3
"""Native original-Go qualification for a SOURCE-INFERRED new regex test input.

The executable test function and map key are derived by Go AST from original
source changes. Only test files are modified; no upstream repositories written.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, subprocess, time

def guard(ok,code):
    if not ok:raise AssertionError(code)

def sha(root):
    z=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],
        capture_output=True,text=True,check=True)
    return z.stdout.strip()

def changed(root):
    out=subprocess.run(["git","-C",str(root),"diff","--name-only"],
        capture_output=True,text=True,check=True)
    return out.stdout.splitlines()

def run(root, testname, label):
    cmd=["go","test","-count=1","-json","-run","^"+testname+"$","-timeout=3m","."]
    t0=time.perf_counter()
    try:
        r=subprocess.run(cmd,cwd=root,capture_output=True,text=True,
            timeout=230,check=False)
    except subprocess.TimeoutExpired:
        return {"label":label,"status":"TIMEOUT_UNKNOWN",
            "seconds":round(time.perf_counter()-t0,3)}
    events=[]
    for line in r.stdout.splitlines():
        try: events.append(json.loads(line))
        except json.JSONDecodeError: continue
    actions=[x.get("Action") for x in events if x.get("Test")==testname]
    failure_lines=[x.get("Output","").strip() for x in events
         if x.get("Test")==testname and
           ("Index:" in x.get("Output","") or "failed Error:" in x.get("Output","")
              or "validator_test.go:" in x.get("Output",""))]
    return {
      "label":label,
      "status":"EXECUTED" if "run" in actions else "NOT_EXECUTED",
      "exit":r.returncode,
      "actions":actions,
      "seconds":round(time.perf_counter()-t0,3),
      "stdout_sha256":hashlib.sha256(r.stdout.encode()).hexdigest(),
      "stderr_tail":r.stderr[-750:],
      "failure_samples":failure_lines[:6]
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=pathlib.Path,required=True)
    p.add_argument("--base",type=pathlib.Path,required=True)
    p.add_argument("--head",type=pathlib.Path,required=True)
    p.add_argument("--negative",type=pathlib.Path,required=True)
    p.add_argument("--pristine",type=pathlib.Path,required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    a=p.parse_args()
    doc=json.loads(a.manifest.read_text())
    guard(doc.get("schema")=="metalogic.source-diff-derived-new-regex-assertion.v1","MANIFEST_SCHEMA")
    test=doc["discovery"]["test_function"]
    file=doc["discovery"]["test_file"]
    guard(test.startswith("Test") and file.endswith("_test.go"),"SELECTED_TEST_SCOPE_INVALID")
    for root in (a.base,a.pristine):guard(sha(root)==doc["base_sha"],"BASE_PIN_WRONG")
    for root in (a.head,a.negative):guard(sha(root)==doc["head_sha"],"HEAD_PIN_WRONG")
    for root in (a.base,a.head,a.negative):
        guard(changed(root)==[file],"NON_TEST_SOURCE_MUTATED")
    guard(changed(a.pristine)==[],"PRISTINE_SOURCE_NOT_CLEAN")
    observed={}
    for label,root in [("base_plus_new_assertion",a.base),
                       ("fixed_head_plus_new_assertion",a.head),
                       ("fixed_head_plus_intentionally_false_assertion",a.negative),
                       ("pristine_base_ablation",a.pristine)]:
        z=run(root,test,label)
        observed[label]=z
        print("GENERATED_NATIVE_ARM "+json.dumps({
          "label":label,"status":z["status"],"exit":z.get("exit"),
          "actions":z.get("actions"),"seconds":z["seconds"],
          "failure_samples":z.get("failure_samples")}))
    base=observed["base_plus_new_assertion"]
    head=observed["fixed_head_plus_new_assertion"]
    negative=observed["fixed_head_plus_intentionally_false_assertion"]
    pristine=observed["pristine_base_ablation"]
    red=lambda x:x["status"]=="EXECUTED" and x["exit"]!=0 and "fail" in x["actions"] and bool(x["failure_samples"])
    green=lambda x:x["status"]=="EXECUTED" and x["exit"]==0 and "pass" in x["actions"]
    result=("WARRANTED_BOUNDED_NEW_SOURCE_DERIVED_NATIVE_ASSERTION"
           if red(base) and green(head) and red(negative) and green(pristine)
           else "UNKNOWN_OR_FAILED_NATIVE_NEW_ASSERTION")
    report={
      "schema":"metalogic.original-go.source-derived-new-executable-assertion-result.v1",
      "result":result,
      "source":doc,
      "native_arms":observed,
      "generated_input_not_present_in_original_author_tests":True,
      "old_vs_new_regexp_delta_in_source":True,
      "no_manual_test_name_or_target_input_manifest":True,
      "oracle_source":"CONTRIBUTOR_HEAD_REGEXP_OLD_VS_NEW_SOURCE_CODE; NOT_EXTERNAL_INDEPENDENT_SPEC",
      "native_application_test_harness":"UPSTREAM_AUTHOR_WRITTEN_ORIGINAL",
      "generator_algorithm":"HUMAN_CODED_RE2_DIFFERENCE_PLUS_GENERIC_GO_AST_ACTIVATION",
      "time_and_cost_measurement":"NATIVE_PROCESS_WALLTIME_ONLY_NO_HUMAN_REVIEW_TIMING",
      "fair_baseline":"COMPETENT_REVIEWER_WITH_SAME_PR_SOURCE_CAN_RUN_SAME_GENERATOR",
      "action_authorization":"NONE",
      "autonomous_method_self_invention":"NOT_PROVEN",
      "nonclaims":["No new bug discovered; upstream fixed historical case",
                   "No independent reference oracle beyond original source regex",
                   "No universal validator correctness or general semantic theorem",
                   "No evidence of customer adoption or L7 autonomous generator"]
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("GENERATED_ASSERTION_FINAL "+json.dumps({
       "verdict":result,"test_operation":test,
       "new_input":doc["discovery"]["new_witness"],
       "old_source_base_rejected":red(base),"fixed_head_accepted":green(head),
       "false_head_control_rejected":red(negative),
       "pristine_original_green":green(pristine)}))
    guard(result=="WARRANTED_BOUNDED_NEW_SOURCE_DERIVED_NATIVE_ASSERTION",
          "GENERATED_ASSERTION_NATIVE_GATE_FAILED")
if __name__=="__main__":
    main()
