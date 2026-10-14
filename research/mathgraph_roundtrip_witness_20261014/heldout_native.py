#!/usr/bin/env python3
"""Five-thousand held-out YAML string inputs across source-exact Go projects.

Reuses *unchanged* previously native-qualified human-selected repair
functions. Does not inspect additional contributor fixes or write upstream.
"""
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
P=json.loads((ROOT/"HELDOUT_5000_PROTOCOL.json").read_text())
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"mathgraph-yaml-heldout-5000-native"
OUT.mkdir(parents=True,exist_ok=True)
EXPECTED_METHOD_BLOB=P["fixed_repair_source_blob"]
RECORD={
 "authority":"NATIVE_HELDOUT_INPUTS_EXISTING_HUMAN_REPAIR_METHOD",
 "protocol_sha256":hashlib.sha256((ROOT/"HELDOUT_5000_PROTOCOL.json").read_bytes()).hexdigest(),
 "source_generator_sha256":hashlib.sha256((ROOT/"heldout_generate.py").read_bytes()).hexdigest(),
 "go_test_template_sha256":hashlib.sha256((ROOT/"heldout_test.go.txt").read_bytes()).hexdigest(),
 "method_git_blob":EXPECTED_METHOD_BLOB,
 "cases_expected":5000,
 "no_method_revision":True,
 "upstream_writes":0,
 "native_arms":[]
}
def git(path,*args,timeout=260):
 return subprocess.run(["git",*args],cwd=path,capture_output=True,text=True,check=True,timeout=timeout).stdout.strip()

def exact_prior_methods():
 # Extract the unchanged two human-authored operations from their
 # previously qualified original source, rather than rewriting them to
 # match any held-out failures. Only trusted local AST function definitions.
 file=ROOT/"whitespace_native.py"
 actual=subprocess.run(["git","hash-object",str(file)],
   cwd=ROOT,capture_output=True,text=True,check=True,timeout=20).stdout.strip()
 if actual!=EXPECTED_METHOD_BLOB:
  raise RuntimeError("SOURCE_METHOD_BLOB_DRIFT_NOT_AN_UNCHANGED_TRANSFER")
 tree=ast.parse(file.read_text())
 selected=[node for node in tree.body if isinstance(node,ast.FunctionDef)
           and node.name in ("patch","add_whitespace")]
 if sorted(x.name for x in selected)!=["add_whitespace","patch"]:
  raise RuntimeError("FROZEN_METHOD_NAMES_NOT_FOUND")
 code=compile(ast.Module(body=selected,type_ignores=[]),str(file), "exec")
 scope={}
 exec(code,scope,scope)
 return scope["patch"],scope["add_whitespace"]

def prepare(path,repo,sha):
 path.mkdir(parents=True,exist_ok=True)
 git(path,"init","--quiet")
 git(path,"remote","add","origin","https://github.com/"+repo+".git")
 git(path,"-c","protocol.version=2","fetch","--quiet","--no-tags","--depth=1","origin",sha)
 git(path,"checkout","--force","--detach",sha)
 if git(path,"rev-parse","HEAD")!=sha:
  raise RuntimeError("FROZEN_UPSTREAM_SHA_CHANGED_"+repo)

def run_arm(label,path,sha,module,case_file,patch_text=None):
 git(path,"checkout","--force","--detach",sha)
 assert git(path,"rev-parse","HEAD")==sha
 source_blob_before=None
 if module=="github.com/goccy/go-yaml":
  source_file=path/"token/token.go"
  source_blob_before=git(path,"hash-object","token/token.go")
  assert source_blob_before==P["target"]["original_token_blob"]
  if patch_text is not None:
   source_file.write_text(patch_text)
   assert git(path,"hash-object","token/token.go")==P["target"]["fully_patched_token_blob"], \
      "HELDOUT_UNCHANGED_METHOD_FAILED_TO_REBUILD_SOURCE"
   assert git(path,"diff","--name-only").splitlines()==["token/token.go"]
 original_mod=hashlib.sha256((path/"go.mod").read_bytes()).hexdigest()
 source=(ROOT/"heldout_test.go.txt").read_text().replace("@MODULE@",module)
 assert "@MODULE@" not in source
 (path/"mathgraph_heldout_test.go").write_text(source)
 (path/"mathgraph_heldout_cases.json").write_bytes(case_file.read_bytes())
 cmd=["go","test","-mod=mod","-count=1","-timeout=11m","-json",
      "-run","^TestMathGraphHeldoutStringFidelity$","."]
 start=time.monotonic()
 proc=subprocess.run(cmd,cwd=path,capture_output=True,text=True,
    env={**os.environ,"GOTOOLCHAIN":"auto"},timeout=780)
 elapsed=round(time.monotonic()-start,2)
 (OUT/(label+".jsonl")).write_text(proc.stdout)
 (OUT/(label+".stderr.txt")).write_text(proc.stderr)
 statuses={}
 for line in proc.stdout.splitlines():
  try:entry=json.loads(line)
  except json.JSONDecodeError:continue
  name=entry.get("Test","")
  if name.startswith("TestMathGraphHeldoutStringFidelity/") and entry.get("Action") in ("fail","pass"):
   statuses[name[len("TestMathGraphHeldoutStringFidelity/"):]]=entry["Action"]
 if set(statuses)!=set(CASES):
  raise RuntimeError("HELDOUT_NATIVE_COVERAGE_INCOMPLETE_"+label+"_"+str(len(statuses)))
 failed={name for name,status in statuses.items() if status=="fail"}
 if proc.returncode!=(1 if failed else 0):
  raise RuntimeError("GO_NATIVE_EXIT_MISMATCH_"+label)
 row={
  "arm":label,"source_sha":sha,"module":module,
  "go_test_sha256":hashlib.sha256(source.encode()).hexdigest(),
  "case_corpus_sha256":RECORD["corpus_sha256"],
  "case_count":len(statuses),"passed":len(statuses)-len(failed),
  "failed":len(failed),
  "failed_by_kind":dict(Counter(CASES[x]["kind"] for x in failed)),
  "failed_ids":sorted(failed),
  "source_blob_before":source_blob_before,
  "source_blob_after":git(path,"hash-object","token/token.go") if source_blob_before else None,
  "reference_modfile_adjusted":hashlib.sha256((path/"go.mod").read_bytes()).hexdigest()!=original_mod,
  "wall_seconds":elapsed
 }
 RECORD["native_arms"].append(row)
 print("MATHGRAPH_HELDOUT_NATIVE_ARM "+json.dumps({
  **row,"failed_ids":sorted(failed)[:12]
 },sort_keys=True),flush=True)
 return failed

