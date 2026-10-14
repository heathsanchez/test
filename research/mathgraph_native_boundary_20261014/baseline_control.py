#!/usr/bin/env python3
"""Post-hoc untouched upstream baseline suite controls; distinct from frozen six-arm experiment."""
import json, os, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/"FROZEN_PROTOCOL.json").read_text())
tmp=Path(os.environ.get("RUNNER_TEMP","/tmp"))
work=tmp/"mathgraph-native-original-test-checkouts"
out=tmp/"mathgraph-native-original-suite-controls"
work.mkdir(parents=True,exist_ok=True)
out.mkdir(parents=True,exist_ok=True)
results=[]
try:
 for item in manifest["target_repositories"]:
  repo=item["repo"]
  name=repo.replace("/","__")
  d=work/name
  d.mkdir()
  def git(*args):
   p=subprocess.run(["git",*args],cwd=d,capture_output=True,text=True,timeout=240,check=True)
   return p.stdout.strip()
  git("init","--quiet")
  git("remote","add","origin","https://github.com/"+repo+".git")
  git("-c","protocol.version=2","fetch","--quiet","--no-tags","--depth=1","origin",item["base_sha"])
  git("checkout","--force","--detach",item["base_sha"])
  assert git("rev-parse","HEAD")==item["base_sha"],"BASE_SHA_MISMATCH"
  assert git("hash-object",str(d/item["ablate_file"]))==item["base_blob"],"SOURCE_FILE_CHANGED"
  start=time.monotonic()
  p=subprocess.run(["go","test","-count=1","-timeout=12m","-json",item["package"]],
    cwd=d,capture_output=True,text=True,timeout=840,
    env={**os.environ,"GOTOOLCHAIN":"auto"})
  (out/(name+".jsonl")).write_text(p.stdout)
  (out/(name+".stderr.txt")).write_text(p.stderr)
  event=[]
  for line in p.stdout.splitlines():
   try:
    e=json.loads(line)
    if e.get("Action") in ("pass","fail") and e.get("Test"):event.append(e)
   except json.JSONDecodeError:pass
  tested=len({e["Test"] for e in event if e["Action"]=="pass" and "/" not in e["Test"]})
  failed=sorted({e["Test"] for e in event if e["Action"]=="fail"})
  result={"repo":repo,"source_sha":item["base_sha"],
          "native_suite":"go test -count=1 -timeout=12m -json "+item["package"],
          "returncode":p.returncode,"passed_tests":tested,"failed_tests":failed,
          "duration_s":round(time.monotonic()-start,2)}
  results.append(result)
  print("MATHGRAPH_UNTOUCHED_BASE_SUITE "+json.dumps(result),flush=True)
  if p.returncode!=0 or tested<1 or failed:
   raise RuntimeError("UNCHANGED_ORIGINAL_TEST_SUITE_NOT_GREEN_"+name)
 report={"authority":"POST_HOC_UNCHANGED_UPSTREAM_BASE_TEST_SUITE_CONTROL",
         "not_part_of_preregistered_six_arms":True,"all_green":True,
         "baseline_repos":results,
         "interpretation":"The original full package tests passed at source revisions where separately authored boundary tests fail; no independent blind discovery, no stateless-agent superiority established."}
 (out/"REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
 print("MATHGRAPH_UNCHANGED_SUITES_RESULT "+json.dumps({"all_green":True,"repos":len(results)}),flush=True)
 if os.environ.get("GITHUB_STEP_SUMMARY"):
  with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:
   f.write("### Original upstream native package tests (post-hoc control)\n\n")
   for x in results:f.write("- "+x["repo"]+" @ "+x["source_sha"]+": "+str(x["passed_tests"])+
           " native Go tests passed, elapsed "+str(x["duration_s"])+" s\n")
   f.write("\n**Separate from six-arm preregistered calibration.**\n")
except Exception as e:
 (out/"REPORT.json").write_text(json.dumps({
  "authority":"POST_HOC_CONTROL_UNQUALIFIED","results":results,"error":str(e)[:450]},indent=2)+"\n")
 print("MATHGRAPH_UNTOUCHED_SUITES_UNQUALIFIED "+str(e)[:450],file=sys.stderr)
 sys.exit(1)
