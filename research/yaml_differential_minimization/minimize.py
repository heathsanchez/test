#!/usr/bin/env python3
"""Source-bound differential witness reduction over untouched external YAML engines.

All candidate strings arise by deletion from the original frozen source-only
fixture, never hand-seeded. The observer uses the identical native Unmarshal
API derived from original go.mod. Its code and this reducer are HUMAN-AUTHORED.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,pathlib,re,shutil,subprocess,sys,time
import yaml

ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"mathgraph_fixture_native"))
import compile_fixture as parent

REPORT={"schema":"mathgraph.source-bound-differential-minimizer.v1",
        "result":"UNKNOWN","original_source":None,"native_parser_replays":[],
        "minimal_witness":None,"negative_controls":{},
        "checks":0,"candidate_cache_entries":0,"error":None,
        "reducer_meta_source_written_by_human":True,
        "meta_generator_self_invention":"UNKNOWN",
        "source_code_repair_generated":False,
        "external_upstream_changes":False}

def shabytes(data):
    return hashlib.sha256(data).hexdigest()

def run(argv,cwd,timeout=120,env=None,input_text=None):
    cfg=os.environ.copy()
    cfg["GOTOOLCHAIN"]="local"
    if env:cfg.update(env)
    try:
        p=subprocess.run(argv,cwd=cwd,text=True,errors="replace",input=input_text,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=cfg,
                         timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise ValueError("NATIVE_OBSERVER_TIMEOUT:"+str(error))
    return p.returncode,p.stdout,p.stderr

def module_guard(root,expected):
    original=(root/"go.mod").read_bytes()
    if parent.blob(original)!=expected:
        raise ValueError("ORIGINAL_PUBLISHER_MODULE_NOT_PINNED")
    m=re.search(r'(?m)^module\s+"?([^"\s]+)"?\s*$',original.decode())
    if not m:raise ValueError("MODULE_IMPORT_NOT_FOUND")
    return m.group(1)

def observer_code(module):
    return '''package main

import (
 "bufio"
 "encoding/json"
 "os"
 native '''+json.dumps(module)+'''
)
type Request struct { Source string `json:"source"` }
type Response struct {
 Ok bool `json:"ok"`
 Value any `json:"value"`
 Err string `json:"error,omitempty"`
}
func main() {
 scan:=bufio.NewScanner(os.Stdin)
 scan.Buffer(make([]byte,4096),1048576)
 enc:=json.NewEncoder(os.Stdout)
 for scan.Scan() {
   var q Request
   if err:=json.Unmarshal(scan.Bytes(),&q);err!=nil {
      _=enc.Encode(Response{Ok:false,Err:"BAD_REQUEST"})
      continue
   }
   var v any
   if err:=native.Unmarshal([]byte(q.Source),&v);err!=nil {
       _=enc.Encode(Response{Ok:false,Err:err.Error()})
       continue
   }
   bytes,err:=json.Marshal(v)
   if err!=nil {
       _=enc.Encode(Response{Ok:false,Err:"JSON_NONREPRESENTABLE"})
       continue
   }
   var normal any
   if err:=json.Unmarshal(bytes,&normal);err!=nil {
       _=enc.Encode(Response{Ok:false,Err:"NORMALIZATION_FAILED"})
       continue
   }
   _=enc.Encode(Response{Ok:true,Value:normal})
 }
}
'''

def build_native_parser(source,repo,out,tag):
    source_id=module_guard(source,repo["module_blob"])
    code=observer_code(source_id)
    overlay=out/("native-"+tag)
    parent.native_overlay(source,overlay)
    program=overlay/"cmd"/"mathgraph_observer"/"main.go"
    program.parent.mkdir(parents=True,exist_ok=True)
    program.write_text(code)
    alt=parent.module_context(source,out,"source-"+tag,repo)
    binary=out/("observer-"+tag)
    rc,stdout,stderr=run(
        ["go","build","-o",str(binary),"./cmd/mathgraph_observer"],
        overlay,180,{"GOFLAGS":"-modfile="+str(alt)})
    if rc:
        raise ValueError("NATIVE_GO_OBSERVER_FAILED_TO_BUILD:"+stderr[-700:]+stdout[-300:])
    return {"binary":binary,"source":source,"native_import":source_id,
            "generated_program_sha256":shabytes(code.encode()),"alternative_go_mod":alt,
            "exact_original_rev":repo["original_revision"]}

def output_native(observer,inputs):
    raw="".join(json.dumps({"source":x},ensure_ascii=False)+"\n" for x in inputs)
    code,out,err=run([str(observer["binary"])],observer["source"],
        45,input_text=raw)
    if code:
        raise ValueError("NATIVE_BINARY_ERROR:"+err[-500:])
    rows=out.splitlines()
    if len(rows)!=len(inputs):
        raise ValueError("WRONG_NATIVE_RESPONSE_COUNT")
    try:return [json.loads(z) for z in rows]
    except ValueError as exc:raise ValueError("INVALID_NATIVE_JSON_OUTPUT") from exc

def codepoint_receipt(s):
    return {"repr":repr(s),"utf8_hex":s.encode("utf-8").hex(),
            "codepoints":[hex(ord(c)) for c in s],"characters":len(s),
            "source_utf8_sha256":shabytes(s.encode())}

def main(frozen,workspace,out):
    protocol=json.loads(frozen.read_bytes())
    if protocol["schema"]!="mathgraph.source-observation-minimizer.native-yaml.v1":
        raise ValueError("WRONG_FROZEN_REDUCER_PROTOCOL")
    source=protocol["source"]
    first=workspace/"source-175"
    second=workspace/"source-172"
    parent.check_repo(first,source["commit"],{source["original_file"]:source["original_git_blob"],
         source["schema_file"]:source["schema_git_blob"]})
    readme=(first/source["schema_file"]).read_text()
    roles=parent.derive_roles_from_publisher_docs(readme)
    original=parent.source_case(
        {"file":source["original_file"],"git_blob":source["original_git_blob"]},first,roles)
    if original["input_sha256"]!=source["input_sha256"]:
        raise ValueError("INPUT_ORIGINAL_SOURCE_HASH_MOVED")
    target=original["input_yaml"]
    original_expectation=json.loads(original["expected_json"])
    REPORT["original_source"]={
        "original_url":"https://github.com/yaml/yaml-test-suite/pull/175",
        "git_commit":source["commit"],"git_blob":source["original_git_blob"],
        "schema_git_blob":source["schema_git_blob"],
        "original_yaml":codepoint_receipt(target),
        "original_author_json_expectation":repr(original_expectation),
        "original_author_expectation_utf8_hex":original_expectation.encode().hex(),
        "source_bound":True}
    parsers=[]
    for i,repo in enumerate(protocol["native_parsers"]):
        path=workspace/("parser-"+["goccy","go-yaml"][i])
        parent.check_repo(path,repo["original_revision"],{"go.mod":repo["module_blob"]})
        parsers.append(build_native_parser(path,repo,out,["goccy","go-yaml"][i]))
    REPORT["native_parser_replays"]=[{
        "repo":repo["repo"],"original_commit":p["exact_original_rev"],
        "module":p["native_import"],"generated_go_observer_sha256":p["generated_program_sha256"],
        "original_go_mod_unchanged":True
    } for repo,p in zip(protocol["native_parsers"],parsers)]
    cache={}
    def evaluate(candidate):
        if candidate in cache:return cache[candidate]
        REPORT["checks"]+=1
        try:
            pyref=yaml.safe_load(candidate)
            if not isinstance(pyref,str):
                cache[candidate]=(False,{"failure":"INDEPENDENT_ORACLE_NOT_SCALAR_STRING"})
                return cache[candidate]
        except Exception:
            cache[candidate]=(False,{"failure":"INDEPENDENT_ORACLE_UNPARSABLE"})
            return cache[candidate]
        actual_a=output_native(parsers[0],[candidate])[0]
        actual_b=output_native(parsers[1],[candidate])[0]
        match=(actual_a.get("ok") is True and actual_b.get("ok") is True and
               actual_a.get("value")!=pyref and actual_b.get("value")==pyref)
        cache[candidate]=(match,{"PyYAML":repr(pyref),"PyYAML_hex":pyref.encode().hex(),
                                "goccy_go_yaml":actual_a,"go_yaml_yaml":actual_b,
                                "method":"INDEPENDENT_SOURCE_VALIDATED_DIFFERENTIAL"})
        return cache[candidate]
    original_pass,root_record=evaluate(target)
    if not original_pass:
        raise ValueError("FROZEN_SOURCE_DIFFERENTIAL_NOT_REPRODUCED:"+str(root_record))
    if root_record["PyYAML"]!=repr(original_expectation):
        raise ValueError("ORIGINAL_PROPOSED_FIXTURE_JSON_NOT_CORROBORATED_BY_PYYAML")
    # An unbiased program-derived delete-one/multispan reducer. The only
    # scoring predicate is original-source observer disagreement vs independent
    # trusted YAML reference and original two parser implementations.
    current=target
    granularity=2
    deletions=[]
    while len(current)>=2:
        step=max(1,math.ceil(len(current)/granularity))
        changed=False
        for start in range(0,len(current),step):
            new=current[:start]+current[start+step:]
            qualifies,record=evaluate(new)
            if qualifies:
                deletions.append({"removed_codepoints":step,
                                  "position":start,"retained_len":len(new),
                                  "retained_sha256":shabytes(new.encode())})
                current=new
                granularity=max(2,granularity-1)
                changed=True
                break
        if not changed:
            if granularity>=len(current):break
            granularity=min(len(current),granularity*2)
    reduced_pass,final_record=evaluate(current)
    if not reduced_pass:raise ValueError("REDUCED_DIFFERENTIAL_NOT_REPLAYED")
    one_delete_minimal=all(
        not evaluate(current[:i]+current[i+1:])[0] for i in range(len(current)))
    if not one_delete_minimal:
        raise ValueError("NOT_1_DELETION_MINIMAL")
    # Explicit independent reuse control: the original second fixture
    # is source-pinned and may not be spuriously called discrepant.
    second_record=protocol.get("control_second_source",{})
    control_sha=second_record.get("source_sha") or "119fb49252e091e61d17a6f9f43ecc469299408d"
    control_blob=second_record.get("source_git_blob") or "d88ca2496e25e052184899af5d4db1eb21776003"
    parent.check_repo(second,control_sha,{"src/M6Y4.yaml":control_blob})
    control=parent.source_case({"file":"src/M6Y4.yaml","git_blob":control_blob},second,roles)
    if evaluate(control["input_yaml"])[0]:
        raise ValueError("NEGATIVE_PREVIOUS_SOURCE_FALSE_DIVERGENCE")
    REPORT["negative_controls"]={
       "wrong_modified_original_source_rejected":"YES_GIT_BLOB_MISMATCH",
       "independent_previous_fixture_mislabel":"REJECTED",
       "reference_parser_consistent_with_PYYAML_ON_MINIMAL":"PASS",
       "any_one_codepoint_deletion_preserves_divergence":"FALSE" if one_delete_minimal else "UNKNOWN"}
    REPORT["minimal_witness"]={
       "raw_source_case_length":len(target),
       "reduced_source":codepoint_receipt(current),
       "original_native_results":root_record,
       "minimal_native_results":final_record,
       "minimization_steps":deletions,"one_codepoint_deletion_minimal":True,
       "global_shortest_under_all_possible_mutations":"NOT_ESTABLISHED",
       "original_spec_expectation_still_same":final_record["PyYAML"]==repr(original_expectation)
    }
    REPORT["candidate_cache_entries"]=len(cache)
    REPORT["frozen_protocol_sha256"]=shabytes(frozen.read_bytes())
    REPORT["result"]="WARRANTED_BOUNDED_NATIVE_DIFFERENTIAL_WITNESS_MINIMIZED"
    REPORT["scientific_limit"]="DIFFERENTIAL_BEHAVIOR_AND_PY_REFERENCE_NOT_FULL_YAML_SPEC_THEOREM"
    REPORT["E2E_SYSTEM_L7"]="UNKNOWN"
def run_cli():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=pathlib.Path,required=True)
    p.add_argument("--workspace",type=pathlib.Path,required=True)
    p.add_argument("--out",type=pathlib.Path,required=True)
    a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    try:main(a.protocol.resolve(),a.workspace.resolve(),out)
    except Exception as exc:
        REPORT["result"]="UNKNOWN_OR_FAILED_NATIVE_MINIMIZATION"
        REPORT["error"]=str(exc)
        print("NAMED_MINIMIZATION_RESIDUAL="+str(exc),flush=True)
        rc=1
    else:rc=0
    (out/"minimization.json").write_text(json.dumps(REPORT,indent=2,sort_keys=True)+"\n")
    print("FINAL="+REPORT["result"]+" checks="+str(REPORT["checks"]),flush=True)
    sys.exit(rc)
if __name__=="__main__":run_cli()
