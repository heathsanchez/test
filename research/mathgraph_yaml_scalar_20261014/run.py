#!/usr/bin/env python3
"""Patch-blind issue-informed numeric grammar; native base/head/ablation. Zero upstream writes."""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
P=json.loads((HERE/"FROZEN_PROTOCOL.json").read_text())
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"mathgraph-yaml-scalar-grammar-native"
OUT.mkdir(parents=True,exist_ok=True)
WORK=OUT/"checkout"
WORK.mkdir(exist_ok=True)
REPORT={
 "authority":"ISSUE_INFORMED_PATCH_UNINSPECTED_NATIVE_GRAMMAR",
 "preregistered_protocol_commit":"9808bef402a82aaf4698fac122796878b61e033f",
 "generator_commit":"d9c3ebee6b7ea76b4c2622d05e2f0f7d5ee61088",
 "protocol_sha256":hashlib.sha256((HERE/"FROZEN_PROTOCOL.json").read_bytes()).hexdigest(),
 "generator_sha256":hashlib.sha256((HERE/"generate.py").read_bytes()).hexdigest(),
 "go_test_sha256":hashlib.sha256((HERE/"mathgraph_scalar_grammar_test.go").read_bytes()).hexdigest(),
 "third_party_writes":0,
 "blind_issue_discovery":False,
 "autonomous_generator_creation":False,
 "arms":[]
}
def git(*args):
 return subprocess.run(["git",*args],cwd=WORK,check=True,capture_output=True,text=True,timeout=260).stdout.strip()
