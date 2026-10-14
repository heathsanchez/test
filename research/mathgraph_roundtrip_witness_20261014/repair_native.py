#!/usr/bin/env python3
"""Native source-exact human-designed repair of independently generated YAML type-fidelity witnesses.

NO upstream writes. No claim of autonomous method invention or unseen upstream prior art.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
FROZEN=json.loads((ROOT/"SPECIAL_SCALAR_REPAIR_PROTOCOL.json").read_text())
PRIOR=json.loads((ROOT/"FROZEN_PROTOCOL.json").read_text())
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"mathgraph-special-scalar-repair-native"
OUT.mkdir(parents=True,exist_ok=True)
WORK=OUT/"checkout"
WORK.mkdir(exist_ok=True)
PIN="72a4f95c648c844ef2f8ddbc009530be64ab4c41"
ORIGINAL_BLOB="1ba8bf07b4859e49f4016551c63c9c8f76fa137f"
SPECIALS={ "string_.nan","string_.NaN","string_.NAN","string_.inf","string_-.inf" }
FLOAT_CONTROLS={"float_nan","float_positive_inf","float_negative_inf"}
STRING_CONTROLS={"string_control_.nanny","string_control_.infinite","string_control_normal","string_control_null","string_control_true"}
# Actual Go subtest IDs include the fixed "string_control_" prefix.
STRING_CONTROLS={"string_control_"+name for name in [".nanny",".infinite","normal","null","true"]}
ALL_TESTS=SPECIALS|FLOAT_CONTROLS|STRING_CONTROLS
REPAIR_SNIPPETS={
 "inf":(
  'for _, keyword := range reservedInfKeywords {\n'
  '\t\treservedKeywordMap[keyword] = func(value, org string, pos *Position) *Token {\n'
  '\t\t\treturn reservedKeywordToken(InfinityType, value, org, pos)\n'
  '\t\t}\n'
  '\t}',
  'for _, keyword := range reservedInfKeywords {\n'
  '\t\treservedKeywordMap[keyword] = func(value, org string, pos *Position) *Token {\n'
  '\t\t\treturn reservedKeywordToken(InfinityType, value, org, pos)\n'
  '\t\t}\n'
  '\t\treservedEncKeywordMap[keyword] = reservedKeywordMap[keyword]\n'
  '\t}'
 ),
 "nan":(
  'for _, keyword := range reservedNanKeywords {\n'
  '\t\treservedKeywordMap[keyword] = func(value, org string, pos *Position) *Token {\n'
  '\t\t\treturn reservedKeywordToken(NanType, value, org, pos)\n'
  '\t\t}\n'
  '\t}',
  'for _, keyword := range reservedNanKeywords {\n'
  '\t\treservedKeywordMap[keyword] = func(value, org string, pos *Position) *Token {\n'
  '\t\t\treturn reservedKeywordToken(NanType, value, org, pos)\n'
  '\t\t}\n'
  '\t\treservedEncKeywordMap[keyword] = reservedKeywordMap[keyword]\n'
  '\t}'
 )
}
EVIDENCE={
 "authority":"WARRANTED_BOUNDED_NATIVE_HUMAN_REPAIR_IF_ALL_GATES_PASS",
 "fix_provenance":"Human-selected known source-level fix after a general test generator found 5 target-only candidates. Not an autonomously invented repair.",
 "source_repo":"goccy/go-yaml","source_sha":PIN,
 "source_original_blob":ORIGINAL_BLOB,
 "protocol_sha256":hashlib.sha256((ROOT/"SPECIAL_SCALAR_REPAIR_PROTOCOL.json").read_bytes()).hexdigest(),
 "new_test_sha256":hashlib.sha256((ROOT/"special_scalar_fidelity_test.go").read_bytes()).hexdigest(),
 "original_generator_sha256":hashlib.sha256((ROOT/"generate.py").read_bytes()).hexdigest(),
 "upstream_writes":0,
 "arms":[]
}
def git(*args):
 p=subprocess.run(["git",*args],cwd=WORK,check=True,capture_output=True,text=True,timeout=260)
 return p.stdout.strip()
def native(cmd,label,timeout=720):
 start=time.monotonic()
 p=subprocess.run(cmd,cwd=WORK,capture_output=True,text=True,
                  timeout=timeout,env={**os.environ,"GOTOOLCHAIN":"auto"})
 (OUT/(label+".stdout.txt")).write_text(p.stdout)
 (OUT/(label+".stderr.txt")).write_text(p.stderr)
 return p,round(time.monotonic()-start,2)
def subtests(text,prefix):
 found={}
 for line in text.splitlines():
  try:msg=json.loads(line)
  except json.JSONDecodeError:continue
  name=msg.get("Test","")
  if name.startswith(prefix) and msg.get("Action") in ("pass","fail"):
   found[name[len(prefix):]]=msg["Action"]
 return found
def evaluate(label,expect_failed):
 assert git("rev-parse","HEAD")==PIN,"PINNED_HEAD_DRIFT"
 test=WORK/"mathgraph_special_scalar_test.go"
 test.write_bytes((ROOT/"special_scalar_fidelity_test.go").read_bytes())
 p,time_s=native(["go","test","-count=1","-timeout=8m","-json",
                   "-run","^TestMathGraphSpecialScalarStringFidelity$","."],label)
 cases=subtests(p.stdout,"TestMathGraphSpecialScalarStringFidelity/")
 got_failed={x for x,v in cases.items() if v=="fail"}
 assert set(cases)==ALL_TESTS,"NATIVE_CASES_INCOMPLETE_"+label+"_"+repr(cases)
 expected={name:("fail" if name in expect_failed else "pass") for name in ALL_TESTS}
 qualified=(cases==expected and p.returncode==(1 if expect_failed else 0))
 row={
   "arm":label,"sha":PIN,"source_blob":git("hash-object","token/token.go"),
   "native_test_sha256":EVIDENCE["new_test_sha256"],
   "cases":len(cases),"passed":len(cases)-len(got_failed),
   "failed":len(got_failed),"failed_ids":sorted(got_failed),
   "negative_controls_passed":all(cases[x]=="pass" for x in FLOAT_CONTROLS|STRING_CONTROLS),
   "go_test_exit_code":p.returncode,"duration_seconds":time_s,
   "qualified":qualified
 }
 EVIDENCE["arms"].append(row)
 print("MATHGRAPH_SPECIAL_REPAIR_ARM "+json.dumps(row,sort_keys=True),flush=True)
 if not qualified:raise RuntimeError("SOURCE_NATIVE_EXPECTATION_MISMATCH_"+label)

def full_package_suite():
 # Keep native original upstream Go tests separate from the new witness.
 test=WORK/"mathgraph_special_scalar_test.go"
 if test.exists():test.unlink()
 p,t=native(["go","test","-count=1","-timeout=10m","./..."],"fixed_original_full_suite",timeout=700)
 success=p.returncode==0
 EVIDENCE["full_original_package_suite"]={
  "command":"go test -count=1 -timeout=10m ./...","status":"PASS" if success else "FAIL",
  "exit_code":p.returncode,"duration_seconds":t
 }
 print("MATHGRAPH_SPECIAL_REPAIR_ORIGINAL_FULL_SUITE "+json.dumps(
   EVIDENCE["full_original_package_suite"],sort_keys=True),flush=True)
 if not success:raise RuntimeError("FULL_ORIGINAL_SUITE_RED_QUALIFICATION_BLOCKED")

def replay_original_1088():
 from collections import Counter
 generated=OUT/"roundtrip_cases.json"
 p=subprocess.run(["python3",str(ROOT/"generate.py"),str(generated)],
                  capture_output=True,text=True,check=True,timeout=30)
 cases=json.loads(generated.read_text())
 assert len(cases)==1088
 types={x["id"]:x["kind"] for x in cases}
 assert len(types)==1088
 corpus_hash=hashlib.sha256(generated.read_bytes()).hexdigest()
 assert corpus_hash=="86b3b2477024dec6cb57b82c3503d472132c5b50f2214bc34aa03afccfc8f2fe"
 EVIDENCE["original_case_corpus_sha256"]=corpus_hash
 original_template=(ROOT/"metamorphic_test.go.txt").read_text()
 original_source=original_template.replace("@MODULE@","github.com/goccy/go-yaml")
 native_file=WORK/"mathgraph_roundtrip_test.go"
 native_file.write_text(original_source)
 (WORK/"mathgraph_roundtrip_corpus.json").write_bytes(generated.read_bytes())
 for arm in ("BASE_1088","FIXED_1088","ABLATED_1088"):
  git("checkout","--force","--detach",PIN)
  if arm=="FIXED_1088":
   (WORK/"token/token.go").write_text(EVIDENCE["patched_source_text"])
  # Deliberately reset before ablation to get the exact original source blob.
  if arm in ("BASE_1088","ABLATED_1088"):
   assert git("hash-object","token/token.go")==ORIGINAL_BLOB
  (WORK/"mathgraph_roundtrip_test.go").write_text(original_source)
  (WORK/"mathgraph_roundtrip_corpus.json").write_bytes(generated.read_bytes())
  test,result_s=native(["go","test","-count=1","-timeout=10m","-json",
                        "-run","^TestMathGraphStringRoundTrip$","."],arm)
  status=subtests(test.stdout,"TestMathGraphStringRoundTrip/")
  assert set(status)==set(types),"ORIGINAL_METAMORPHIC_CASES_INCOMPLETE_"+arm
  failed={x for x,v in status.items() if v=="fail"}
  counter=Counter(types[x] for x in failed)
  expected_count=16 if arm=="FIXED_1088" else 21
  expected_special=set() if arm=="FIXED_1088" else {
   "keywords_023","keywords_024","keywords_025","keywords_026","keywords_027"
  }
  actual_special={x for x in failed if x in {
   "keywords_023","keywords_024","keywords_025","keywords_026","keywords_027"
  }}
  assert len(failed)==expected_count and actual_special==expected_special, \
    "METAMORPHIC_FIX_ONLY_EXPECTED_RESIDUALS_"+arm+"_"+str(len(failed))
  assert (test.returncode==1)==bool(failed),"METAMORPHIC_PROCESS_EXIT_"+arm
  row={"arm":arm,"failed":len(failed),"passed":1088-len(failed),
       "by_kind":dict(counter),"failed_case_ids":sorted(failed),
       "source_sha":PIN,"source_blob":git("hash-object","token/token.go"),
       "duration_s":result_s}
  EVIDENCE.setdefault("original_1088_replay",[]).append(row)
  print("MATHGRAPH_SPECIAL_REPAIR_1088 "+json.dumps({
   **row,"failed_case_ids":sorted(failed)[:25]
  },sort_keys=True),flush=True)

def main():
 assert FROZEN["discovery_basis"]["repo_commit"]==PIN
 assert FROZEN["allowed_source_file"]=="token/token.go"
 assert PRIOR["total_cases"]==1088
 assert (ROOT/"special_scalar_fidelity_test.go").is_file()
 git("init","--quiet")
 git("remote","add","origin","https://github.com/goccy/go-yaml.git")
 git("-c","protocol.version=2","fetch","--quiet","--no-tags","--depth=1","origin",PIN)
 git("checkout","--force","--detach",PIN)
 assert git("rev-parse","HEAD")==PIN,"ORIGINAL_SOURCE_SHA_MISMATCH"
 assert git("hash-object","token/token.go")==ORIGINAL_BLOB,"ORIGINAL_SOURCE_BLOB_MISMATCH"
 original=(WORK/"token/token.go").read_text()
 modified=original
 for category,(old,new) in REPAIR_SNIPPETS.items():
  assert modified.count(old)==1,"REPAIR_ANCHOR_NOT_UNIQUE_"+category
  modified=modified.replace(old,new,1)
 assert modified!=original
 EVIDENCE["patched_source_sha256"]=hashlib.sha256(modified.encode()).hexdigest()
 EVIDENCE["patched_source_text"]=modified
 evaluate("BASE",SPECIALS)
 (WORK/"token/token.go").write_text(modified)
 assert git("diff","--name-only").splitlines()==["token/token.go"], \
    "REPAIR_SCOPE_MORE_THAN_ONE_IMPLEMENTATION_FILE"
 evaluate("PATCHED",set())
 full_package_suite()
 # Remove implementation patch without changing test bytes.
 git("checkout","--force","--detach",PIN)
 assert git("hash-object","token/token.go")==ORIGINAL_BLOB, \
    "SOURCE_REVERT_DID_NOT_RESTORE_BLOB"
 evaluate("ABLATED",SPECIALS)
 assert len(EVIDENCE["arms"])==3
 replay_original_1088()
 EVIDENCE.pop("patched_source_text")
 EVIDENCE["verdict"]="WARRANTED_BOUNDED_NATIVE_HUMAN_REPAIR_WITH_ABLATION"
 EVIDENCE["autonomous_method_genesis"]="UNKNOWN"
 EVIDENCE["upstream_repair_published"]=False
 print("MATHGRAPH_SPECIAL_REPAIR_FINAL "+json.dumps({
   "verdict":EVIDENCE["verdict"],
   "special_test_arms":3,"failing_string_before":5,
   "failing_string_after":0,"failing_string_revert":5,
   "full_suite":EVIDENCE["full_original_package_suite"]["status"],
   "original_1088_failures":[x["failed"] for x in EVIDENCE["original_1088_replay"]],
   "autonomous_method_genesis":"UNKNOWN"
 },sort_keys=True),flush=True)
 if os.environ.get("GITHUB_STEP_SUMMARY"):
  with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:
   f.write("### Exact native repair and ablation — special scalar type fidelity\n\n")
   for row in EVIDENCE["arms"]:
    f.write("- "+row["arm"]+": "+str(row["passed"])+"/13 native cases passed; fail "+str(row["failed"])+".\n")
   f.write("- Original 1088 metamorphic cases before/fixed/ablation: "+
      "/".join(str(x["failed"]) for x in EVIDENCE["original_1088_replay"])+" failures.\n")
   f.write("- Full original Go suite after scoped repair: "+
     EVIDENCE["full_original_package_suite"]["status"]+".\n\n")
   f.write("Known limits: human-designed repair; 16 pre-existing whitespace failures remain; no autonomous generator self-invention, third-party code writes, or upstream disclosures.\n")
try:main()
except Exception as err:
 EVIDENCE.pop("patched_source_text",None)
 EVIDENCE["verdict"]="UNQUALIFIED_NATIVE_OR_SOURCE_BOUNDARY"
 EVIDENCE["diagnostic"]=str(err)[:500]
 print("MATHGRAPH_SPECIAL_REPAIR_UNQUALIFIED "+str(err)[:500],file=sys.stderr)
 (OUT/"REPORT.json").write_text(json.dumps(EVIDENCE,indent=2)+"\n")
 sys.exit(1)
(OUT/"REPORT.json").write_text(json.dumps(EVIDENCE,indent=2)+"\n")
