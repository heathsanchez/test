#!/usr/bin/env python3
"""One-file native repair + causal ablation for pre-existing go-yaml issue #872.

Does not change upstream PR #958, upstream issues or the live MathGraph App.
Tests existing first-party Go suite, independent 130-case nested-Marshal oracle,
and unchanged inherited-special-scalar negative controls.
"""
import hashlib,json,os
from pathlib import Path
import subprocess,sys,time

ROOT=Path(__file__).resolve().parent
PLAN=json.loads((ROOT/"INHERITED_KEEP_CHOMPING_REPAIR_FROZEN.json").read_text())
PR=json.loads((ROOT/"FROZEN_PROTOCOL.json").read_text())
TMP=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"mathgraph-go-yaml-issue872-repair"
TMP.mkdir(exist_ok=True,parents=True)
WORK=TMP/"checkout"
WORK.mkdir(exist_ok=True)
SHA="a34b94ecb553bb5a693296c30232a89026db79ca"
TEST=ROOT/"mathgraph_pr958_test.go"
TEST_SHA=hashlib.sha256(TEST.read_bytes()).hexdigest()
FILE="ast/ast.go"
CHOMP_IDS={
 f"{mode}_chomp_keep/shape{s}_indent{i}"
 for mode in ("literal","folded") for s in range(5) for i in (2,4)
}
RECORD={
 "authority":"WARRANTED_BOUNDED_NATIVE_HUMAN_SEPARATE_ISSUE_REPAIR_IF_ALL_GATES_PASS",
 "target":"goccy/go-yaml#958",
 "related_preexisting_issue":"goccy/go-yaml#872",
 "exact_pr_head":SHA,
 "protocol_sha256":hashlib.sha256((ROOT/"INHERITED_KEEP_CHOMPING_REPAIR_FROZEN.json").read_bytes()).hexdigest(),
 "test_source_sha256":TEST_SHA,
 "external_writes":0,
 "tests":[],
 "not_autonomous_repair":True
}
def git(*args):
 return subprocess.run(["git",*args],cwd=WORK,check=True,
    capture_output=True,text=True,timeout=230).stdout.strip()

def native(name,arguments,timeout=700):
 now=time.monotonic()
 result=subprocess.run(arguments,cwd=WORK,capture_output=True,text=True,
    timeout=timeout,env={**os.environ,"GOTOOLCHAIN":"auto"})
 (TMP/(name+".stdout")).write_text(result.stdout)
 (TMP/(name+".stderr")).write_text(result.stderr)
 return result,round(time.monotonic()-now,3)

def outcome(output,prefix,depth):
 data={}
 first={}
 for line in output.splitlines():
  try:x=json.loads(line)
  except json.JSONDecodeError:continue
  test=x.get("Test","")
  if not test.startswith(prefix):continue
  suffix=test[len(prefix):]
  if suffix.count("/")!=depth:continue
  if x.get("Action") in ("pass","fail"):data[suffix]=x["Action"]
  if x.get("Action")=="output" and ("nested encoding" in x.get("Output","") or
     "nested fragment" in x.get("Output","") or "inherited string" in x.get("Output","")):
   first.setdefault(suffix,x["Output"].strip()[:420])
 return data,first

def run_case(arm,expected_failure):
 extra=WORK/"mathgraph_pr958_test.go"
 extra.write_bytes(TEST.read_bytes())
 result,time_s=native(arm,["go","test","-count=1","-json","-timeout=8m",
   "-run","^TestMathGraph(NestedByteMarshalerInvariant|PreexistingScalarRiskNotAttributableToPR)$","."],500)
 nested,evidence=outcome(result.stdout,"TestMathGraphNestedByteMarshalerInvariant/",1)
 inherited,_=outcome(result.stdout,"TestMathGraphPreexistingScalarRiskNotAttributableToPR/",0)
 assert len(nested)==130,"NESTED_COVERAGE_INCOMPLETE_"+arm+"_"+str(len(nested))
 assert len(inherited)==5,"INHERITED_COVERAGE_INCOMPLETE_"+arm
 nested_failed={key for key,status in nested.items() if status=="fail"}
 inherited_failed={key for key,status in inherited.items() if status=="fail"}
 assert inherited_failed=={
   "string_.nan","string_.NaN","string_.NAN","string_.inf","string_-.inf"
 },"INHERITED_SOURCE_BEHAVIOR_CHANGED_"+arm
 valid=nested_failed==expected_failure and result.returncode==1
 row={
  "arm":arm,"source_sha":SHA,"source_blob":git("hash-object",FILE),
  "test_sha256":TEST_SHA,"nested_pass":130-len(nested_failed),
  "nested_failed":len(nested_failed),"nested_failed_case_ids":sorted(nested_failed),
  "inherited_failures":len(inherited_failed),
  "native_exit":result.returncode,"elapsed_seconds":time_s,
  "qualified":valid
 }
 RECORD["tests"].append(row)
 print("MATHGRAPH_ISSUE872_NATIVE_ARM "+json.dumps(row,sort_keys=True),flush=True)
 if not valid:raise RuntimeError("SOURCE_NATIVE_WITNESS_MISMATCH_"+arm)
 return nested_failed

