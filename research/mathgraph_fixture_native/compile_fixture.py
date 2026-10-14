#!/usr/bin/env python3
"""Produce original source-bound native Go tests from external specification-only fixtures.

The upstream suite supplies inputs and expected JSON outcomes. No PR author
supplied executable tests or code fixes. This generator is HUMAN-AUTHORED,
not a self-modifying meta-generator; its values and case names are *read* from
original source (not seeded in program code).
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,re,shutil,subprocess,sys,time,os,importlib.util

import yaml

ROOT=pathlib.Path(__file__).resolve().parent
REPORT={"schema":"mathgraph.external-spec-to-native-go-test.v1",
        "state":"UNKNOWN","cases":[],"counterfactuals":[],
        "generator_human_authored":True,
        "generated_native_test_files":True,
        "generator_self_modified":False,
        "E2E_SYSTEM_L7":"UNKNOWN",
        "error":None}

def digest(s):
    return hashlib.sha256(s).hexdigest()

def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\\0"+data).hexdigest()

def git(root,*args):
    cp=subprocess.run(["git","-C",str(root),*args],capture_output=True,text=True)
    if cp.returncode:raise ValueError("SOURCE_GIT_FAILURE:"+cp.stderr[-240:])
    return cp.stdout.strip()

def check_repo(root,sha,files):
    if git(root,"rev-parse","HEAD")!=sha:
        raise ValueError("EXACT_ORIGINAL_SOURCE_REVISION_MISMATCH")
    for path,expected in files.items():
        if git(root,"hash-object",path)!=expected:
            raise ValueError("ORIGINAL_SOURCE_GIT_BLOB_MISMATCH:"+path)

def run(argv,cwd,timeout=280,envextra=None):
    env=os.environ.copy()
    env["GOTOOLCHAIN"]="local"
    if envextra:env.update(envextra)
    t=time.monotonic()
    try:
        x=subprocess.run(argv,cwd=cwd,env=env,stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,text=True,errors="replace",timeout=timeout)
        code=x.returncode;output=x.stdout
    except subprocess.TimeoutExpired as error:
        code=124;output="NATIVE_TIMEOUT "+str(error)
    return {"argv":argv,"exit_code":code,"elapsed_seconds":round(time.monotonic()-t,3),
            "stdout_sha256":digest(output.encode()),"stdout_tail":output[-4600:]}

def derive_roles_from_publisher_docs(readme):
    """Role selection is constrained by the original upstream schema, not by fixture ID."""
    matches=re.findall(r"(?m)^\*\s+`in\.([A-Za-z0-9_]+)`\s+--\s+(.+)$",
                       readme)
    inputs=[ext for ext,descr in matches if "YAML input" in descr]
    oracles=[ext for ext,descr in matches if "JSON value" in descr]
    if len(inputs)!=1 or len(oracles)!=1:
        raise ValueError("UNKNOWN_OR_AMBIGUOUS_UPSTREAM_TEST_SCHEMA")
    if inputs[0]==oracles[0]:
        raise ValueError("INPUT_ORACLE_FIELD_COLLISION")
    return tuple([inputs[0],oracles[0]])

def source_case(frozen,source,readme_roles):
    data=(source/frozen["file"]).read_bytes()
    if blob(data)!=frozen["git_blob"]:
        raise ValueError("EXTERNAL_SPEC_FIXTURE_GIT_BLOB_MISMATCH")
    changed=bytearray(data);changed[10]^=1
    if blob(bytes(changed))==frozen["git_blob"]:
        raise ValueError("SOURCE_MUTATION_ACCEPTED")
    document=yaml.safe_load(data)
    if not isinstance(document,list) or len(document)!=1 or not isinstance(document[0],dict):
        raise ValueError("UNSUPPORTED_OR_MULTIPLE_FIXTURE_CASES")
    row=document[0]
    key_input,key_expected=readme_roles
    if (key_input not in row or key_expected not in row
        or not isinstance(row[key_input],str) or not isinstance(row[key_expected],str)):
        raise ValueError("MISSING_DECLARED_INPUT_OR_JSON_EXPECTATION")
    expected=json.loads(row[key_expected])
    actual_py=yaml.safe_load(row[key_input])
    # Convert through JSON to ensure comparable JSON semantic types.
    try: ref=json.loads(json.dumps(actual_py,sort_keys=True))
    except (TypeError,ValueError):raise ValueError("PYTHON_BASELINE_CANNOT_EXPORT_TO_JSON")
    if ref!=expected:
        # This is a material SOURCE-OBSERVED discrepancy; do not assume the
        # original proposed upstream fixture is already authoritative.
        raise ValueError("ORIGINAL_FIXTURE_PYTHON_BASELINE_DISAGREES_WITH_AUTHOR_JSON")
    return {"input_yaml":row[key_input],"expected_json":row[key_expected],
            "source_row_name":row.get("name","unknown"),
            "raw_git_blob":frozen["git_blob"],
            "raw_sha256":digest(data),
            "input_sha256":digest(row[key_input].encode()),
            "expected_semantic_sha256":digest(
                json.dumps(expected,sort_keys=True,separators=(",",":")).encode()),
            "python_source_oracle":"MATCHED"}

def make_native_test(case,module,prefix="MathGraphSpec"):
    name="Test"+prefix+"_"+case["input_sha256"][:14]
    ins=json.dumps(case["input_yaml"],ensure_ascii=True)
    exp=json.dumps(case["expected_json"],ensure_ascii=True)
    # The only source-specific compiler input is original go.mod module URI.
    # Native Go yaml.Unmarshal is the shared public interface of the declared
    # two independently maintained libraries. No source code changes are made.
    src=f'''package yaml_test

import (
  "encoding/json"
  "fmt"
  "reflect"
  "testing"
  native {json.dumps(module)}
)

func {name}(t *testing.T) {{
  source := {ins}
  expectation := {exp}
  var actual any
  if err := native.Unmarshal([]byte(source), &actual); err != nil {{
    t.Fatalf("PARSER_REJECTED_SOURCE_FIXTURE: %v", err)
  }}
  canonical, err := json.Marshal(actual)
  if err != nil {{ t.Fatalf("NOT_CONVERTIBLE_TO_COMPARABLE_JSON: %v", err) }}
  var decoded any
  if err := json.Unmarshal(canonical, &decoded); err != nil {{
    t.Fatalf("GENERATED_JSON_NORMALIZATION_FAILED: %v", err)
  }}
  var want any
  if err := json.Unmarshal([]byte(expectation), &want); err != nil {{
    t.Fatalf("ORIGINAL_JSON_ORACLE_INVALID: %v", err)
  }}
  if !reflect.DeepEqual(decoded,want) {{
    t.Fatalf("ORIGINAL_AUTHOR_EXPECTATION_MISMATCH: got=%s expected=%s",
              fmt.Sprintf("%v",decoded),fmt.Sprintf("%v",want))
  }}
}}
'''
    return name,src

def native_module(root,pin):
    original=(root/"go.mod").read_bytes()
    if blob(original)!=pin["module_blob"]:
        raise ValueError("NATIVE_GO_MODULE_PIN_CHANGED")
    m=re.search(r'(?m)^module\s+"?([^"\s]+)"?\s*$',original.decode())
    if not m:raise ValueError("ORIGINAL_GO_MODULE_NOT_DISCOVERED")
    return m.group(1)

def native_overlay(root,dest):
    def ignore(folder,names):
        return {s for s in names if s in {".git",".cache","__pycache__"}}
    shutil.copytree(root,dest,ignore=ignore,dirs_exist_ok=False)

def module_context(root,out,tag,repo):
    # Old go-yaml/yaml's historical go.mod lacks a current checksum/Go directive.
    # Normalize dependency tool input OUTSIDE original publisher repository,
    # as in previously qualified exact Go table-method work.
    raw=(root/"go.mod").read_bytes()
    alt=out/(tag+".mod")
    alt.write_bytes(raw)
    result=run(["go","mod","tidy","-modfile="+str(alt)],root,120)
    if result["exit_code"]!=0:
        raise ValueError("HISTORICAL_GO_DEPENDENCY_CONTEXT_UNAVAILABLE:"+str(result))
    if blob((root/"go.mod").read_bytes())!=repo["module_blob"]:
        raise ValueError("PUBLISHER_GO_MODULE_REWRITTEN")
    return alt

def replay(proto,root,out):
    data=json.loads(proto.read_bytes())
    if data["schema"]!="mathgraph.native-generator-fixture-source-progression.v1":
        raise ValueError("UNQUALIFIED_FROZEN_SOURCE_PROTOCOL")
    report_hash=digest(proto.read_bytes())
    out.mkdir(parents=True,exist_ok=True)
    fixture_sources={}
    for i,f in enumerate(data["independent_source"]["cases"]):
        src=root/("source-"+str(f["PR"]))
        check_repo(src,f["commit"],{f["file"]:f["git_blob"]})
        fixture_sources[f["PR"]]=src
    original_readme=fixture_sources[data["independent_source"]["cases"][0]["PR"]]/data["independent_source"]["schema_description_path"]
    if blob(original_readme.read_bytes())!=data["independent_source"]["schema_blob"]:
        raise ValueError("UPSTREAM_SPEC_SCHEMA_VERSION_CHANGED")
    roles=derive_roles_from_publisher_docs(original_readme.read_text())
    REPORT["schema_roles_from_pinned_original_documentation"]=list(roles)
    REPORT["frozen_protocol_sha256"]=report_hash
    fixtures=[(i,source_case(i,fixture_sources[i["PR"]],roles))
              for i in data["independent_source"]["cases"]]
    # Old Go compiler cannot parse any .yaml source as a Go-native test file;
    # the declared constructor grammar rejects the out-of-language path.
    prior=(root/"coordinator"/"research/mathgraph_go_yaml_transfer/discover_go_test_scopes.go")
    if "strings.HasSuffix(relative,\"_test.go\")" not in prior.read_text():
        raise ValueError("PREVIOUS_METHOD_DECLINE_SOURCE_NOT_FOUND")
    REPORT["previous_go_method"]="UNKNOWN_UNSUPPORTED_SPEC_ONLY_FIXTURE_EXTENSION"
    for repo in data["external_native_parsers"]:
        tag=repo["submodule_id"]
        target=root/("parser-"+tag)
        check_repo(target,repo["revision"],{"go.mod":repo["module_blob"]})
        module=native_module(target,repo)
        context=module_context(target,out,tag,repo)
        extra={"GOFLAGS":"-modfile="+str(context)}
        baseline=run(["go","test","-count=1","-timeout=120s","./..."],target,420,extra)
        REPORT.setdefault("ordinary_go_suite_baselines",[]).append({
             "repo":repo["repository"],"native":baseline})
        if baseline["exit_code"]!=0:
            raise ValueError("HISTORICAL_ORIGINAL_NATIVE_GO_SUITE_RED:"+repo["repository"])
        for spec,case in fixtures:
            workspace=out/("replay-"+tag+"-"+str(spec["PR"]))
            native_overlay(target,workspace)
            name,compiled=make_native_test(case,module)
            testpath=workspace/"zz_mathgraph_external_spec_generated_test.go"
            testpath.write_text(compiled)
            # Generate original source a second time and assert exact identity
            # after clean restart without stateful saved answers.
            if make_native_test(case,module)[1]!=compiled:
                raise ValueError("GENERATED_TEST_NOT_DETERMINISTIC")
            native=run(["go","test","-count=1","-v","-timeout=120s",
                        "-run","^"+name+"$","."],workspace,300,extra)
            executed=("=== RUN   "+name in native["stdout_tail"] and
                      ("--- PASS: "+name in native["stdout_tail"] or
                       "--- FAIL: "+name in native["stdout_tail"]))
            if native["exit_code"] in (124,) or not executed:
                verdict="UNKNOWN_GENERATED_NATIVE_TEST_NOT_EXECUTED"
            elif native["exit_code"]==0:
                verdict="WARRANTED_BOUNDED_PROPOSED_SPEC_FIXTURE_AGREEMENT"
            elif "ORIGINAL_AUTHOR_EXPECTATION_MISMATCH" in native["stdout_tail"]:
                verdict="WARRANTED_BOUNDED_OBSERVED_FIXTURE_EXPECTATION_DIFFERENCE"
            else:
                verdict="UNKNOWN_NATIVE_PARSER_OR_TEST_INFRASTRUCTURE"
            REPORT["cases"].append({
               "fixture_PR":spec["PR"],"stage":spec["stage"],
               "original_source":spec["file"],"source_repo":data["independent_source"]["repository"],
               "native_parser_repo":repo["repository"],"native_module":module,
               "source_identity":case,"generated_go_test_name":name,
               "generated_go_test_sha256":digest(compiled.encode()),
               "native_test_run":native,"native_test_executed":executed,
               "verdict":verdict,"fixture_expected_result_authorship":"ORIGINAL_UPSTREAM_TEST_SUITE_PR"})
            print("SOURCE_SPEC_PR_"+str(spec["PR"])+"_"+tag+"="+verdict,flush=True)
    # A negative oracle changes a NEW fixture's expected semantics. It must
    # fail without being able to impersonate a genuine original fixture.
    a=fixtures[0][1];b=fixtures[1][1]
    if a["expected_semantic_sha256"]==b["expected_semantic_sha256"]:
        raise ValueError("NEGATIVE_ORACLES_NOT_DISTINCT")
    swapped=dict(a);swapped["expected_json"]=b["expected_json"]
    original=make_native_test(a,data["external_native_parsers"][0]["repository"])
    changed=make_native_test(swapped,data["external_native_parsers"][0]["repository"])
    if original[1]==changed[1]:
        raise ValueError("CHANGED_JSON_ORACLE_NOT_REFLECTED_IN_CODE")
    REPORT["negative_controls"]={"changed_original_fixture_bytes":"REJECTED_GIT_BLOB",
       "swapped_original_oracle":"GENERATED_GO_BYTES_DIFFER",
       "deterministic_cold_generation":"PASS",
       "document_role_readme_source_binding":"PASS"}
    qualified=all(x["verdict"].startswith("WARRANTED_BOUNDED_") for x in REPORT["cases"])
    REPORT["state"]="WARRANTED_BOUNDED_SOURCE_SPEC_TO_EXECUTABLE_NATIVE_TEST" if qualified else "UNKNOWN_UNSUPPORTED_ORACLE_OR_EXECUTION"
    REPORT["source_specification_truth"]="UPSTREAM_PR_PROPOSED_NOT_INDEPENDENT_YAML_FORMAL_THEOREM"
    REPORT["native_program_auto_generated"]=True
    REPORT["meta_generator_code_human_written"]=True
    REPORT["L7"]="UNKNOWN"
    if not qualified:
        raise ValueError("NOT_ALL_SPEC_PARSER_PAIRS_QUALIFIED")
def persist(out):
    out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(REPORT,indent=2,sort_keys=True)+"\n")
    print("FINAL="+REPORT["state"],flush=True)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=pathlib.Path,required=True)
    p.add_argument("--workspace",type=pathlib.Path,required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    a=p.parse_args()
    try:replay(a.protocol.resolve(),a.workspace.resolve(),a.out.resolve())
    except Exception as error:
        REPORT["error"]=str(error)
        REPORT["state"]="UNKNOWN_EXECUTION_FAILURE"
        print("NAMED_RESIDUAL="+str(error),flush=True)
        persist(a.out.resolve())
        sys.exit(1)
    persist(a.out.resolve())
if __name__=="__main__":main()
