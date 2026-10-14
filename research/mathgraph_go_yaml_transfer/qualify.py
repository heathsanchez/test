#!/usr/bin/env python3
"""Go-YAML source-native controlled counterfactual and compiled test-scope discovery.

Native Go test selector IR is constructed from the upstream original Go AST;
no test function name is in FROZEN_PROTOCOL. This runner itself is human-authored.
No external source writes, generated code repairs or formal-source theorem claims.
"""
from __future__ import annotations
import hashlib, json, os, pathlib, re, shutil, subprocess, sys, time

HERE=pathlib.Path(__file__).resolve().parent
COORD=HERE.parents[1]
WORK=COORD.parent
PROTO=HERE/"FROZEN_PROTOCOL.json"
OUT=HERE/"evidence"
OUT.mkdir(parents=True,exist_ok=True)
REPORT={"schema":"mathgraph.go-yaml-native-grammar-transfer.v1",
        "verdict":"UNKNOWN_NOT_YET_QUALIFIED","status":"RUNNING",
        "cases":[],"failed_gate":None}

def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()
def getoutput(argv,cwd,timeout=420,extra_env=None):
    env=os.environ.copy();env["GOTOOLCHAIN"]="local"
    if extra_env:env.update(extra_env)
    t=time.monotonic()
    try:
        p=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,
                         errors="replace",timeout=timeout,env=env)
        output=p.stdout+p.stderr
        code=p.returncode
    except subprocess.TimeoutExpired as e:
        output="TIMEOUT "+str(e);code=124
    return {"argv":argv,"exit_code":code,"wall_seconds":round(time.monotonic()-t,3),
            "output_sha256":digest(output.encode()),"output_tail":output[-4300:]}
def git(root,*args):
    p=getoutput(["git",*args],root,20)
    if p["exit_code"]!=0:raise RuntimeError("GIT_FAILURE:"+str(args)+p["output_tail"])
    return p["output_tail"].strip()
def verify_git(root,sha,files):
    got=git(root,"rev-parse","HEAD")
    if got!=sha:raise ValueError("ORIGINAL_GIT_COMMIT_CHANGED")
    for path,expected in files.items():
        got_blob=git(root,"hash-object",path)
        if got_blob!=expected:
            raise ValueError("ORIGINAL_GIT_BLOB_CHANGED:"+path)
def api_check(case,metadata,base):
    if (metadata.get("number")!=case["pr"] or metadata.get("state")!="open"
       or metadata.get("head",{}).get("sha")!=case["head"]
       or metadata.get("base",{}).get("sha")!=base
       or metadata.get("base",{}).get("repo",{}).get("full_name")!="goccy/go-yaml"):
        raise ValueError("UPSTREAM_PR_HEAD_OR_BASE_MISMATCH")
def original_copy(root,out):
    def skip(path,names):
        return {z for z in names if z in {".git",".cache","__pycache__"}}
    shutil.copytree(root,out,ignore=skip,dirs_exist_ok=False)
def scope_ir(binary,base,head,testpath):
    r=getoutput([str(binary),str(base/testpath),str(head/testpath),testpath],HERE,60)
    if r["exit_code"]!=0:raise ValueError("NATIVE_AST_SCOPE_UNKNOWN:"+r["output_tail"])
    try:v=json.loads(r["output_tail"])
    except ValueError as e:raise ValueError("NATIVE_AST_INVALID_JSON") from e
    if (v.get("status")!="CANDIDATE_NEEDS_NATIVE_BEFORE_AFTER" or
         v.get("schema")!="mathgraph.automatically-derived-native-go-scope-ir.v1" or
         not v.get("scopes")):
        raise ValueError("NATIVE_AST_SCOPE_MISSING")
    return v

