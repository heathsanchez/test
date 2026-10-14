#!/usr/bin/env python3
"""Fixed metamorphic invariant on exact real Go/YAML implementations; no external writes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
P=json.loads((ROOT/"FROZEN_PROTOCOL.json").read_text())
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"mathgraph-roundtrip-native-receipts"
OUT.mkdir(parents=True,exist_ok=True)
REPORT={
 "protocol_commit":"207586de76ac7d29be4c44a28c936843a064e9d7",
 "generator_commit":"9892aee487563ccafe2c9dc50961b8c4e0eb6677",
 "protocol_sha256":hashlib.sha256((ROOT/"FROZEN_PROTOCOL.json").read_bytes()).hexdigest(),
 "source_generator_sha256":hashlib.sha256((ROOT/"generate.py").read_bytes()).hexdigest(),
 "test_template_sha256":hashlib.sha256((ROOT/"metamorphic_test.go.txt").read_bytes()).hexdigest(),
 "authority":"UNSEEN_INPUTS_NATIVE_METAMORPHIC_CANDIDATE_ONLY",
 "third_party_writes":0,"autonomous_method_invention":False,
 "repos":[]
}
def git(d,*args):
 return subprocess.run(["git",*args],cwd=d,check=True,capture_output=True,text=True,timeout=250).stdout.strip()
def main():
 assert len(P["target_revisions"])==2 and P["total_cases"]==1088
 corpus=OUT/"mathgraph_roundtrip_corpus.json"
 p=subprocess.run(["python3",str(ROOT/"generate.py"),str(corpus)],capture_output=True,text=True,check=True,timeout=20)
 print(p.stdout.strip(),flush=True)
 inputs=json.loads(corpus.read_text())
 assert len(inputs)==1088
 ids={c["id"] for c in inputs}
 assert len(ids)==1088
 index={c["id"]:c for c in inputs}
 REPORT["case_corpus_sha256"]=hashlib.sha256(corpus.read_bytes()).hexdigest()
 for target in P["target_revisions"]:
  name=target["repo"]
  directory=OUT/("checkout_"+name.replace("/","__"))
  directory.mkdir(parents=True,exist_ok=True)
  git(directory,"init","--quiet")
  git(directory,"remote","add","origin","https://github.com/"+name+".git")
  git(directory,"-c","protocol.version=2","fetch","--quiet","--no-tags",
      "--depth=1","origin",target["sha"])
  git(directory,"checkout","--force","--detach",target["sha"])
  assert git(directory,"rev-parse","HEAD")==target["sha"],"CHECKOUT_SHA_MISMATCH"
  module=target["module"]
  assert module in ("github.com/goccy/go-yaml","gopkg.in/yaml.v3")
  source=(ROOT/"metamorphic_test.go.txt").read_text().replace("@MODULE@",module)
  assert "@MODULE@" not in source
  (directory/"mathgraph_roundtrip_test.go").write_text(source)
  (directory/"mathgraph_roundtrip_corpus.json").write_bytes(corpus.read_bytes())
  # Older reference repository lacks a committed go.sum for one test
  # dependency. Module resolution is permitted in this ephemeral checkout
  # only; preserve immutable source by checking original go.mod bytes.
  original_mod=hashlib.sha256((directory/"go.mod").read_bytes()).hexdigest()
  start=time.monotonic()
  result=subprocess.run(["go","test","-mod=mod","-json","-count=1","-timeout=11m",
    "-run","^TestMathGraphStringRoundTrip$","."],
    cwd=directory,env={**os.environ,"GOTOOLCHAIN":"auto"},
    capture_output=True,text=True,timeout=810)
  assert hashlib.sha256((directory/"go.mod").read_bytes()).hexdigest()==original_mod, \
    "MODULE_MANIFEST_CHANGED_BY_DEPENDENCY_RESOLUTION_"+name
  elapsed=round(time.monotonic()-start,2)
  evidence=name.replace("/","__")
  (OUT/(evidence+".jsonl")).write_text(result.stdout)
  (OUT/(evidence+".stderr.txt")).write_text(result.stderr)
  statuses={}
  prefix="TestMathGraphStringRoundTrip/"
  for ln in result.stdout.splitlines():
   try:rec=json.loads(ln)
   except ValueError:continue
   test=rec.get("Test","")
   if test.startswith(prefix) and rec.get("Action") in ("pass","fail"):
    statuses[test[len(prefix):]]=rec["Action"]
  assert set(statuses)==ids,"INCOMPLETE_NATIVE_ROUNDTRIP_SUBTESTS_"+name+"_"+str(len(statuses))
  failed={key for key,status in statuses.items() if status=="fail"}
  assert result.returncode==(1 if failed else 0),"NATIVE_PROCESS_STATUS_MISMATCH_"+name
  fail_by_type={kind:sum(index[x]["kind"]==kind for x in failed)
      for kind in P["case_budgets"]}
  REPORT["repos"].append({
    "repo":name,"sha":target["sha"],"module":module,
    "test_source_sha256":hashlib.sha256(source.encode()).hexdigest(),
    "fixture_sha256":REPORT["case_corpus_sha256"],"cases":len(statuses),
    "passed":len(statuses)-len(failed),"failed":len(failed),
    "failed_by_kind":fail_by_type,
    "failed_ids":sorted(failed),
    "go_test_exit_code":result.returncode,
    "duration_s":elapsed,
    "native_receipt":evidence+".jsonl"
  })
  print("MATHGRAPH_ROUNDTRIP_NATIVE "+json.dumps({
    "repo":name,"sha":target["sha"],"cases":len(statuses),
    "passed":len(statuses)-len(failed),"failed":len(failed),
    "by_kind":fail_by_type,"first_ids":sorted(failed)[:25],
    "duration_s":elapsed
  },sort_keys=True),flush=True)
 assert len(REPORT["repos"])==2
 target,reference=REPORT["repos"]
 assert target["repo"]=="goccy/go-yaml" and reference["repo"]=="go-yaml/yaml"
 target_fails=set(target["failed_ids"])
 reference_fails=set(reference["failed_ids"])
 only_target=sorted(target_fails-reference_fails)
 both=sorted(target_fails&reference_fails)
 reference_only=sorted(reference_fails-target_fails)
 REPORT["candidate_target_only"]=[index[x] for x in only_target]
 REPORT["both_fail_oracle_unknown"]=[index[x] for x in both]
 REPORT["reference_only"]=[index[x] for x in reference_only]
 REPORT["classification"]=(
   "NEW_REPRODUCIBLE_TARGET_ONLY_CANDIDATE_REQUIRES_INDEPENDENT_REPLAY" if only_target else
   "NO_TARGET_ONLY_DIFFERENTIAL_WITNESS_IN_FROZEN_CORPUS"
 )
 REPORT["warrant"]={
   "target_specific_native_failure_candidates":len(only_target),
   "shared_invariant_failures_not_promoted":len(both),
   "reference_only_invariant_failures":len(reference_only),
   "no_unseen_issue_discovery_claim":True,
   "source_to_method_generator_self_modification":"NOT_TESTED",
 }
 print("MATHGRAPH_ROUNDTRIP_FINAL "+json.dumps({
   "classification":REPORT["classification"],
   "target_only":len(only_target),"shared_unknown":len(both),
   "reference_only":len(reference_only),
   "first_target_candidates":[index[x] for x in only_target[:8]]
 },ensure_ascii=False,sort_keys=True),flush=True)
 if os.environ.get("GITHUB_STEP_SUMMARY"):
  with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:
   f.write("### Two independent Go YAML string-roundtrip semantic oracles\n\n")
   for x in REPORT["repos"]:
    f.write("- "+x["repo"]+" at "+x["sha"]+": "+str(x["passed"])+
     "/1088 passed; failures "+str(x["failed"])+
     ", by family "+json.dumps(x["failed_by_kind"])+".\n")
   f.write("\nTarget-only candidates: "+str(len(only_target))+
     "; shared/invariant-uncertain: "+str(len(both))+
     "; reference-only: "+str(len(reference_only))+".\n\n")
   f.write("All deviations are **candidates only** pending native reproduction and review; no upstream writes.\n")
try:main()
except Exception as e:
 REPORT["classification"]="INFRASTRUCTURE_OR_ORACLE_INCOMPLETE"
 REPORT["diagnostic"]=str(e)[:600]
 print("MATHGRAPH_ROUNDTRIP_UNQUALIFIED "+str(e)[:600],file=sys.stderr)
 (OUT/"REPORT.json").write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n")
 sys.exit(1)
(OUT/"REPORT.json").write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n")
