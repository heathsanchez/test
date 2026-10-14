#!/usr/bin/env python3
"""Cross-project protected negative: unchanged go-native selector on new test grammar."""
import json, pathlib, subprocess, hashlib, os,sys
ROOT=pathlib.Path(__file__).resolve().parent
COORD=ROOT.parents[1]
WORK=COORD.parent
PROTO=ROOT/"FROZEN_PROTOCOL.json"
OUT=ROOT/"evidence";OUT.mkdir(parents=True,exist_ok=True)
REPORT={"authority":"UNKNOWN_UNCHANGED_TEST_GRAMMAR","old_generator_modified":False,"cases":[]}

def check(root,commit,files):
    def call(*args):
        p=subprocess.run(["git","-C",str(root),*args],capture_output=True,text=True)
        if p.returncode:raise RuntimeError("GIT_UNAVAILABLE:"+p.stderr[-300:])
        return p.stdout.strip()
    if call("rev-parse","HEAD")!=commit:raise RuntimeError("GIT_COMMIT_MISMATCH")
    for path,blob in files.items():
        if call("hash-object",path)!=blob:raise RuntimeError("GIT_BLOB_MISMATCH:"+path)

def run():
    spec=json.loads(PROTO.read_bytes());up=spec["upstream"];base=WORK/"base-go-yaml"
    files={"go.mod":up["go_mod_blob"]}
    for item in up["cases"]:
        for x in item["files"]:
            files[x["path"]]=x["base_blob"]
    check(base,up["base"],files)
    generator=COORD/"research/mathgraph_go_yaml_transfer/discover_go_test_scopes.go"
    executable=OUT/"old-scope"
    p=subprocess.run(["go","build","-o",str(executable),str(generator)],capture_output=True,text=True,env={**os.environ,"GO111MODULE":"off"})
    if p.returncode:raise RuntimeError("ORIGINAL_GO_SCOPE_GENERATOR_NOT_COMPILED:"+p.stderr[-500:])
    for item in up["cases"]:
        head=WORK/("head-go-yaml-"+str(item["pr"]))
        check(head,item["head"],{z["path"]:z["head_blob"] for z in item["files"]})
        cases=[]
        for x in item["files"]:
            if x["role"]!="native_test":continue
            t=subprocess.run([str(executable),str(base/x["path"]),str(head/x["path"]),x["path"]],
                        capture_output=True,text=True)
            parsed=json.loads(t.stdout)
            if not(t.returncode==1 and parsed.get("status")=="UNKNOWN_NO_NATIVE_TEST_SCOPE_DIFFERENCE" and not parsed.get("scopes")):
                raise RuntimeError("OLD_SCOPE_RESULT_UNEXPECTED:"+str(item["pr"])+":"+t.stdout[:500])
            cases.append({"file":x["path"],"old_grammar_result":parsed["status"],"old_grammar_exit":t.returncode})
        REPORT["cases"].append({"original_PR":item["pr"],"original_head":item["head"],"observations":cases})
        print("PR_"+str(item["pr"])+"_OLD_GO_SCOPE_DECLINES="+str(len(cases)),flush=True)
    REPORT["result"]="WARRANTED_BOUNDED_NATIVE_GENERATOR_GRAMMAR_OBSTRUCTION"
    REPORT["new_method_generated"]=False
    REPORT["next_minimal_primitive"]="GO_CHANGED_GLOBAL_TABLE_TO_RECEIVER_TEST_DEPENDENCY"
    REPORT["L7"]="UNKNOWN"
try:
    run()
except Exception as exc:
    REPORT["result"]="UNKNOWN_PROBE_FAILURE"
    REPORT["error"]=str(exc)
finally:
    (OUT/"grammar_probe.json").write_text(json.dumps(REPORT,indent=2)+"\n")
    print("STATUS="+REPORT.get("result","UNKNOWN"),flush=True)
if REPORT["result"]!="WARRANTED_BOUNDED_NATIVE_GENERATOR_GRAMMAR_OBSTRUCTION":sys.exit(1)
