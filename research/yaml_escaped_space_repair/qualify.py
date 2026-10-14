#!/usr/bin/env python3
"""Native bounded repair qualification for independently discovered YAML whitespace difference.

No external repository writes. Candidate edit templates and verification code
are HUMAN-AUTHORED after frozen protocol. Native YAML tests are GENERATED from
pinned public YAML-specification fixture plus source-derived metamorphic
variants; their expected semantic values come from independent PyYAML.
"""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,re,shutil,subprocess,sys,time
import yaml

ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"mathgraph_fixture_native"))
import compile_fixture as source_compiler

STATE={"schema":"mathgraph.goccy-scanner-escaped-whitespace-bounded-repair.v1",
       "status":"UNKNOWN","upstream_mutated":False,
       "candidates":[],"negatives":{},"error":None,
       "manual_patch_template_authorship":True,
       "autonomous_meta_generator":"UNKNOWN"}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def go(argv,cwd,timeout=300,extra=None):
    env=os.environ.copy();env["GOTOOLCHAIN"]="local"
    if extra:env.update(extra)
    t=time.monotonic()
    try:
        p=subprocess.run(argv,cwd=cwd,env=env,text=True,
              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        code=p.returncode;log=p.stdout
    except subprocess.TimeoutExpired as err:
        code=124;log="NATIVE_TIMEOUT "+str(err)
    return {"exit":code,"elapsed":round(time.monotonic()-t,3),
            "log_sha256":sha(log.encode()),"tail":log[-9000:]}

def isolate_body(src):
    tag="func (s *Scanner) scanDoubleQuote(ctx *Context) (*token.Token, error) {"
    i=src.find(tag);j=src.find("func (s *Scanner) validateDocumentSeparatorMarker",i)
    if i<0 or j<i:raise ValueError("ORIGINAL_NATIVE_SCANNER_FUNCTION_SCOPE_MOVED")
    return src[:i],src[i:j],src[j:]

def patch_source(original,mode):
    a,b,c=isolate_body(original)
    if mode=="ORIGINAL_NO_CHANGE":return original
    if mode=="REMOVE_ALL_TRAILING_SPACE_TRIM":
        needle='''			notSpaceIdx := -1
			for i := len(value) - 1; i >= 0; i-- {
				if value[i] == ' ' {
					continue
				}
				notSpaceIdx = i
				break
			}
			if len(value) > notSpaceIdx {
				value = value[:notSpaceIdx+1]
			}
'''
        if b.count(needle)!=1:raise ValueError("ORIGINAL_NATIVE_TRIM_LOOP_STRUCTURE_CHANGED")
        return a+b.replace(needle,"",1)+c
    if mode=="PRESERVE_EXPLICIT_ESCAPED_SPACE_INDEX":
        patches=[
           ('	value := []rune{}\n','	value := []rune{}\n	escapedSpaceIndex := -1\n'),
           ("if value[i] == ' ' {","if value[i] == ' ' && i != escapedSpaceIndex {"),
           ("value = value[:notSpaceIdx+1]\n","value = value[:notSpaceIdx+1]\n			escapedSpaceIndex = -1\n"),
           ("value = append(value, 0x20)\n","value = append(value, 0x20)\n				escapedSpaceIndex = len(value) - 1\n")
        ]
        for old,new in patches:
            if b.count(old)!=1:raise ValueError("UNEXPECTED_SCANNER_PATCHSITE_OR_AMBIGUITY:"+repr(old))
            b=b.replace(old,new,1)
        return a+b+c
    raise ValueError("NOT_FROZEN_CANDIDATE_PATCH:"+mode)

def source_inputs(original,minimum):
    # Every target value derives from original external YAML input and
    # independently computed PyYAML semantics; no handwritten success text.
    variants={
       "original":original,
       "one-deletion-minimal":minimum,
       "repeat-escaped-space":original.replace(chr(92)+" ",(chr(92)+" ")*2,1),
       "append-unescaped-trailing-space":original.replace(chr(92)+" ",chr(92)+"  ",1),
       "replace-escape-with-unescaped-space":original.replace(chr(92)+" "," ",1),
       "replace-escape-with-linebreak-escape":original.replace(chr(92)+" "+chr(10),chr(92)+chr(10),1),
       "add-content-after-escaped-space":original.replace(chr(92)+" "+chr(10),chr(92)+" x"+chr(10),1),
    }
    result=[]
    seen=set()
    for key,src in variants.items():
        if src in seen:continue
        seen.add(src)
        try:
            val=yaml.safe_load(src)
            if not isinstance(val,str):continue
        except Exception:continue
        result.append({"label":key,"input_yaml":src,"expected_json":json.dumps(val),
              "input_sha256":sha(src.encode()),"expected_value_hex":val.encode().hex(),
              "expected_value_repr":repr(val)})
    if not {"original","one-deletion-minimal","replace-escape-with-unescaped-space"}.issubset(
        {x["label"] for x in result}):
        raise ValueError("CRITICAL_PYYAML_METAMORPHIC_VARIANT_MISSING")
    return result

def generate_tests(variants,module):
    source_file=None;methods={}
    for v in variants:
        name,code=source_compiler.make_native_test(v,module,prefix="NativeYaml")
        if source_file is None:
            source_file=code
        else:
            idx=code.find("func "+name+"(")
            if idx<0:raise ValueError("GENERATOR_NATIVE_FUNCTION_MISSING")
            source_file+="\n"+code[idx:]
        methods[v["label"]]=name
    return source_file,methods

def run_test_program(base,out,modfile,code,methods,tag):
    scratch=out/("candidate-"+tag)
    source_compiler.native_overlay(base,scratch)
    filename=scratch/"zz_mathgraph_generated_yaml_whitespace_test.go"
    filename.write_text(code)
    result=go(["go","test","-count=1","-v","-timeout=120s",
               "-run","^TestNativeYaml_", "."],scratch,240,
              {"GOFLAGS":"-modfile="+str(modfile)})
    observations={}
    for label,name in methods.items():
        start=("=== RUN   "+name) in result["tail"]
        accepted=("--- PASS: "+name) in result["tail"]
        rejected=("--- FAIL: "+name) in result["tail"]
        observations[label]={"method":name,"executed":start,
                              "PASS":accepted,"FAIL":rejected}
    result["individual_method_observations"]=observations
    result["generated_test_sha256"]=sha(code.encode())
    return result,scratch

def main(proto,workspace,out):
    p=json.loads(proto.read_bytes())
    if p["schema"]!="mathgraph.source-bound-yaml-scanner-repair-v1":
        raise ValueError("WRONG_FROZEN_REPAIR_PROTOCOL")
    f=p["source_case"];u=p["upstream"]
    spec=workspace/"source-175";original=workspace/"original-goccy"
    reference=workspace/"reference-go-yaml"
    source_compiler.check_repo(spec,f["commit"],{f["path"]:f["git_blob"],
         f["readme"]:f["readme_blob"]})
    source_compiler.check_repo(original,u["commit"],{u["scanner_file"]:u["scanner_git_blob"],
         u["module_file"]:u["module_blob"]})
    parent_first=source_compiler.source_case({"file":f["path"],"git_blob":f["git_blob"]},
                       spec,source_compiler.derive_roles_from_publisher_docs(
                           (spec/f["readme"]).read_text()))
    initial=parent_first["input_yaml"]
    if sha(initial.encode())!=f["input_sha256"]:
        raise ValueError("UNEXPECTED_ORIGINAL_YAML_INPUT")
    minimum=initial.removesuffix("\n")
    if sha(minimum.encode())!=p["prior_minimizer"]["codepoint_deletion_minimal_utf8_sha256"]:
        raise ValueError("PREVIOUS_INDEPENDENT_MINIMAL_WITNESS_NOT_REPLAYED")
    variant=source_inputs(initial,minimum)
    STATE["source_case"]={"url":"https://github.com/yaml/yaml-test-suite/pull/175",
       "original_git_blob":f["git_blob"],"original_input_sha256":f["input_sha256"],
       "minimal_sha256":sha(minimum.encode()),"variation_count":len(variant)}
    STATE["variants"]=[{k:v for k,v in row.items() if k!="input_yaml"} for row in variant]
    mod=source_compiler.native_module(original,{"module_blob":u["module_blob"]})
    base_modfile=source_compiler.module_context(original,out,"goccy",{"module_blob":u["module_blob"]})
    original_suite=go(["go","test","-count=1","-timeout=120s","./..."],original,420,
                 {"GOFLAGS":"-modfile="+str(base_modfile)})
    STATE["original_full_go_suite"]=original_suite
    if original_suite["exit"]!=0:
        raise ValueError("ORIGINAL_NATIVE_SUITE_NOT_GREEN")
    code,names=generate_tests(variant,mod)
    originals,orig_scratch=run_test_program(original,out,base_modfile,code,names,"original")
    STATE["original_original_fixture_generated_native_tests"]=originals
    if not originals["individual_method_observations"]["original"]["FAIL"]:
        raise ValueError("ORIGINAL_SCANNER_FAILURE_NOT_CONFIRMED")
    if not originals["individual_method_observations"]["one-deletion-minimal"]["FAIL"]:
        raise ValueError("INDEPENDENT_MINIMAL_WITNESS_NOT_CONFIRMED")
    # Independently maintained reference parser must accept all source-based
    # variants under the SAME source-generated Go tests.
    ref=p["prior_minimizer"].get("reference_repo",{})
    source_compiler.check_repo(reference,"f6f7691b1fdeb513f56608cd2c32c51f8194bf51",
        {"go.mod":"f407ea3213edc12392275945f8291202b0712c9d"})
    refmod=source_compiler.module_context(reference,out,"go-yaml",{"module_blob":"f407ea3213edc12392275945f8291202b0712c9d"})
    reference_code,ref_names=generate_tests(variant,"gopkg.in/yaml.v3")
    reference_results,_=run_test_program(reference,out,refmod,reference_code,ref_names,"reference")
    STATE["independent_go_yaml_original_source_native_reference"]=reference_results
    if (reference_results["exit"]!=0 or not all(
        x["PASS"] for x in reference_results["individual_method_observations"].values())):
        raise ValueError("INDEPENDENT_GO_YAML_REFERENCE_NOT_ALL_GREEN")
    scanner_source=(original/u["scanner_file"]).read_text()
    target_dir=pathlib.Path(u["scanner_file"])
    for mode in p["candidate_patches"]:
        edited=patch_source(scanner_source,mode)
        if mode=="ORIGINAL_NO_CHANGE" and edited!=scanner_source:
            raise ValueError("BASELINE_SOURCE_WAS_CHANGED")
        if mode!="ORIGINAL_NO_CHANGE" and edited==scanner_source:
            raise ValueError("PATCH_CONSTRUCTED_NO_SOURCE_CHANGE")
        selected=out/("patched-"+mode.lower())
        source_compiler.native_overlay(original,selected)
        (selected/target_dir).write_text(edited)
        res,trial_root=run_test_program(selected,out,base_modfile,code,names,mode.lower())
        all_pass=all(z["PASS"] for z in res["individual_method_observations"].values())
        suite=go(["go","test","-count=1","-timeout=120s","./..."],selected,420,
               {"GOFLAGS":"-modfile="+str(base_modfile)})
        accepted=(mode!="ORIGINAL_NO_CHANGE" and all_pass and suite["exit"]==0)
        report={"mode":mode,"source_sha256":sha(edited.encode()),
                "changed_original_source":mode!="ORIGINAL_NO_CHANGE",
                "generated_native_results":res,"complete_native_go_suite":suite,
                "all_independent_reference_cases_matched":all_pass,
                "accepted_bounded_repair":accepted}
        STATE["candidates"].append(report)
        print("PATCH_"+mode+"="+("PASS" if accepted else "REJECTED_OR_UNKNOWN")+
             " generated_pass="+str(sum(z["PASS"] for z in res["individual_method_observations"].values()))+
             " full_native_rc="+str(suite["exit"]),flush=True)
    approved=[x for x in STATE["candidates"]
              if x["mode"]=="PRESERVE_EXPLICIT_ESCAPED_SPACE_INDEX"]
    if len(approved)!=1 or not approved[0]["accepted_bounded_repair"]:
        raise ValueError("SOURCE_ESCAPED_WHITESPACE_NATIVE_REPAIR_NOT_QUALIFIED")
    if (original/u["scanner_file"]).read_text()!=scanner_source:
        raise ValueError("PUBLISHER_ORIGINAL_SOURCE_CHANGED")
    STATE["result"]="WARRANTED_BOUNDED_SOURCE_NATIVE_ESCAPED_WHITESPACE_REPAIR_IN_SCRATCH"
    STATE["negative_controls"]={
       "source_original_byte_pin":"PASS",
       "original_minimal_reopens_without_patch":"PASS",
       "original_complete_suite_unchanged":"PASS",
       "all_reference_source_derived_cases":"PASS",
       "strict_human_authored_patch_template_disclosure":"PASS",
       "no_upstream_changes":"PASS"}
    STATE["status"]="PASS"
    STATE["E2E_SYSTEM_L7"]="UNKNOWN"
def cli():
    ap=argparse.ArgumentParser()
    ap.add_argument("--protocol",required=True,type=pathlib.Path)
    ap.add_argument("--workspace",required=True,type=pathlib.Path)
    ap.add_argument("--out",required=True,type=pathlib.Path)
    a=ap.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    try:main(a.protocol.resolve(),a.workspace.resolve(),out)
    except Exception as e:
        STATE["error"]=str(e);STATE["status"]="UNKNOWN_OR_FAILED";
        print("NAMED_REPAIR_RESIDUAL="+str(e),flush=True);rc=1
    else:rc=0
    (out/"repair_report.json").write_text(json.dumps(STATE,indent=2,sort_keys=True)+"\n")
    print("FINAL="+STATE["status"],flush=True)
    sys.exit(rc)
if __name__=="__main__":cli()
