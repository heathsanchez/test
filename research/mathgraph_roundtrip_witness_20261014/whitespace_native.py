#!/usr/bin/env python3
"""Frozen five-arm YAML whitespace string-fidelity repair; original upstream source is read-only."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
PROTOCOL=json.loads((ROOT/"WHITESPACE_REPAIR_PROTOCOL.json").read_text())
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"mathgraph-yaml-whitespace-native"
OUT.mkdir(parents=True,exist_ok=True)
DIR=OUT/"checkout"
DIR.mkdir(exist_ok=True)
SHA="72a4f95c648c844ef2f8ddbc009530be64ab4c41"
ORIGINAL_BLOB="1ba8bf07b4859e49f4016551c63c9c8f76fa137f"
SPECIAL_BLOB="5d7df07558ef5e93c22a97d05a597a2dc00db389"
WHITESPACE_16=set(PROTOCOL["preexisting_oracle"]["exposed_residuals"])
SPECIAL_5={"keywords_023","keywords_024","keywords_025","keywords_026","keywords_027"}
EVIDENCE={
 "authority":"BOUNDED_HUMAN_SECOND_METHOD_VERIFIED_IF_ALL_GATES_PASS",
 "source_repo":PROTOCOL["source_repo"],
 "source_sha":SHA,
 "preregistered_whitespace_protocol_sha256":hashlib.sha256((ROOT/"WHITESPACE_REPAIR_PROTOCOL.json").read_bytes()).hexdigest(),
 "original_source_blob":ORIGINAL_BLOB,
 "prior_special_source_blob":SPECIAL_BLOB,
 "original_case_corpus_sha256":"86b3b2477024dec6cb57b82c3503d472132c5b50f2214bc34aa03afccfc8f2fe",
 "go_native_test_template_sha256":hashlib.sha256((ROOT/"metamorphic_test.go.txt").read_bytes()).hexdigest(),
 "no_upstream_writes":True,
 "not_autonomous_method_generation":True,
 "arms":[]
}
def git(*args):
 return subprocess.run(["git",*args],cwd=DIR,check=True,capture_output=True,text=True,timeout=250).stdout.strip()
def run(cmd,label,timeout=650):
 start=time.monotonic()
 p=subprocess.run(cmd,cwd=DIR,check=False,capture_output=True,text=True,
     env={**os.environ,"GOTOOLCHAIN":"auto"},timeout=timeout)
 (OUT/(label+".stdout.txt")).write_text(p.stdout)
 (OUT/(label+".stderr.txt")).write_text(p.stderr)
 return p,round(time.monotonic()-start,3)
def patch(source):
 inf_old=(
  'for _, keyword := range reservedInfKeywords {\n'
  '\t\treservedKeywordMap[keyword] = func(value, org string, pos *Position) *Token {\n'
  '\t\t\treturn reservedKeywordToken(InfinityType, value, org, pos)\n'
  '\t\t}\n'
  '\t}'
 )
 nan_old=(
  'for _, keyword := range reservedNanKeywords {\n'
  '\t\treservedKeywordMap[keyword] = func(value, org string, pos *Position) *Token {\n'
  '\t\t\treturn reservedKeywordToken(NanType, value, org, pos)\n'
  '\t\t}\n'
  '\t}'
 )
 for old in (inf_old,nan_old):
  assert source.count(old)==1,"SPECIAL_SOURCE_PATCH_ANCHOR_NOT_UNIQUE"
  new=old[:-2]+'\t\treservedEncKeywordMap[keyword] = reservedKeywordMap[keyword]\n\t}'
  # old[:-2] removes the loop's closing "\t}", not its new line:
  assert new.count("reservedEncKeywordMap[keyword]")==1
  source=source.replace(old,new,1)
 return source
def add_whitespace(s):
 old='func IsNeedQuoted(value string) bool {\n\tif value == "" {\n\t\treturn true\n\t}\n'
 added=old+'\tif strings.ContainsAny(value, "\\t\\r\\n") {\n\t\treturn true\n\t}\n'
 assert s.count(old)==1,"QUOTE_WHITESPACE_SOURCE_ANCHOR_NOT_UNIQUE"
 assert 'strings.ContainsAny(value, "\\t\\r\\n")' not in s
 return s.replace(old,added,1)
def test_case_set(arm,source,expected_fail):
 git("checkout","--force","--detach",SHA)
 assert git("rev-parse","HEAD")==SHA,"GIT_REVISION_CHANGED"
 p=DIR/"token/token.go"
 p.write_text(source)
 expected_blob=git("hash-object","token/token.go")
 if arm=="ORIGINAL" or arm=="ALL_CHANGES_REMOVED":
  assert expected_blob==ORIGINAL_BLOB
 if arm=="SPECIAL_ONLY" or arm=="WHITESPACE_REMOVED":
  assert expected_blob==SPECIAL_BLOB
 if arm=="SPECIAL_PLUS_WHITESPACE":
  assert expected_blob!=SPECIAL_BLOB and expected_blob!=ORIGINAL_BLOB
 paths=git("diff","--name-only").splitlines()
 assert paths==([] if expected_blob==ORIGINAL_BLOB else ["token/token.go"]), \
   "NON_TARGET_SOURCE_PATCH_IN_EXPERIMENT"
 native_test=(ROOT/"metamorphic_test.go.txt").read_text().replace(
   "@MODULE@","github.com/goccy/go-yaml")
 (DIR/"mathgraph_roundtrip_test.go").write_text(native_test)
 (DIR/"mathgraph_roundtrip_corpus.json").write_bytes(CORPUS_BYTES)
 result,elapsed=run(["go","test","-count=1","-json","-timeout=10m",
  "-run","^TestMathGraphStringRoundTrip$","."],arm)
 prefix="TestMathGraphStringRoundTrip/"
 statuses={}
 for line in result.stdout.splitlines():
  try:record=json.loads(line)
  except json.JSONDecodeError:continue
  name=record.get("Test","")
  if name.startswith(prefix) and record.get("Action") in ("fail","pass"):
   statuses[name[len(prefix):]]=record["Action"]
 assert set(statuses)==set(CASES),"NATIVE_SUBTEST_COMPLETENESS_"+arm+"_"+str(len(statuses))
 actual={x for x,v in statuses.items() if v=="fail"}
 errors=actual.symmetric_difference(expected_fail)
 row={
  "arm":arm,"source_sha":SHA,"token_blob":expected_blob,
  "native_test_sha256":EVIDENCE["go_native_test_template_sha256"],
  "case_corpus_sha256":EVIDENCE["original_case_corpus_sha256"],
  "case_count":len(statuses),
  "passed":len(statuses)-len(actual),"failed":len(actual),
  "failures_by_class":dict(Counter(CASES[x] for x in actual)),
  "unexpected_case_ids":sorted(errors),
  "exit_code":result.returncode,
  "runtime_s":elapsed,
  "qualified":actual==expected_fail and result.returncode==(1 if expected_fail else 0)
 }
 EVIDENCE["arms"].append(row)
 print("MATHGRAPH_WHITESPACE_NATIVE_ARM "+json.dumps(row,sort_keys=True),flush=True)
 if not row["qualified"]:raise RuntimeError("NATIVE_WHITESPACE_CASE_MISMATCH_"+arm)
 return source
def main():
 global CORPUS_BYTES,CASES
 assert PROTOCOL["source_repo"]=="goccy/go-yaml"
 assert PROTOCOL["exact_source_commit"]==SHA
 assert len(WHITESPACE_16)==16 and len(SPECIAL_5)==5
 manifest=json.loads((ROOT/"FROZEN_PROTOCOL.json").read_text())
 assert manifest["total_cases"]==1088,"FROZEN_CASE_COUNT_CHANGED"
 corpus_file=OUT/"roundtrip_cases.json"
 gen=subprocess.run(["python3",str(ROOT/"generate.py"),str(corpus_file)],
    capture_output=True,text=True,check=True,timeout=20)
 print(gen.stdout.strip(),flush=True)
 CORPUS_BYTES=corpus_file.read_bytes()
 assert hashlib.sha256(CORPUS_BYTES).hexdigest()==EVIDENCE["original_case_corpus_sha256"], \
    "FROZEN_CORPUS_DIGEST_MISMATCH"
 examples=json.loads(CORPUS_BYTES)
 CASES={x["id"]:x["kind"] for x in examples}
 assert len(CASES)==1088 and all(CASES[i]=="whitespace" for i in WHITESPACE_16)
 git("init","--quiet")
 git("remote","add","origin","https://github.com/goccy/go-yaml.git")
 git("-c","protocol.version=2","fetch","--quiet","--no-tags","--depth=1","origin",SHA)
 git("checkout","--force","--detach",SHA)
 assert git("rev-parse","HEAD")==SHA
 assert git("hash-object","token/token.go")==ORIGINAL_BLOB
 original=(DIR/"token/token.go").read_text()
 special=patch(original)
 test_case_set("ORIGINAL",original,SPECIAL_5|WHITESPACE_16)
 # The first patch must exactly reproduce its previously qualified Git blob.
 git("checkout","--force","--detach",SHA)
 (DIR/"token/token.go").write_text(special)
 assert git("hash-object","token/token.go")==SPECIAL_BLOB, \
   "FIRST_REPAIR_RECONSTRUCTION_MISMATCH"
 test_case_set("SPECIAL_ONLY",special,WHITESPACE_16)
 cumulative=add_whitespace(special)
 test_case_set("SPECIAL_PLUS_WHITESPACE",cumulative,set())
 # Full unchanged upstream Go suite plus new metamorphic tests.
 original_suite,t=run(["go","test","-count=1","-timeout=10m","./..."],
     "cumulative_original_full_suite",timeout=720)
 EVIDENCE["full_original_suite"]={
  "status":"PASS" if original_suite.returncode==0 else "FAIL",
  "exit_code":original_suite.returncode,"runtime_s":t
 }
 print("MATHGRAPH_WHITESPACE_FULL_SUITE "+json.dumps(
  EVIDENCE["full_original_suite"],sort_keys=True),flush=True)
 if original_suite.returncode!=0:
  raise RuntimeError("CUMULATIVE_PATCH_BREAKS_UNCHANGED_ORIGINAL_SUITE")
 test_case_set("WHITESPACE_REMOVED",special,WHITESPACE_16)
 test_case_set("ALL_CHANGES_REMOVED",original,SPECIAL_5|WHITESPACE_16)
 assert len(EVIDENCE["arms"])==5
 EVIDENCE["verdict"]="WARRANTED_BOUNDED_TWO_DISTINCT_HUMAN_REPAIRS_NATIVE_CAUSAL_ABLATION"
 EVIDENCE["method_generator_self_invention"]="UNKNOWN"
 EVIDENCE["source_to_multi_repo_transfer"]="UNKNOWN"
 print("MATHGRAPH_WHITESPACE_FINAL "+json.dumps({
   "verdict":EVIDENCE["verdict"],"failures":[r["failed"] for r in EVIDENCE["arms"]],
   "full_suite":EVIDENCE["full_original_suite"]["status"],
   "preserves_original_1088_cases":True
 },sort_keys=True),flush=True)
 if os.environ.get("GITHUB_STEP_SUMMARY"):
  with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:
   f.write("### Source-exact YAML two-stage string type-fidelity repair\n\n")
   for r in EVIDENCE["arms"]:
    f.write("- "+r["arm"]+": "+str(r["passed"])+"/1088 pass; "+
      str(r["failed"])+" fail, source blob "+r["token_blob"]+".\n")
   f.write("\nFull upstream Go test suite: "+EVIDENCE["full_original_suite"]["status"]+".\n")
   f.write("\nBoth repair operations were human-selected after seeing native witness failures. No upstream writes, product deployment, or L7 self-invention.\n")
try:
 main()
except Exception as error:
 EVIDENCE["verdict"]="UNQUALIFIED_OR_NATIVE_SEMANTIC_RESIDUAL"
 EVIDENCE["diagnostic"]=str(error)[:550]
 print("MATHGRAPH_WHITESPACE_UNQUALIFIED "+str(error)[:550],file=sys.stderr)
 (OUT/"REPORT.json").write_text(json.dumps(EVIDENCE,indent=2)+"\n")
 sys.exit(1)
(OUT/"REPORT.json").write_text(json.dumps(EVIDENCE,indent=2)+"\n")
