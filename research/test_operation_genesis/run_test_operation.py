#!/usr/bin/env python3
"""Execute auto-discovered (not hard-coded) Go tests at original predecessor and author head."""
from __future__ import annotations
import argparse,json,pathlib,re,subprocess,time,hashlib,sys
def check(ok,msg):
    if not ok:raise RuntimeError(msg)
def gitrev(path):
    r=subprocess.run(["git","-C",str(path),"rev-parse","HEAD"],text=True,capture_output=True,check=True)
    return r.stdout.strip()
def run(package, names, workdir):
    escaped="|".join(re.escape(n) for n in names)
    cmd=["go","test","-json","-count=1","-timeout=5m","-run",f"^({escaped})$",package]
    st=time.perf_counter()
    try:
        run=subprocess.run(cmd,cwd=workdir,text=True,stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,check=False,timeout=360)
    except subprocess.TimeoutExpired:
        return {"status":"TIMEOUT_UNKNOWN","elapsed_s":round(time.perf_counter()-st,3)}
    events=[]
    for line in run.stdout.splitlines():
        try:x=json.loads(line)
        except json.JSONDecodeError:continue
        events.append(x)
    statuses={}
    for name in names:
        status=[e for e in events if e.get("Test")==name and e.get("Action") in ("run","pass","fail","skip")]
        statuses[name]=[e.get("Action") for e in status]
    # A red must fail INSIDE an original Go testing function, not compilation/import/setup.
    original_fails=[n for n in names if "run" in statuses[n] and "fail" in statuses[n]]
    original_passes=[n for n in names if "run" in statuses[n] and "pass" in statuses[n]]
    assertion_events=[e.get("Output","") for e in events
                      if any(e.get("Test","")==n or e.get("Test","").startswith(n+"/") for n in original_fails) and
                      (re.search(r"\.go:[0-9]+:",e.get("Output","")) or
                       re.search(r"\b(?:got|want|mismatch)\b",e.get("Output","")))]
    return {"status":"COMPLETE" if all("run" in actions for actions in statuses.values()) else "TEST_DISCOVERY_INCOMPLETE",
            "exit":run.returncode,"elapsed_s":round(time.perf_counter()-st,3),
            "selected":statuses,"fail_names":original_fails,"pass_names":original_passes,
            "test_assertion_events":assertion_events[:24],
            "json_test_stdout_sha256":hashlib.sha256(run.stdout.encode()).hexdigest(),
            "stderr_tail":run.stderr[-750:],
            "invocation":["go","test","-json","-count=1","-timeout=5m","-run",f"^({escaped})$",package]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=pathlib.Path,required=True)
    p.add_argument("--base",type=pathlib.Path,required=True)
    p.add_argument("--head",type=pathlib.Path,required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    p.add_argument("--pristine",type=pathlib.Path)
    p.add_argument("--ablate",action="store_true")
    p.add_argument("--withdraw",action="store_true")
    a=p.parse_args()
    m=json.loads(a.manifest.read_text())
    check(m["schema"]=="metalogic.original-go-source-test-operation-extraction.v1","MANIFEST_SCHEMA_WRONG")
    check(gitrev(a.base)==m["base_sha"] and gitrev(a.head)==m["head_sha"],"SOURCE_PIN_MISMATCH")
    check(m.get("source_test_patch_only") is True,"IMPLEMENTATION_PATCH_LAUNDERED")
    selected=m["selected"]
    ablation_observations={}
    if a.ablate:
        check(a.pristine is not None and gitrev(a.pristine)==m["base_sha"],
              "PRISTINE_SOURCE_IDENTITY_NOT_QUALIFIED")
        status=subprocess.run(["git","-C",str(a.pristine),"status","--porcelain"],
                              text=True,capture_output=True,check=True)
        check(not status.stdout.strip(),"PRISTINE_BASE_NOT_CLEAN")
        packageGroups={}
        for entry in selected:packageGroups.setdefault(entry["package"],[]).append(entry["function"])
        for package,names in sorted(packageGroups.items()):
            ablation_observations[package]=run(package,names,a.pristine)
            record=ablation_observations[package]
            check(record["exit"]==0 and record["status"]=="TEST_DISCOVERY_INCOMPLETE" and
                  not record["fail_names"] and not record["pass_names"] and
                  all(not v for v in record["selected"].values()),
                  "ABLATION_STILL_EXECUTED_QUALIFYING_TEST")
        verdict="UNKNOWN_REQUIRED_TEST_OPERATION_REMOVED"
    elif a.withdraw: verdict="STALE_EVIDENCE_WITHDRAWN"
    elif not selected:verdict="UNKNOWN_NO_TEST_FUNCTION_EXTRACTED"
    else:verdict=None
    records={}
    if verdict is None:
        packageGroups={}
        for entry in selected:packageGroups.setdefault(entry["package"],[]).append(entry["function"])
        for package,names in sorted(packageGroups.items()):
            records[package]={"base":run(package,names,a.base),"head":run(package,names,a.head)}
        failures=any(rec["base"]["fail_names"] and rec["base"]["test_assertion_events"] and
                     rec["head"]["exit"]==0 and
                     set(rec["head"]["pass_names"])==set(packageGroups[pkg]) and
                     rec["base"]["status"]==rec["head"]["status"]=="COMPLETE"
                     for pkg,rec in records.items())
        all_head_good=all(rec["head"]["exit"]==0 and
                          set(rec["head"]["pass_names"])==set(packageGroups[pkg])
                          for pkg,rec in records.items())
        any_setup_failure=any(rec["base"]["status"]!="COMPLETE" or rec["head"]["status"]!="COMPLETE"
                              for rec in records.values())
        if any_setup_failure:verdict="UNKNOWN_GO_TEST_SETUP_OR_EXTRACTION"
        elif failures and all_head_good:verdict="WARRANTED_BOUNDED_ORIGINAL_AUTHORED_TEST_RED_BASE_GREEN_HEAD"
        else:verdict="NO_QUALIFIED_SOURCE_NATIVE_FAILURE_TO_SUCCESS"
    result={
      "schema":"metalogic.source-derived-native-test-operation-result.v1",
      "third_original_repo":m["repo"],"base_sha":m["base_sha"],"head_sha":m["head_sha"],
      "result":verdict,"selection":selected,"native_test_records":records,
      "causal_no_added_test_run":ablation_observations,
      "generated_test_source":False,"selection_derived_from_go_ast_diff":True,
      "source_test_patch_only":True,"action_authorization":"NONE",
      "baseline":{
        "fully_informed_reviewer_given_same_PR_diff_and_Go_toolchain":
           "CAN_DISCOVER_AND_RUN_THE_SAME_AUTHOR_TESTS",
        "measured_time_savings":"NOT_MEASURED",
        "new_independent_unknown_bug_found":"NO",
        "automatic_operation_invention":"NOT_SHOWN"},
      "nonclaims":["Original author supplied all assertion semantics and fix",
                   "Selector only acquires test activation from original diff",
                   "No target grammar synthesis or generalized source-to-intent truth"]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("GO_SOURCE_GENESIS "+json.dumps({"result":verdict,"selected":[x["function"] for x in selected],
         "packages":list(records),"causal_test_patch_only":True,
         "no_semantic_handwritten_manifest":True,"L7":"UNKNOWN"}))
    if a.ablate:check(verdict=="UNKNOWN_REQUIRED_TEST_OPERATION_REMOVED","BAD_ABLATION")
    elif a.withdraw:check(verdict=="STALE_EVIDENCE_WITHDRAWN","BAD_WITHDRAWAL")
    else:check(verdict=="WARRANTED_BOUNDED_ORIGINAL_AUTHORED_TEST_RED_BASE_GREEN_HEAD",
       "NATIVE_BEFORE_AFTER_NOT_QUALIFIED")
if __name__=="__main__":main()