def main():
 assert PLAN["source"]["commit"]==SHA and PR["target"]["head"]==SHA
 assert len(CHOMP_IDS)==20 and PLAN["source"]["file"]==FILE
 git("init","--quiet")
 git("remote","add","origin","https://github.com/goccy/go-yaml.git")
 git("-c","protocol.version=2","fetch","--quiet","--no-tags","--depth=1","origin",SHA)
 git("checkout","--force","--detach",SHA)
 assert git("rev-parse","HEAD")==SHA
 source=(WORK/FILE).read_text()
 initial_blob=git("hash-object",FILE)
 old='\tlit := strings.TrimRight(strings.TrimRight(origin, " "), "\\n")'
 assert source.count(old)==1,"CHOMPING_SOURCE_REPAIR_ANCHOR_NOT_UNIQUE"
 new=(
  '\tlit := strings.TrimRight(origin, " ")\n'
  '\tif strings.Contains(n.Start.Value, "+") {\n'
  '\t\t// Keep chomping retains blank lines. The final newline is supplied\n'
  '\t\t// by the enclosing YAML printer.\n'
  '\t\tlit = strings.TrimSuffix(lit, "\\n")\n'
  '\t} else {\n'
  '\t\tlit = strings.TrimRight(lit, "\\n")\n'
  '\t}'
 )
 candidate=source.replace(old,new,1)
 assert candidate!=source
 RECORD["original_ast_blob"]=initial_blob
 RECORD["patched_source_sha256"]=hashlib.sha256(candidate.encode()).hexdigest()
 run_case("PR_HEAD_ORIGINAL",CHOMP_IDS)
 (WORK/FILE).write_text(candidate)
 changed=git("diff","--name-only").splitlines()
 assert changed==[FILE],"SOURCE_PATCH_ESCAPED_SINGLE_FILE_"+repr(changed)
 run_case("ISSUE872_CANDIDATE_PATCH",set())
 # Run the unchanged project tests only, without our expected-to-fail
 # inherited controls.
 (WORK/"mathgraph_pr958_test.go").unlink()
 original,time_s=native("PATCHED_ORIGINAL_UPSTREAM_GO_TESTS",
     ["go","test","-count=1","-timeout=10m","./..."],700)
 RECORD["original_suite"]={
   "exit":original.returncode,
   "passed":original.returncode==0,
   "runtime_s":time_s
 }
 print("MATHGRAPH_ISSUE872_ORIGINAL_SUITE "+json.dumps(RECORD["original_suite"]),flush=True)
 if original.returncode!=0:
  raise RuntimeError("EXISTING_UPSTREAM_GO_SUITE_FAILED_UNDER_PROPOSED_PATCH")
 # Causal ablation uses exact HEAD blob (not synthetic modified code).
 git("checkout","--force","--detach",SHA)
 assert git("hash-object",FILE)==initial_blob,"SOURCE_ABLATION_NOT_EXACT"
 run_case("ONE_FILE_PATCH_REMOVED",CHOMP_IDS)
 RECORD["verdict"]="WARRANTED_BOUNDED_NATIVE_REPAIR_FOR_SEPARATE_PREEXISTING_ISSUE_872"
 RECORD["maintainer_next_action"]="PR #958 can be judged independently; submit a separate scoped issue #872 repair for explicit upstream review. Do not block PR #958 solely on inherited known issue."
 print("MATHGRAPH_ISSUE872_FINAL "+json.dumps({
   "verdict":RECORD["verdict"],
   "original_failed":20,"patched_failed":0,"ablated_failed":20,
   "original_go_suite_passed":True,
   "separate_issue":"goccy/go-yaml#872",
   "upstream_writes":0
 },sort_keys=True),flush=True)
 if os.environ.get("GITHUB_STEP_SUMMARY"):
  with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as fd:
   fd.write("### PR #958 one consequential decision — separate inherited issue #872\n\n")
   fd.write("This is a human-designed candidate repair, not autonomous inference.\n\n")
   for x in RECORD["tests"]:
    fd.write("- "+x["arm"]+": "+str(x["nested_pass"])+"/130 nested checks, "+
      str(x["inherited_failures"])+"/5 unchanged inherited negative controls.\n")
   fd.write("\nOriginal project tests under candidate patch: PASS.\n")
   fd.write("**Recommended action:** review issue #872 separately, do not blame or block PR #958 for a preexisting out-of-scope issue.\n")

try:main()
except Exception as e:
 RECORD["verdict"]="UNQUALIFIED_NATIVE_REPAIR_OR_FALSE_PREMISE"
 RECORD["diagnostic"]=str(e)[:550]
 print("MATHGRAPH_ISSUE872_UNQUALIFIED "+str(e)[:550],file=sys.stderr)
 (TMP/"REPORT.json").write_text(json.dumps(RECORD,indent=2)+"\n")
 sys.exit(1)
(TMP/"REPORT.json").write_text(json.dumps(RECORD,indent=2)+"\n")