def main():
    raw=PROTO.read_bytes()
    frozen=json.loads(raw)
    if frozen.get("schema")!="mathgraph.native-method-grammar-separator.go-yaml.v1":
        raise ValueError("INVALID_FROZEN_PROTOCOL")
    original=frozen["external"]
    base=WORK/"upstream-base"
    verify_git(base,original["base"],{
       "go.mod":original["go_mod_blob"],
       "decode.go":original["cases"][0]["base_source_blob"],
       "decode_test.go":original["cases"][0]["base_test_blob"],
       "parser/parser.go":original["cases"][1]["base_source_blob"],
       "parser/parser_test.go":original["cases"][1]["base_test_blob"]
    })
    # First establish the independently verified old source grammar gap:
    # the existing AST selector only accepts Python unittest ClassDef/Test...
    previous=(COORD/"research/unified_consequence_runtime/external_pr_v1/qualify.py")
    original_git_blob=git(COORD,"hash-object",str(previous))
    if original_git_blob!=frozen["predecessor"]["method_blob"]:
        raise ValueError("OLD_QUALIFIER_SOURCE_CHANGED")
    prior=previous.read_text()
    if not all(t in prior for t in ("import ast","discovered_test_methods","tests/test_ieantn.py")):
        raise ValueError("OLD_QUALIFIER_SOURCE_SCOPE_UNKNOWN")
    REPORT["old_method_grammar"]="UNSUPPORTED_GO_BY_PYTHON_UNITTEST_AST"
    REPORT["old_method_original_blob"]=original_git_blob
    # Go's official parser supplies syntax/name identity; human authored
    # IR constructor code is pre-registered in the FROZEN_PROTOCOL.
    compiler=OUT/"discover-go-native-scope"
    b=getoutput(["go","build","-o",str(compiler),str(HERE/"discover_go_test_scopes.go")],
                COORD,90,{"GO111MODULE":"off"})
    if b["exit_code"]!=0:raise ValueError("NATIVE_GO_AST_GENERATOR_BUILD_FAILED:"+b["output_tail"])
    REPORT["generator_build"]=b
    # Full original native suite: a strong ordinary baseline, not a weak straw man.
    baseline=getoutput(["go","test","-count=1","-timeout=120s","./..."],base,480)
    REPORT["full_original_suite"]=baseline
    if baseline["exit_code"]!=0:
        raise ValueError("ORIGINAL_BASE_NATIVE_SUITE_NOT_GREEN")
    for case in original["cases"]:
        pr=case["pr"]
        head=WORK/("upstream-pr"+str(pr))
        verify_git(head,case["head"],{
           case["source_file"]:case["head_source_blob"],
           case["test_file"]:case["head_test_blob"],
           "go.mod":original["go_mod_blob"]
        })
        md=json.loads((WORK/"metadata"/(str(pr)+".json")).read_text())
        api_check(case,md,original["base"])
        selection=scope_ir(compiler,base,head,case["test_file"])
        expected=case["test_file"]
        # Sanity-check no changed source path or named test target was
        # supplied by human. Native compiler discovered scoped op plan.
        for scope in selection["scopes"]:
            if scope["file"]!=expected:
                raise ValueError("DISCOVERED_TEST_FILE_SOURCE_MISMATCH")
            if scope["package"] not in {".","./parser"}:
                raise ValueError("UNEXPECTED_NATIVE_GO_PACKAGE_SCOPE")
            if scope["mode"] not in {"ACQUIRE_NEW_GO_TEST","REFINE_EXISTING_GO_TEST_SCOPE"}:
                raise ValueError("UNEXPECTED_NATIVE_METHOD_IR")
            if not scope["name"].startswith("Test"):
                raise ValueError("UNSUPPORTED_DISCOVERED_GO_TEST_NAME")
        # Strong independent Go runner introspection confirms native test
        # names; we do not trust the self-report of AST selection alone.
        pkg=selection["scopes"][0]["package"]
        listing=getoutput(["go","test","-list",".",pkg],head,240)
        if listing["exit_code"]!=0:raise ValueError("GO_NATIVE_TEST_LIST_FAILED:"+listing["output_tail"])
        for scope in selection["scopes"]:
            if not re.search(r"(?m)^"+re.escape(scope["name"])+r"$",listing["output_tail"]):
                raise ValueError("NATIVE_RUNNER_DOES_NOT_RECOGNIZE_AST_METHOD:"+scope["name"])
        overlay=WORK/("counterfactual-pr"+str(pr))
        original_copy(base,overlay)
        target=overlay/case["test_file"]
        shutil.copyfile(head/case["test_file"],target)
        if target.read_bytes()!=(head/case["test_file"]).read_bytes():
            raise ValueError("ORIGINAL_HEAD_TEST_BYTES_CHANGED_IN_OVERLAY")
        if (overlay/case["source_file"]).read_bytes()!=(base/case["source_file"]).read_bytes():
            raise ValueError("PR_HEAD_SOURCE_LEAKED_INTO_BASELINE")
        before=[];after=[]
        for scope in selection["scopes"]:
            cmd=scope["native_command"]
            x=getoutput(cmd,overlay,270)
            y=getoutput(cmd,head,270)
            before.append(x);after.append(y)
        # Source-injected before must fail as a REAL Go native test assertion,
        # not just because the compiler or dependencies failed.
        before_expected=all(x["exit_code"] not in (0,124) and
                            re.search(r"--- FAIL: Test",x["output_tail"]) for x in before)
        after_expected=all(y["exit_code"]==0 and "FAIL" not in y["output_tail"]
                           for y in after)
        fully_updated=getoutput(["go","test","-count=1","-timeout=120s","./..."],head,480)
        passed=(before_expected and after_expected and
                fully_updated["exit_code"]==0)
        report={
           "pr":pr,"source":"https://github.com/goccy/go-yaml/pull/"+str(pr),
           "base":original["base"],"head":case["head"],
           "changed_source":case["source_file"],"test_file":case["test_file"],
           "inferred_method_ir":selection,
           "independent_compiler_test_list":listing,
           "counterfactual_base_source_plus_exact_head_tests":before,
           "original_pr_source_plus_exact_head_tests":after,
           "head_full_native_suite":fully_updated,
           "source_scope":"ORIGINAL_GO_TESTS_AND_GO_PARSER",
           "PR_repair_authored_by":"EXTERNAL_CONTRIBUTOR",
           "method_IR_constructed_automatically":True,
           "operator_grammar_source_human_authored":True,
           "new_generator_self_revision":False,
           "verdict":"WARRANTED_BOUNDED_NATIVE_GO_METHOD_IR_AND_CAUSAL_PR_REGRESSION" if passed
             else "UNKNOWN_GO_NATIVE_BEHAVIOR_NOT_SEPARATED"
        }
        REPORT["cases"].append(report)
        print("PR_"+str(pr)+" "+report["verdict"]+" discovered="+
              ",".join(scope["name"] for scope in selection["scopes"]),flush=True)
    REPORT.update({"frozen_protocol_sha256":digest(raw),
       "verdict":"WARRANTED_BOUNDED_GO_NATIVE_METHOD_PLAN_TRANSFER" if all(
          x["verdict"].startswith("WARRANTED") for x in REPORT["cases"])
             else "UNKNOWN_NATIVE_TRANSFER",
       "human_authored_method_generator":True,
       "method_IR_selected_from_predeclared_grammar":True,
       "new_general_generator_operation_self_constructed":False,
       "fixes_generated_by_MathGraph":False,
       "external_maintainer_used_MathGraph_tool":False,
       "app_webhook_live":False,
       "E2E_SYSTEM_L7":"UNKNOWN","authority":"ADVISORY_ONLY"})
    REPORT["status"]="COMPLETE"
    if REPORT["verdict"]!="WARRANTED_BOUNDED_GO_NATIVE_METHOD_PLAN_TRANSFER":
        raise ValueError("NOT_ALL_NEW_NATIVE_GO_PROBLEMS_SEPARATED")
def persist():
    (OUT/"report.json").write_text(json.dumps(REPORT,indent=2,sort_keys=True)+"\n")
    print("FINAL",json.dumps({k:REPORT.get(k) for k in
          ("status","verdict","failed_gate","E2E_SYSTEM_L7")}),flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        REPORT["status"]="FAILED_OR_UNKNOWN"
        REPORT["failed_gate"]=str(e)
        print("NAMED_NATIVE_RESIDUAL="+str(e),file=sys.stderr,flush=True)
        persist()
        sys.exit(1)
    else:
        persist()