def run():
 assert P["source_pr"]==939 and P["contributor_patch_seen"] is False
 fixture=OUT/"mathgraph_generated_scalar_cases.json"
 p=subprocess.run(["python3",str(HERE/"generate.py"),str(fixture)],
     check=True,capture_output=True,text=True,timeout=15)
 print(p.stdout.strip(),flush=True)
 corpus=json.loads(fixture.read_text())
 kinds={kind:sum(x["kind"]==kind for x in corpus)
        for kind in ("numeric","malformed","quoted","control")}
 assert kinds=={"numeric":256,"malformed":36,"quoted":96,"control":4}
 REPORT["corpus_sha256"]=hashlib.sha256(fixture.read_bytes()).hexdigest()
 cases={x["name"]:x["kind"] for x in corpus}
 git("init","--quiet")
 git("remote","add","origin","https://github.com/"+P["repository"]+".git")
 git("-c","protocol.version=2","fetch","--quiet","--no-tags","--depth=1",
     "origin",P["source_base"],P["source_head"])
 # This is an automatic file-selection rule, not a human-picked target file.
 changed=git("diff","--name-only",P["source_base"],P["source_head"],"--","*.go").splitlines()
 implementations=[p for p in changed if p.endswith(".go") and not p.endswith("_test.go")]
 if len(implementations)!=1:
  raise RuntimeError("IMPLEMENTATION_CARDINALITY_OUTSIDE_PRESET_"+str(implementations))
 implementation=implementations[0]
 REPORT["selected_source_file"]=implementation
 base_failures=set()
 for arm,sha in [
     ("BASE",P["source_base"]),
     ("CONTRIBUTOR_HEAD",P["source_head"]),
     ("HEAD_SOURCE_ABLATED",P["source_head"])
 ]:
  git("checkout","--force","--detach",sha)
  assert git("rev-parse","HEAD")==sha,"SOURCE_SHA_MOVED"
  if arm=="HEAD_SOURCE_ABLATED":
   base_bytes=subprocess.run(["git","show",P["source_base"]+":"+implementation],
             cwd=WORK,check=True,capture_output=True).stdout
   (WORK/implementation).write_bytes(base_bytes)
   assert git("diff","--name-only").splitlines()==[implementation],"ABLATION_CHANGED_OTHER_SOURCE"
  (WORK/"mathgraph_scalar_grammar_test.go").write_bytes(
    (HERE/"mathgraph_scalar_grammar_test.go").read_bytes())
  (WORK/"mathgraph_generated_scalar_cases.json").write_bytes(fixture.read_bytes())
  began=time.monotonic()
  p=subprocess.run(["go","test","-count=1","-json","-timeout=12m",
       "-run","^TestMathGraphScalarGrammar$","."],
       cwd=WORK,capture_output=True,text=True,timeout=850,
       env={**os.environ,"GOTOOLCHAIN":"auto"})
  seconds=round(time.monotonic()-began,2)
  (OUT/(arm+".jsonl")).write_text(p.stdout)
  (OUT/(arm+".stderr.txt")).write_text(p.stderr)
  outcome={}
  prefix="TestMathGraphScalarGrammar/"
  for line in p.stdout.splitlines():
   try: obj=json.loads(line)
   except ValueError: continue
   name=obj.get("Test","")
   if name.startswith(prefix) and obj.get("Action") in ("pass","fail"):
    outcome[name[len(prefix):]]=obj["Action"]
  if set(outcome)!=set(cases):
   raise RuntimeError("NATIVE_SUBTESTS_INCOMPLETE_"+arm+"_"+str(len(outcome)))
  failed={name for name,status in outcome.items() if status=="fail"}
  failed_by_kind={k:sum(cases[name]==k for name in failed) for k in kinds}
  row={
   "arm":arm,"source_sha":sha,"source_file":implementation,
   "source_blob_after_arm":git("hash-object",implementation),
   "fixture_sha256":REPORT["corpus_sha256"],
   "test_sha256":REPORT["go_test_sha256"],
   "cases":len(outcome),"passed":len(outcome)-len(failed),
   "failed":len(failed),"failed_by_kind":failed_by_kind,
   "first_failed_case_ids":sorted(failed)[:35],
   "exit_code":p.returncode,"elapsed_seconds":seconds
  }
  REPORT["arms"].append(row)
  print("MATHGRAPH_GRAMMAR_NATIVE_ARM "+json.dumps(row,sort_keys=True),flush=True)
  if arm=="BASE":
   base_failures={name for name in failed if cases[name]=="numeric"}
   assert len(base_failures)>=5,"BASE_MISSING_EXPECTED_NUMERIC_FAILURE"
   assert all(cases[n]=="numeric" for n in failed),"BASE_NEGATIVE_CONTROLS_UNEXPECTED"
  if arm=="CONTRIBUTOR_HEAD":
   if failed:
    REPORT["heldout_patch_residual_candidates"]=sorted(failed)
    raise RuntimeError("CONTRIBUTOR_HEAD_GRAMMAR_MISMATCH_REQUIRES_NATIVE_REVIEW")
   assert p.returncode==0,"CONTRIBUTOR_HEAD_NATIVE_SETUP_FAIL"
  if arm=="HEAD_SOURCE_ABLATED":
   ablated={name for name in failed if cases[name]=="numeric"}
   assert base_failures.issubset(ablated),"CAUSAL_REVERT_DID_NOT_REOPEN_BOUNDARY"
   assert all(cases[n]=="numeric" for n in failed),"ABLATED_NEGATIVE_CONTROLS_UNEXPECTED"
 assert len(REPORT["arms"])==3
 REPORT["verdict"]="WARRANTED_BOUNDED_ISSUE_INFORMED_PATCH_BLIND_NATIVE_GRAMMAR_ABLATION"
 REPORT["new_undocumented_behavior"]="UNKNOWN_NOT_CLAIMED"
 print("MATHGRAPH_GRAMMAR_FINAL "+json.dumps({
   "verdict":REPORT["verdict"],"arms":3,"cases_per_arm":len(cases),
   "base_numeric_failures":len(base_failures),
   "fixed_failures":REPORT["arms"][1]["failed"],
   "ablated_failures":REPORT["arms"][2]["failed"]
 },sort_keys=True),flush=True)
 if os.environ.get("GITHUB_STEP_SUMMARY"):
  with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:
   f.write("### Issue-informed, patch-uninspected YAML native grammar test\n\n")
   for a in REPORT["arms"]:
    f.write("- "+a["arm"]+": "+str(a["passed"])+"/"+str(a["cases"])+
      " passed, failures: "+str(a["failed"])+
      ", by kind: "+json.dumps(a["failed_by_kind"])+
      " ("+str(a["elapsed_seconds"])+"s)\n")
   f.write("\nNo claim of autonomous generator-language invention or new bug discovery without issue hints.\n")
try:
 run()
except Exception as e:
 REPORT["verdict"]="UNQUALIFIED_OR_POTENTIAL_HELDOUT_RESIDUAL"
 REPORT["diagnostic"]=str(e)[:500]
 print("MATHGRAPH_GRAMMAR_UNQUALIFIED "+str(e)[:500],file=sys.stderr)
 (OUT/"REPORT.json").write_text(json.dumps(REPORT,indent=2)+"\n")
 sys.exit(1)
(OUT/"REPORT.json").write_text(json.dumps(REPORT,indent=2)+"\n")
