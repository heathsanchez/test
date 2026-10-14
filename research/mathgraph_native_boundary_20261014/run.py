#!/usr/bin/env python3
"""Source-pinned native Go before/after/ablation verifier; no upstream writes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
REPORT_DIR = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "mathgraph-native-boundary-evidence"
REPORT_DIR.mkdir(parents=True,exist_ok=True)
MANIFEST_BYTES = (ROOT / "FROZEN_PROTOCOL.json").read_bytes()
P = json.loads(MANIFEST_BYTES)
RECORD = {
 "protocol_commit":"21230aa8bccbf039d1f132cbb07583dd01e4048d",
 "protocol_sha256":hashlib.sha256(MANIFEST_BYTES).hexdigest(),
 "authority":"NATIVE_HISTORICAL_CALIBRATION_KNOWN_PATCHES_NOT_BLIND_DISCOVERY",
 "arms":[],
 "external_source_writes":0
}
CASE_EXPECTATIONS = {
 "ethereum/go-ethereum":(["matching_id"],
   ["mismatched_numeric","null_id","missing_id","wrong_type_string"]),
 "goccy/go-yaml":(["matching_unique_binding"],
   ["mapping_prior_binding","sequence_prior_binding"])
}
TEST_FILES={
 "ethereum/go-ethereum":"mathgraph_rpc_boundary_test.go",
 "goccy/go-yaml":"mathgraph_yaml_boundary_test.go"
}
def git(cwd,*args,timeout=270):
 p=subprocess.run(["git",*args],cwd=cwd,check=True,capture_output=True,
                  text=True,timeout=timeout)
 return p.stdout.strip()
def pin_source(d,item,sha,expected_blob):
 git(d,"checkout","--force","--detach",sha)
 if git(d,"rev-parse","HEAD") != sha:
  raise RuntimeError("SOURCE_SHA_MISMATCH")
 if git(d,"hash-object",str(d/item["ablate_file"])) != expected_blob:
  raise RuntimeError("SOURCE_BLOB_MISMATCH")
def native_go_test(d,item,arm,should_pass,should_fail):
 filename=item["test_function"]
 cmd=["go","test","-count=1","-timeout=8m","-json",
      "-run","^"+filename+"$",item["package"]]
 began=time.monotonic()
 p=subprocess.run(cmd,cwd=d,capture_output=True,text=True,timeout=600,
                  env={**os.environ,"GOTOOLCHAIN":"auto"})
 elapsed=round(time.monotonic()-began,2)
 evidence_id=item["repo"].replace("/","__")+"__"+arm
 (REPORT_DIR/(evidence_id+".jsonl")).write_text(p.stdout)
 (REPORT_DIR/(evidence_id+".stderr.txt")).write_text(p.stderr)
 prefix=filename+"/"
 statuses={}
 for line in p.stdout.splitlines():
  try: obj=json.loads(line)
  except json.JSONDecodeError:continue
  name=obj.get("Test","")
  if name.startswith(prefix) and obj.get("Action") in ("pass","fail"):
   statuses[name[len(prefix):]]=obj["Action"]
 expected={**{s:"pass" for s in should_pass},**{s:"fail" for s in should_fail}}
 passed=(statuses==expected and p.returncode==(0 if not should_fail else 1))
 result={
  "repository":item["repo"],"arm":arm,"source_sha":git(d,"rev-parse","HEAD"),
  "test_sha256":hashlib.sha256((d/item["test_path"]).read_bytes()).hexdigest(),
  "test_outcomes":statuses,"expected":expected,
  "exit_code":p.returncode,"native_seconds":elapsed,
  "qualified":passed
 }
 RECORD["arms"].append(result)
 print("MATHGRAPH_NATIVE_ARM "+json.dumps(result,sort_keys=True),flush=True)
 if not passed:
  raise RuntimeError("NATIVE_ORACLE_MISMATCH_"+item["repo"].replace("/","_")+"_"+arm)

def main():
 if P.get("epistemic_authority")!="CROSS_REPOSITORY_HISTORICAL_BEFORE_AFTER_CALIBRATION_NOT_BLIND_DISCOVERY":
  raise RuntimeError("PROTOCOL_AUTHORITY_CHANGED")
 if shutil.which("go") is None:raise RuntimeError("NO_NATIVE_GO_TOOLCHAIN")
 if len(P.get("target_repositories",[]))!=2:raise RuntimeError("PROTOCOL_TARGETS_CHANGED")
 for item in P["target_repositories"]:
  name=item["repo"]
  if name not in CASE_EXPECTATIONS:raise RuntimeError("TARGET_NOT_PREREGISTERED")
  controls,invalid=CASE_EXPECTATIONS[name]
  dest=REPORT_DIR/("checkout_"+name.replace("/","__"))
  dest.mkdir()
  git(dest,"init","--quiet")
  git(dest,"remote","add","origin","https://github.com/"+name+".git")
  git(dest,"-c","protocol.version=2","fetch","--quiet","--no-tags",
      "--depth=1","origin",item["base_sha"],item["head_sha"])
  for arm,sha,blob in [
   ("BASE",item["base_sha"],item["base_blob"]),
   ("PATCHED",item["head_sha"],item["head_blob"]),
   ("ABLATED",item["head_sha"],item["head_blob"])
  ]:
   pin_source(dest,item,sha,blob)
   if arm=="ABLATED":
    baseline=subprocess.run(["git","show",item["base_sha"]+":"+item["ablate_file"]],
      cwd=dest,capture_output=True,check=True).stdout
    (dest/item["ablate_file"]).write_bytes(baseline)
    if git(dest,"hash-object",str(dest/item["ablate_file"]))!=item["base_blob"]:
     raise RuntimeError("ABLATION_BLOB_MISMATCH")
    if git(dest,"diff","--name-only").splitlines()!=[item["ablate_file"]]:
     raise RuntimeError("ABLATION_EXCEEDS_SINGLE_SOURCE_FILE")
   source=ROOT/TEST_FILES[name]
   testfile=dest/item["test_path"]
   testfile.parent.mkdir(parents=True,exist_ok=True)
   shutil.copyfile(source,testfile)
   native_go_test(dest,item,arm,controls+invalid if arm=="PATCHED" else controls,
                  [] if arm=="PATCHED" else invalid)
  print("MATHGRAPH_NATIVE_REPO_3_ARMS_QUALIFIED "+name,flush=True)
 if len(RECORD["arms"])!=6 or not all(x["qualified"] for x in RECORD["arms"]):
  raise RuntimeError("INCOMPLETE_NATIVE_QUALIFICATION")
 RECORD["verdict"]="WARRANTED_BOUNDED_HISTORICAL_NATIVE_CAUSAL_ABLATION"
 RECORD["blind_discovery"]="NOT_TESTED_ALREADY_SAW_AUTHOR_FIXES"
 RECORD["autonomous_method_creation"]="NOT_TESTED"
 (REPORT_DIR/"REPORT.json").write_text(json.dumps(RECORD,indent=2)+"\n")
 print("MATHGRAPH_NATIVE_FINAL "+json.dumps({
  "verdict":RECORD["verdict"],"arm_count":len(RECORD["arms"]),
  "all_qualified":True,"blind_discovery":RECORD["blind_discovery"]
 }),flush=True)
 if os.environ.get("GITHUB_STEP_SUMMARY"):
  with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as fd:
   fd.write("### Native source-pinned causal calibration (original contributor fixes known)\n\n")
   for a in RECORD["arms"]:
    fd.write("- "+a["repository"]+" "+a["arm"]+": "+json.dumps(a["test_outcomes"])+
      " (qualified="+str(a["qualified"])+", "+str(a["native_seconds"])+"s)\n")
   fd.write("\n**NOT a blind discovery, autonomous method invention, or live App semantic publication.**\n")

try:main()
except Exception as e:
 RECORD["verdict"]="UNQUALIFIED"
 RECORD["diagnostic"]=str(e)[:500]
 (REPORT_DIR/"REPORT.json").write_text(json.dumps(RECORD,indent=2)+"\n")
 print("MATHGRAPH_NATIVE_UNQUALIFIED "+str(e)[:500],file=sys.stderr)
 sys.exit(1)
