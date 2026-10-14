#!/usr/bin/env python3
"""Held-out native Go source grammar and gocheck test-data dependency replay.

No per-paper/per-PR test names, field names, or patched implementations.
All original source revisions, Go blobs, and PR metadata are frozen first.
General grammar implementation itself is HUMAN-AUTHORED after protocol freeze.
"""
from __future__ import annotations
import hashlib,json,pathlib,re,os,sys,subprocess,shutil,time

HERE=pathlib.Path(__file__).resolve().parent
COORD=HERE.parents[1]
WORK=COORD.parent
OUT=HERE/"evidence"
OUT.mkdir(parents=True,exist_ok=True)
PROTOCOL=HERE/"FROZEN_PROTOCOL.json"
REPORT={"schema":"mathgraph.go-yaml-test-table-closure.v1",
        "status":"UNKNOWN","cases":[],"error":None}
DEPENDENCY_MODFILE=None

def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def run(argv,cwd,timeout=400,envextra=None,expected_method=None):
    env=os.environ.copy()
    env.update({"GOTOOLCHAIN":"local"})
    if argv and len(argv)>1 and argv[0]=="go" and argv[1]=="test" and DEPENDENCY_MODFILE is not None:
        env["GOFLAGS"]="-modfile="+str(DEPENDENCY_MODFILE)
    if envextra:env.update(envextra)
    t=time.monotonic()
    try:
        p=subprocess.run(argv,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     text=True,errors="replace",timeout=timeout,env=env)
        ret=p.returncode;output=p.stdout
    except subprocess.TimeoutExpired as exc:
        ret=124;output="TIMEOUT "+str(exc)
    result={"argv":argv,"exit_code":ret,"wall_s":round(time.monotonic()-t,3),
       "output_sha256":sha(output.encode()),"output_tail":output[-4000:]}
    if expected_method:
        exact=re.compile(r"(?m)^(PASS|FAIL):[^\n]*\b"+re.escape(expected_method)+r"\b")
        observed=exact.search(output)
        result["native_method_observed"]=bool(observed)
        result["native_method_result"]=observed.group(1) if observed else "NO_METHOD_OBSERVED"
        result["actual_gocheck_output"]=bool(re.search(r"(?m)^(PASS|FAIL):",output))
    return result
def check_git(root,commit,files):
    def g(*args):
        p=run(["git",*args],root,25)
        if p["exit_code"]!=0:raise ValueError("ORIGINAL_GIT_CHECK_FAILURE")
        return p["output_tail"].strip()
    if g("rev-parse","HEAD")!=commit:raise ValueError("ORIGINAL_REPOSITORY_HEAD_NOT_PINNED")
    for path,blob in files.items():
        if g("hash-object",path)!=blob:raise ValueError("ORIGINAL_SOURCE_BLOB_NOT_PINNED:"+path)
def copytree(base,path):
    shutil.copytree(base,path,ignore=shutil.ignore_patterns(".git"),dirs_exist_ok=False)
def original_scope_obstruction(spec,base,head,old_executable):
    seen=[]
    for file in (v["path"] for v in spec["files"] if v["role"]=="native_test"):
        p=run([str(old_executable),str(base/file),str(head/file),file],HERE,45)
        v=json.loads(p["output_tail"])
        if not(p["exit_code"]==1 and v["status"]=="UNKNOWN_NO_NATIVE_TEST_SCOPE_DIFFERENCE"
           and not v["scopes"]):
            raise ValueError("OLD_GO_GENERATOR_NOT_FOUND_TO_FAIL_CLOSED")
        seen.append({"file":file,"verdict":"UNKNOWN_NO_NATIVE_TEST_SCOPE_DIFFERENCE"})
    return seen
def construct_scopes(exe,base,head,testfile):
    cmd=[str(exe),str(base/testfile),str(head/testfile),
         testfile,str(base/"go.mod")]
    p=subprocess.run(cmd,cwd=HERE,capture_output=True,text=True,timeout=45)
    if p.returncode!=0:
        raise ValueError("NEW_METHOD_PLAN_OBSTRUCTION:"+p.stdout[-750:]+p.stderr[-450:])
    value=json.loads(p.stdout)
    if (value.get("schema")!="mathgraph.go-ast-test-table-receiver-plan.v1"
        or value.get("status")!="CANDIDATE_NEEDS_NATIVE_VERIFIER"
        or not value.get("generated_method_ir")):
        raise ValueError("NO_REACHABLE_TYPED_RECEIVER_TEST")
    if not value.get("changed_original_global_tables"):
        raise ValueError("CHANGED_TEST_DATA_DECLARATION_NOT_FOUND")
    for method in value["generated_method_ir"]:
        if (method.get("test_file")!=testfile
           or method.get("acquired_operator")!="ACQUIRE_GO_GLOBAL_TABLE_TO_RECEIVER_TEST"
           or not method.get("discovered_test_method","").startswith("Test")
           or method.get("source_table") not in value["changed_original_global_tables"]
           or method.get("native_command",[None])[0]!="go"):
            raise ValueError("UNQUALIFIED_GENERATED_METHOD_IR")
    return value