def main():
 global CASES
 assert P["generated_case_total"]==5000
 assert P["target"]["repo"]=="goccy/go-yaml"
 assert P["reference"]["repo"]=="go-yaml/yaml"
 patch,add_whitespace=exact_prior_methods()
 datafile=OUT/"heldout_cases.json"
 result=subprocess.run(["python3",str(ROOT/"heldout_generate.py"),str(datafile)],
    capture_output=True,text=True,check=True,timeout=60)
 print(result.stdout.strip(),flush=True)
 entries=json.loads(datafile.read_text())
 CASES={x["id"]:x for x in entries}
 assert len(CASES)==5000
 assert dict(Counter(x["kind"] for x in entries))==P["case_families"]
 RECORD["corpus_sha256"]=hashlib.sha256(datafile.read_bytes()).hexdigest()
 target=P["target"]; reference=P["reference"]
 native=OUT/"target"
 prepare(native,target["repo"],target["sha"])
 original=(native/"token/token.go").read_text()
 repaired=add_whitespace(patch(original))
 assert repaired!=original
 fail_original=run_arm("target_original",native,target["sha"],
      target["module"],datafile)
 fail_repaired=run_arm("target_repaired",native,target["sha"],
      target["module"],datafile,patch_text=repaired)
 control=OUT/"reference"
 prepare(control,reference["repo"],reference["sha"])
 fail_reference=run_arm("reference_unmodified",control,reference["sha"],
      reference["module"],datafile)
 resolved=sorted(fail_original-fail_repaired)
 newly_failed=sorted(fail_repaired-fail_original)
 target_only=sorted(fail_repaired-fail_reference)
 both=sorted(fail_repaired&fail_reference)
 reference_only=sorted(fail_reference-fail_repaired)
 RECORD["classification"]="HELDOUT_NATIVE_CROSS_LIBRARY_BEHAVIOR_OBSERVED"
 RECORD["comparison"]={
  "repaired_but_previous_failure":len(resolved),
  "new_failures_caused_by_unchanged_method":len(newly_failed),
  "residual_target_only":len(target_only),
  "residual_shared_unknown":len(both),
  "reference_only":len(reference_only),
  "resolved_case_examples":[CASES[x] for x in resolved[:18]],
  "newly_failed_case_examples":[CASES[x] for x in newly_failed[:18]],
  "target_only_case_examples":[CASES[x] for x in target_only[:25]],
  "shared_case_examples":[CASES[x] for x in both[:15]]
 }
 RECORD["universal_fidelity"]="NOT_ESTABLISHED"
 RECORD["new_bugs"]="CANDIDATES_NOT_PROMOTED"
 RECORD["method_self_invention"]="NOT_TESTED"
 print("MATHGRAPH_HELDOUT_FINAL "+json.dumps({
   "classification":RECORD["classification"],
   "original_failures":len(fail_original),
   "repaired_failures":len(fail_repaired),
   "reference_failures":len(fail_reference),
   "resolved":len(resolved),
   "new_failures":len(newly_failed),
   "target_only":len(target_only),
   "shared_unknown":len(both),
   "reference_only":len(reference_only),
   "first_target_residuals":[CASES[x] for x in target_only[:12]]
 },ensure_ascii=False,sort_keys=True),flush=True)
 if os.environ.get("GITHUB_STEP_SUMMARY"):
  with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:
   f.write("### 5,000 untouched YAML string roundtrip cases / frozen human repair method\n\n")
   for x in RECORD["native_arms"]:
    f.write("- "+x["arm"]+": "+str(x["passed"])+"/5000 pass, failures "+
      str(x["failed"])+", by family "+json.dumps(x["failed_by_kind"])+".\n")
   f.write("\nResolved from original: "+str(len(resolved))+
    "; newly failed: "+str(len(newly_failed))+
    "; target-only residuals: "+str(len(target_only))+
    "; shared: "+str(len(both))+".\n")
   f.write("\nNo prior method revision after held-out inputs. Differences remain **bounded candidates**; no autonomous invention or upstream changes.\n")

try:main()
except Exception as error:
 RECORD["classification"]="UNQUALIFIED_HELDOUT_NATIVE_OR_CONTROL"
 RECORD["diagnostic"]=str(error)[:550]
 print("MATHGRAPH_HELDOUT_UNQUALIFIED "+str(error)[:550],file=sys.stderr)
 (OUT/"REPORT.json").write_text(json.dumps(RECORD,ensure_ascii=False,indent=2)+"\n")
 sys.exit(1)
(OUT/"REPORT.json").write_text(json.dumps(RECORD,ensure_ascii=False,indent=2)+"\n")
