#!/usr/bin/env python3
"""One consequential GitHub PR review decision via real source-native Go tests.

Only writes to temporary GitHub Actions checkouts and private artifact.
No upstream comments, merges, code modifications or production-app assertions.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
PROTOCOL=json.loads((ROOT/"FROZEN_PROTOCOL.json").read_text())
TMP=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"mathgraph-one-consequential-pr958"
TMP.mkdir(parents=True,exist_ok=True)
REPO=PROTOCOL["target"]["repository"]
PR=PROTOCOL["target"]["pr"]
REPORT={
 "protocol_commit":"04b3d8c098841c8833f8055329e56048ad4d3d7c",
 "protocol_sha256":hashlib.sha256((ROOT/"FROZEN_PROTOCOL.json").read_bytes()).hexdigest(),
 "native_test_sha256":hashlib.sha256((ROOT/"mathgraph_pr958_test.go").read_bytes()).hexdigest(),
 "target":PROTOCOL["target"],
 "project_code_modified":False,
 "external_repository_writes":0,
 "claims_capped_at":"Source-bound native test observations on one PR, not general safe-to-merge or autonomous discovery",
 "arms":[]
}
CASE_TYPE="TestMathGraphNestedByteMarshalerInvariant/"
INHERITED_TYPE="TestMathGraphPreexistingScalarRiskNotAttributableToPR/"
CONTROL_NAMES={"plain_control","quoted_control"}

def git(d,*args,timeout=280):
 r=subprocess.run(["git",*args],cwd=d,capture_output=True,text=True,timeout=timeout,check=True)
 return r.stdout.strip()
def native(d,args,name,timeout=600):
 started=time.monotonic()
 proc=subprocess.run(args,cwd=d,capture_output=True,text=True,timeout=timeout,
                     env={**os.environ,"GOTOOLCHAIN":"auto"})
 duration=round(time.monotonic()-started,3)
 (TMP/(name+".stdout")).write_text(proc.stdout)
 (TMP/(name+".stderr")).write_text(proc.stderr)
 return proc,duration
def decode_subtests(stdout,prefix):
 results={}
 samples={}
 for line in stdout.splitlines():
  try:entry=json.loads(line)
  except ValueError:continue
  name=entry.get("Test","")
  if name.startswith(prefix):
   key=name[len(prefix):]
   # count only the true leaf tests, not parent case results.
   if prefix==CASE_TYPE and key.count("/")!=1:continue
   if prefix==INHERITED_TYPE and "/" in key:continue
   action=entry.get("Action")
   if action in ("pass","fail"):results[key]=action
   elif action=="output" and key not in samples and ("nested fragment" in entry.get("Output","") or "inherited string" in entry.get("Output","")):
    samples[key]=entry.get("Output","").strip()[:600]
 return results,samples
def checkout_sources():
 d=TMP/"checkout"
 d.mkdir(exist_ok=True)
 git(d,"init","--quiet")
 git(d,"remote","add","origin","https://github.com/"+REPO+".git")
 git(d,"-c","protocol.version=2","fetch","--quiet","--no-tags","--depth=1",
     "origin",PROTOCOL["target"]["base"],PROTOCOL["target"]["head"])
 return d
def run_arm(d,name,sha):
 git(d,"checkout","--force","--detach",sha)
 if git(d,"rev-parse","HEAD")!=sha:raise RuntimeError("SOURCE_SHA_PIN_DRIFT")
 # Git checkout deliberately retains untracked files. Remove only the exact
 # previously injected research test before running untouched upstream CI.
 # This keeps the original suite a genuine no-extra-test baseline.
 leftover=d/"mathgraph_pr958_test.go"
 if leftover.exists():
  if leftover.read_bytes()!=(ROOT/"mathgraph_pr958_test.go").read_bytes():
   raise RuntimeError("UNEXPECTED_FOREIGN_UNTRACKED_TEST_SOURCE")
  leftover.unlink()
 # The original test suite runs before adding the MathGraph tests.
 native_suite,elapsed_suite=native(d,["go","test","-count=1","-timeout=10m","./..."],
      name+"_original_suite",timeout=720)
 REPORT["arms"].append({
  "arm":name,"source_sha":sha,
  "original_suite":{"passed":native_suite.returncode==0,
                    "exit_code":native_suite.returncode,"duration_s":elapsed_suite}
 })
 if native_suite.returncode!=0:
  raise RuntimeError("ORIGINAL_UPSTREAM_SUITE_NOT_GREEN_"+name)
 testfile=d/"mathgraph_pr958_test.go"
 testfile.write_bytes((ROOT/"mathgraph_pr958_test.go").read_bytes())
 if git(d,"status","--short","--untracked-files=all").splitlines()!=["?? mathgraph_pr958_test.go"]:
  raise RuntimeError("UNEXPECTED_UPSTREAM_SOURCE_CHANGE")
 command=["go","test","-json","-count=1","-timeout=8m",
          "-run","^TestMathGraph(NestedByteMarshalerInvariant|PreexistingScalarRiskNotAttributableToPR)$","."]
 proc,elapsed=native(d,command,name+"_native_checks",timeout=540)
 nested,examples=decode_subtests(proc.stdout,CASE_TYPE)
 inherited,ex2=decode_subtests(proc.stdout,INHERITED_TYPE)
 # Exact frozen matrix: 13 fragment names x 5 shapes x 2 indents.
 assert len(nested)==PROTOCOL["cases"]["expected"],(
  "NESTED_NATIVE_ORACLE_INCOMPLETE_"+name+"_"+str(len(nested)))
 assert len(inherited)==5,"INHERITED_NEGATIVE_CONTROL_INCOMPLETE"
 assert proc.returncode==int("fail" in list(nested.values())+list(inherited.values())), \
     "PROCESS_STATUS_INCONSISTENT_"+name
 a=REPORT["arms"][-1]
 a["native_test"]={
  "source_sha256":REPORT["native_test_sha256"],
  "nested_total":len(nested),
  "nested_pass":sum(v=="pass" for v in nested.values()),
  "nested_fail":sum(v=="fail" for v in nested.values()),
  "inherited_controls":inherited,
  "native_elapsed_s":elapsed,
  "exit_code":proc.returncode,
  "first_error_examples":examples
 }
 a["nested_cases"]=nested
 return nested,inherited,examples

def main():
 if REPO!="goccy/go-yaml" or PR!=958:
  raise RuntimeError("FROZEN_PR_SCOPE_CHANGED")
 d=checkout_sources()
 base,base_old,base_e=run_arm(d,"BASE",PROTOCOL["target"]["base"])
 head,head_old,head_e=run_arm(d,"PR_HEAD",PROTOCOL["target"]["head"])
 if set(base)!=set(head):raise RuntimeError("SUBCASE_IDENTITY_MISMATCH")
 # No prioritization based on a post-hoc definition of a "pass".
 controls={k for k in base if k.split("/")[0] in CONTROL_NAMES}
 if len(controls)!=20:raise RuntimeError("NO_SUFFICIENT_PLAIN_QUOTED_CONTROLS")
 if any(base[k]!="pass" or head[k]!="pass" for k in controls):
  raise RuntimeError("CONTROL_CASES_UNTRUSTWORTHY")
 introduced=sorted(k for k in base if base[k]=="pass" and head[k]=="fail")
 repaired=sorted(k for k in base if base[k]=="fail" and head[k]=="pass")
 unresolved=sorted(k for k in base if base[k]=="fail" and head[k]=="fail")
 stable=sorted(k for k in base if base[k]=="pass" and head[k]=="pass")
 inherited_consistent=(base_old==head_old)
 # For this target, pre-existing .nan/.inf failures must not be converted
 # into PR-attributed blocker; record both outcomes as a false-alarm control.
 if not inherited_consistent:
  raise RuntimeError("PR_HEAD_AFFECTED_INHERITED_CONTROL_REQUIRES_SEPARATE_REVIEW")
 finding=None
 if introduced:
  chosen=introduced[0] # fixed deterministic lexicographic tie-break
  finding={
   "code":"PR_INTRODUCED_BEHAVIORAL_REGRESSION_CANDIDATE",
   "case":chosen,"base":"pass","head":"fail",
   "evidence":head_e.get(chosen,""),
   "next_action":"Reproduce this exact native case alone and qualify a minimal repair with ablation. Do not merge until attributable failure is explained.",
   "merge_recommendation":"HOLD_FOR_EXACT_NATIVE_REPRODUCTION"
  }
 elif repaired:
  chosen=repaired[0]
  finding={
   "code":"PR_REPAIRS_PREEXISTING_BEHAVIOR_IN_SCOPED_NATIVE_TEST",
   "case":chosen,"base":"fail","head":"pass",
   "evidence":base_e.get(chosen,""),
   "next_action":"Review the contributor's tests and inspect remaining inherited failures separately; do not assert global safety.",
   "merge_recommendation":"NO_NEW_REGRESSION_IN_THIS_SCOPED_MATRIX"
  }
 else:
  finding={
   "code":"NO_ATTRIBUTABLE_CHANGE_IN_SCOPED_NATIVE_TESTS",
   "next_action":"No merge-blocking native witness from this test; seek other evidence/requirements.",
   "merge_recommendation":"UNKNOWN_WITHIN_OTHER_BEHAVIOR"
  }
 REPORT["decision"]={
  "introduced_regressions":len(introduced),
  "repaired_behaviors":len(repaired),
  "unresolved_preexisting":len(unresolved),
  "stable_cases":len(stable),
  "controls_passed":len(controls),
  "inherited_control_identical_between_arms":inherited_consistent,
  "finding":finding,
  "attribution_summary":{
   "new_regression_cases":introduced,
   "repaired_cases":repaired,
   "unresolved_cases":unresolved
  }
 }
 # Preserve full outcomes only in artifact. Summary is small and code-centric.
 print("MATHGRAPH_PR958_DECISION "+json.dumps({
  "source_base":PROTOCOL["target"]["base"],
  "source_head":PROTOCOL["target"]["head"],
  "introduced_regressions":len(introduced),
  "repaired_behaviors":len(repaired),
  "unresolved_preexisting":len(unresolved),
  "stable_cases":len(stable),
  "inherited_controls_same":inherited_consistent,
  "one_finding":finding
 },sort_keys=True),flush=True)
 REPORT["verdict"]=(
   "WARRANTED_BOUNDED_NEW_ATTRIBUTABLE_NATIVE_REGRESSION" if introduced else
   "WARRANTED_BOUNDED_NO_NEW_REGRESSION_IN_FIXED_MATRIX"
 )
 if os.environ.get("GITHUB_STEP_SUMMARY"):
  with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:
   f.write("### One consequential maintainer decision — external Go YAML PR #958\n\n")
   f.write("**Source-pinned real native Go tests; contributor patch not inspected before fixture froze.**\n\n")
   f.write("| Metric | Base | PR head |\n|---|---:|---:|\n")
   for arm in REPORT["arms"]:
    f.write("| Original test suite ("+arm["arm"]+") | "+("PASS" if arm["original_suite"]["passed"] else "FAIL")+" | exact SHA |\n")
   f.write("\nIntroduced regressions: "+str(len(introduced))+
           "; repaired cases: "+str(len(repaired))+
           "; unresolved inherited: "+str(len(unresolved))+
           "; stable: "+str(len(stable))+".\n")
   f.write("\n**One prioritized finding:** "+finding["code"]+
           ". Human-authored oracle; 130 bounded cases and five inherited controls; no universal safe-to-merge or autonomous method claim.\n")
 
try:main()
except Exception as e:
 REPORT["verdict"]="UNQUALIFIED_ENVIRONMENT_OR_NATIVE_TEST"
 REPORT["diagnostic"]=str(e)[:500]
 print("MATHGRAPH_PR958_UNQUALIFIED "+str(e)[:500],file=sys.stderr)
 (TMP/"REPORT.json").write_text(json.dumps(REPORT,indent=2)+"\n")
 sys.exit(1)
(TMP/"REPORT.json").write_text(json.dumps(REPORT,indent=2)+"\n")
