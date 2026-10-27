#!/usr/bin/env python3
"""Source-identified complete prefix for List.getElem?_eq_getElem, no proof rewrites."""
import json,hashlib,os,subprocess,sys
from pathlib import Path
ROOT=Path("/tmp/getelem")
ROOT.mkdir(parents=True,exist_ok=True)
DATA=ROOT/"path_reachable.ndjson"
PIN="96918fb408e535b34b50780d6b8fcbae51e5340659ec5a782d0cded926eae479"
TARGET="List.getElem?_eq_getElem"
OUT=ROOT/"evidence";OUT.mkdir(exist_ok=True)
LEDGER=Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
EXE="metatron-kernel/target/release/metatron-kernel"
OFF="/tmp/arena-reference/checkers/official/.lake/build/bin/kernel"
report={"status":"UNKNOWN","original_sha256":PIN,"target":TARGET,"results":{}}
try:
  data=DATA.read_bytes()
  assert hashlib.sha256(data).hexdigest()==PIN
  lines=data.splitlines(keepends=True)
  names={0:""};found=[]
  for i,line in enumerate(lines):
    item=json.loads(line)
    if "in" in item:
      obj=item.get("str") or item.get("num")
      if obj:
        parent=obj["pre"]
        assert parent in names
        names[item["in"]]=names[parent]+("." if parent else "")+str(obj.get("str",obj.get("i")))
    if "thm" in item and names.get(item["thm"]["name"])==TARGET:
      found.append((i,item["thm"]))
  assert len(found)==1,("target missing/duplicate",len(found))
  idx,thm=found[0]
  prefix=b"".join(lines[:idx+1])
  path=ROOT/"exact-source-prefix.ndjson";path.write_bytes(prefix)
  report["prefix"]={"record_count":idx+1,"length":len(prefix),"sha256":hashlib.sha256(prefix).hexdigest(),"theorem_record":thm}
  ledger=json.loads(LEDGER.read_text())
  base={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
  cases={"official":dict(base),"unmodified":dict(base),"historical-origin":dict(base),"combined-origin":dict(base),"combined-captured-pi":dict(base),"combined-lowbudget-pi":dict(base)}
  for nm in ("historical-origin","combined-origin","combined-captured-pi","combined-lowbudget-pi"):
    cases[nm].update({"NUCLEUS_EXPERIMENTAL_"+k:"1" for k in ledger["origin_flags"]})
    cases[nm]["NUCLEUS_EXPERIMENTAL_EXACT_PROOF_NEUTRALS"]="1"
  cases["combined-origin"]["NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA"]="1"
  cases["combined-origin"]["NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL"]="1"
  cases["combined-captured-pi"]["NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA"]="1"
  cases["combined-captured-pi"]["NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL"]="1"
  cases["combined-captured-pi"]["NUCLEUS_EXPERIMENTAL_CAPTURED_PI_RECOVERY"]="1"
  cases["combined-captured-pi"]["NUCLEUS_TRACE_CAPTURED_PI_RECOVERY"]="1"
  cases["combined-captured-pi"]["NUCLEUS_TRACE_FAILED_RECEIVER_CONVERSION"]="1"
  cases["combined-captured-pi"]["NUCLEUS_TRACE_EXACT_PROJECTION"]="1"
  cases["combined-captured-pi"]["NUCLEUS_TRACE_SOURCE_CAPTURE_TARGET"]="1"
  cases["combined-lowbudget-pi"].update(cases["combined-captured-pi"])
  cases["combined-lowbudget-pi"]["NUCLEUS_EXPERIMENTAL_CAPTURED_PI_LOWBUDGET"]="1"
  for nm,env in cases.items():
    cmd=[OFF,str(path)] if nm=="official" else [EXE]
    if nm!="official":
      env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
      env["NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE"]="1"
      env["NUCLEUS_TRACE_NEUTRAL_HEADS"]="1"
      env["NUCLEUS_TRACE_VALUE_MISMATCH"]="1"
      env["NUCLEUS_TRACE_EXACT_PROOF_NEUTRALS"]="1"
    p=subprocess.run(cmd,input=None if nm=="official" else prefix,env=env,capture_output=True,timeout=210)
    r={"exit_code":p.returncode,"stderr_tail":p.stderr.decode(errors="replace")[-48000:],"stdout_tail":p.stdout.decode(errors="replace")[-1500:]}
    report["results"][nm]=r
    print(nm,r["exit_code"],r["stderr_tail"][-5500:],flush=True)
    if nm=="official":assert p.returncode==0,("official source invalid",r)
    else:assert p.returncode in (0,2),("valid source REJECT/crash",nm,r)
  report["status"]="WARRANTED_SOURCE_PINNED_FIRST_GETELEM_OBSTRUCTION"
  rc=0
except Exception as e:
  report["error"]=repr(e);rc=1
finally:
  (OUT/"getelem-prefix-report.json").write_text(json.dumps(report,indent=2)+"\n")
  print("FINAL",report["status"],flush=True)
sys.exit(rc)