def main():
    raw=PROTOCOL.read_bytes()
    p=json.loads(raw)
    if p["schema"]!="mathgraph.native-method-grammar-gap.go-check-tables.v1":
        raise ValueError("WRONG_FROZEN_PROTOCOL")
    source=p["upstream"];base=WORK/"base-go-yaml"
    pinned={"go.mod":source["go_mod_blob"]}
    for case in source["cases"]:
        for entry in case["files"]:pinned[entry["path"]]=entry["base_blob"]
    check_git(base,source["base"],pinned)
    # Historical source has no complete Go sum/modern go directive.
    # Isolate toolchain normalization in an ALTERNATE external module file.
    # Both original and proposed revision are compiled under the SAME
    # normalized dependency graph; never modify publisher go.mod/go.sum.
    global DEPENDENCY_MODFILE
    DEPENDENCY_MODFILE=OUT/"source-preserved-dependencies.mod"
    DEPENDENCY_MODFILE.write_bytes((base/"go.mod").read_bytes())
    tidy=run(["go","mod","tidy","-modfile="+str(DEPENDENCY_MODFILE)],base,150)
    if tidy["exit_code"]!=0:
        raise ValueError("ALTERNATE_DEPENDENCY_NORMALIZATION_FAILED:"+tidy["output_tail"])
    check_git(base,source["base"],{"go.mod":source["go_mod_blob"]})
    REPORT["dependency_context"]={
       "method":"go mod tidy -modfile=SOURCE_EXTERNAL_ALTERNATE",
       "source_publisher_go_mod_unchanged":True,
       "normalized_alternate_mod_sha256":sha(DEPENDENCY_MODFILE.read_bytes()),
       "normalized_alternate_sum_sha256":sha(
             DEPENDENCY_MODFILE.with_suffix(".sum").read_bytes())
          if DEPENDENCY_MODFILE.with_suffix(".sum").exists() else "UNKNOWN",
       "no_original_publishers_source_modification":True}
    from_old=COORD/"research/mathgraph_go_yaml_transfer/discover_go_test_scopes.go"
    old_binary=OUT/"old-method-generator"
    new_binary=OUT/"new-table-method-generator"
    for path,target in [(from_old,old_binary),
                        (HERE/"construct_table_test_ir.go",new_binary)]:
        compiled=run(["go","build","-o",str(target),str(path)],COORD,90,{"GO111MODULE":"off"})
        if compiled["exit_code"]!=0:
            raise ValueError("NATIVE_SELECTOR_DID_NOT_COMPILE:"+str(path)+compiled["output_tail"])
    REPORT["old_generator_original_source_sha256"]=sha(from_old.read_bytes())
    REPORT["new_grammar_generator_is_human_written"]=True
    baseline=run(["go","test","-count=1","-timeout=120s","./..."],base,480)
    REPORT["original_full_native_suite"]=baseline
    if baseline["exit_code"]!=0:
        raise ValueError("OLD_REPOSITORY_FULL_GO_SUITE_NOT_GREEN")
    for case in source["cases"]:
        pr=case["pr"];head=WORK/("head-go-yaml-"+str(pr))
        check_git(head,case["head"],{z["path"]:z["head_blob"] for z in case["files"]})
        original_metadata=json.loads((WORK/"metadata"/(str(pr)+".json")).read_text())
        if (original_metadata.get("number")!=pr
            or original_metadata.get("state")!="open"
            or original_metadata.get("head",{}).get("sha")!=case["head"]
            or original_metadata.get("base",{}).get("sha")!=source["base"]):
            raise ValueError("LIVE_GITHUB_ORIGINAL_PR_REVISION_MISMATCH")
        old_results=original_scope_obstruction(case,base,head,old_binary)
        overlay=WORK/("shadow-test-files-pr"+str(pr))
        copytree(base,overlay)
        for entry in case["files"]:
            if entry["role"]!="native_test":continue
            shutil.copyfile(head/entry["path"],overlay/entry["path"])
        for entry in case["files"]:
            if entry["role"]=="production" and (
                overlay/entry["path"]).read_bytes()!=(base/entry["path"]).read_bytes():
                raise ValueError("HEAD_IMPLEMENTATION_CONTAMINATED_OLD_SOURCE")
        method_plans=[]
        for entry in case["files"]:
            if entry["role"]=="native_test":
                method_plans.append(construct_scopes(new_binary,base,head,entry["path"]))
        seen=set();methods=[]
        for plan in method_plans:
            for test in plan["generated_method_ir"]:
                name=test["discovered_test_method"]
                # A method using two changed tables is ONE evidence test.
                if name in seen:continue
                seen.add(name);methods.append(test)
        before=[];after=[]
        for method in methods:
            cmd=method["native_command"]
            name=method["discovered_test_method"]
            a=run(cmd,overlay,330,expected_method=name)
            b=run(cmd,head,330,expected_method=name)
            # Positive must explicitly report PASS for the exact derived
            # gocheck receiver method. Empty selections cannot be green.
            a["native_failed_assertion"]=(a["exit_code"] not in (0,124) and
              a["native_method_result"]=="FAIL")
            b["native_pass"]=(b["exit_code"]==0 and
              b["native_method_result"]=="PASS")
            before.append(a);after.append(b)
        full_head=run(["go","test","-count=1","-timeout=120s","./..."],head,480)
        full_overlay=run(["go","test","-count=1","-timeout=120s","./..."],overlay,480)
        pass_current=all(y["native_pass"] for y in after)
        true_counterfactual=any(x["native_failed_assertion"] for x in before)
        success=(pass_current and true_counterfactual
             and full_head["exit_code"]==0
             and full_overlay["exit_code"] not in (0,124))
        entry={"pr":pr,"source":"https://github.com/go-yaml/yaml/pull/"+str(pr),
           "base":source["base"],"head":case["head"],
           "old_grammar_protected_obstruction":old_results,
           "automatic_new_native_method_plans":method_plans,
           "selected_receivers_unique":sorted(seen),
           "old_source_plus_head_original_test_data":before,
           "original_pr_head_plus_same_test_data":after,
           "full_original_plus_head_test_data":full_overlay,
           "full_new_source_native_suite":full_head,
           "generator_source_human_authored_after_freeze":True,
           "original_PR_fix_and_tests_external_authors":True,
           "generated_new_test_plan_IR":True,
           "generated_implementation_fix":False,
           "E2E_SYSTEM_L7":"UNKNOWN",
           "verdict":"WARRANTED_BOUNDED_GO_TABLE_RECEIVER_TEST_CLOSURE" if success
             else "UNKNOWN_NATIVE_GO_TABLE_RECEIVER_BEHAVIOR"}
        REPORT["cases"].append(entry)
        print("PR_"+str(pr)+"_VERDICT="+entry["verdict"]+
              " scopes="+",".join(sorted(seen))+
              " native_failed="+str(sum(x["native_failed_assertion"] for x in before))+
              " native_pass="+str(sum(x["native_pass"] for x in after)),flush=True)
    REPORT["status"]="WARRANTED_BOUNDED_NATIVE_GO_CHECK_TABLE_METHOD_TRANSFER" if all(
            a["verdict"].startswith("WARRANTED") for a in REPORT["cases"]) else "UNKNOWN_NATIVE_TABLE_TRANSFER"
    REPORT["original_source_repository"]="go-yaml/yaml"
    REPORT["frozen_protocol_sha256"]=sha(raw)
    REPORT["status_notes"]="No self-writing generator, no preseeded tests/tables, no external code changes"
    REPORT["E2E_SYSTEM_L7"]="UNKNOWN"
    REPORT["outside_owner_product_operation"]=False
    if not REPORT["status"].startswith("WARRANTED"):
        raise ValueError("NOT_ALL_ORIGINAL_GO_TABLE_REVISIONS_SEPARATED")
def write():
    (OUT/"table_transfer_report.json").write_text(json.dumps(REPORT,indent=2,sort_keys=True)+"\n")
    print("FINAL="+REPORT["status"],flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        REPORT["error"]=str(exc)
        REPORT["status"]="UNKNOWN_QUALIFICATION_FAILED"
        print("NAMED_NATIVE_RESIDUAL="+str(exc),file=sys.stderr,flush=True)
        write();sys.exit(1)
    else:write()
