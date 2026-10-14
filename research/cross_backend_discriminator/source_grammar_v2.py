#!/usr/bin/env python3
"""Human-written source-test literal miner + native cross-implementation probe.

NO manually embedded operation names or expression prefixes. Source-author
strings in newly added tests are admitted by native jq syntax validation.
All source pins/runner roles provided outside algorithm by an auditable manifest.
This is not autonomous generator invention or proof of general semantics.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, subprocess, sys, time
Q=re.compile(r'r(#{0,4})"([^"\n]*?)"\1|(?<![A-Za-z0-9_])"((?:\\.|[^"\\\n])*)"')
BT=re.compile(chr(96)+"([^\\n]{1,240})"+chr(96))
JMACRO=re.compile(r'json!\(\s*(\[[^\n]{0,140}\]|\{[^\n]{0,140}\}|null|true|false|[0-9]{1,5})\s*\)')
SEEDS=[None,[],[0],[1],[1,2,3],{},{"a":1},{"a":[1]},"","ab",0,1]
LIMIT_FILTERS,LIMIT_INPUTS=20,12
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def digest(b):return hashlib.sha256(b).hexdigest()
def need(c,s):
 if not c:raise ValueError(s)
def exact(repo,sha):
 p=subprocess.run(["git","-C",repo,"rev-parse","HEAD"],text=True,capture_output=True,timeout=10)
 need(p.returncode==0 and p.stdout.strip()==sha,"ORIGINAL_SOURCE_PIN_MISMATCH")
def literals(line):
 out=[]
 for m in Q.finditer(line):
  if m.group(2) is not None:v=m.group(2)
  else:
   try:v=json.loads('"'+m.group(3)+'"')
   except ValueError:continue
  if v and len(v)<=240 and "\n" not in v:out.append(v)
 for m in BT.finditer(line):out.append(m.group(1))
 return out
def test_literals(diff):
 found=[];authored=[];origins=[];allowed=False;file=""
 for i,line in enumerate(diff.splitlines(),1):
  if line.startswith("+++ b/"):
   file=line[6:];base=pathlib.PurePosixPath(file).name.lower()
   allowed=(file.endswith(".rs") and ("test" in file.lower() or "spec" in file.lower())) or base.endswith("_test.go")
  elif allowed and line.startswith("+") and not line.startswith("+++"):
   for s in literals(line[1:]):
    found.append(s);origins.append({"path":file,"line_in_diff":i,"literal_sha256":digest(s.encode())})
    try:authored.append(json.loads(s))
    except ValueError:pass
   for m in JMACRO.finditer(line[1:]):
    try:authored.append(json.loads(m.group(1)))
    except ValueError:pass
 return found,authored,origins
def proc(argv,stdin=None,timeout=1.2):
 t=time.monotonic()
 safe={k:v for k,v in os.environ.items() if not any(n in k for n in ("TOKEN","SECRET","PRIVATE_KEY"))}
 try:z=subprocess.run(argv,input=stdin,text=True,capture_output=True,timeout=timeout,check=False,env=safe)
 except subprocess.TimeoutExpired:return {"status":"TIMEOUT_UNKNOWN","elapsed":round(time.monotonic()-t,4)}
 except OSError:return {"status":"PROCESS_SETUP_UNKNOWN","elapsed":round(time.monotonic()-t,4)}
 if z.returncode:
  return {"status":"PROCESS_ERROR","exit":z.returncode,"stderr_tail":z.stderr[-160:],"elapsed":round(time.monotonic()-t,4)}
 try:values=[json.loads(s) for s in z.stdout.splitlines() if s.strip()]
 except ValueError:return {"status":"OUTPUT_PARSE_UNKNOWN","elapsed":round(time.monotonic()-t,4)}
 return {"status":"VALUE","values":values,"elapsed":round(time.monotonic()-t,4)}
def syntactic(s):
 if not s or "\n" in s or len(s)>180:return False
 x=proc(["jq","-nc",s],timeout=0.6)
 return x["status"]=="VALUE" or (x["status"]=="PROCESS_ERROR" and "jq: error (at " in x.get("stderr_tail",""))
def extract(config):
 s=config["source"];exact(s["head_dir"],s["head_sha"]);exact(s["base_dir"],s["base_sha"])
 d=subprocess.run(["git","-C",s["head_dir"],"diff","--unified=0",s["base_sha"],s["head_sha"],"--","*.rs","**/*.rs","*.go","**/*.go"],
  check=True,capture_output=True,text=True,timeout=30).stdout
 literals_,authored,where=test_literals(d)
 candidates=[];seen=set()
 for lit in literals_:
  if lit not in seen:
   seen.add(lit)
   if syntactic(lit):candidates.append(lit)
   if len(candidates)==LIMIT_FILTERS:break
 inputs=[];ids=set()
 for v in authored+SEEDS:
  k=canon(v)
  if k not in ids:
   ids.add(k);inputs.append(v)
   if len(inputs)==LIMIT_INPUTS:break
 return {"status":"FILTERS_ADMITTED" if candidates else "UNKNOWN_NO_SOURCE_TEST_FILTER_ADMITTED",
  "original_diff_sha256":digest(d.encode()),"original_source_literals":len(literals_),
  "admitted_filters":candidates,"input_domain":inputs,
  "origin_count":len(where),"origin_locations":where}
def compare(a,b):
 if a["status"]!="VALUE" or b["status"]!="VALUE":return "UNKNOWN_INCOMPLETE"
 return "EQUAL" if a["values"]==b["values"] else "DIFFERENT"
def evaluate(c,ablate=False,withdraw=False,ablate_tests=False):
 x=extract(c);filters=x["admitted_filters"] if not ablate_tests else []
 if not filters:return {"schema":"metalogic.source-operation.v2","family":c["family"],"result":"UNKNOWN_TEST_SOURCE_ABLATED" if ablate_tests else x["status"],"extraction":x,"observations":[],"action_authorization":"NONE"}
 runs=c["runners"];need(set(runs)=={"reference","base","head"},"INVALID_RUNNERS")
 bin_dir=os.environ.get("NATIVE_BIN_DIR","")
 need(bin_dir and pathlib.Path(bin_dir).exists(),"ORIGINAL_BIN_DIRECTORY_MISSING")
 observed=[]
 for f in filters:
  for inp in x["input_domain"]:
   stdin=canon(inp)+"\n"
   arms={}
   for name,argv in runs.items():
    if ablate and name=="reference":arms[name]={"status":"REFERENCE_ABLATED"}
    else:
     cmd=[a.replace("__BIN__",bin_dir) for a in argv]+[f]
     arms[name]=proc(cmd,stdin)
   observed.append({"filter":f,"input":inp,"observations":arms,
      "base_reference":compare(arms["base"],arms["reference"]),
      "head_reference":compare(arms["head"],arms["reference"])})
 diffs=[r for r in observed if r["base_reference"]=="DIFFERENT"]
 fixed=[r for r in diffs if r["head_reference"]=="EQUAL"]
 added=[r for r in observed if r["base_reference"]=="UNKNOWN_INCOMPLETE" and r["head_reference"]=="EQUAL" and r["observations"]["reference"]["status"]=="VALUE"]
 stable=[r for r in observed if r["base_reference"]=="EQUAL" and r["head_reference"]=="EQUAL"]
 regress=[r for r in observed if r["base_reference"]=="EQUAL" and r["head_reference"]=="DIFFERENT"]
 unknown=[r for r in observed if "UNKNOWN" in r["base_reference"] or "UNKNOWN" in r["head_reference"]]
 key=lambda v:(len(canon([v["filter"],v["input"]])),canon([v["filter"],v["input"]]))
 status=("STALE_EVIDENCE_WITHDRAWN" if withdraw else "UNKNOWN_REQUIRED_REFERENCE_REMOVED" if ablate else
  "WARRANTED_BOUNDED_SOURCE_TEST_DERIVED" if fixed or added else
  "REFUTED_BOUNDED_UNREPAIRED" if diffs else "UNKNOWN_NO_NATIVE_SOURCE_TEST_WITNESS")
 return {"schema":"metalogic.source-operation.v2","family":c["family"],"source":c["source"],
  "result":status,"extraction":x,"ablation":ablate,"withdrawal":withdraw,
  "counts":{"cases":len(observed),"base_value_mismatches":len(diffs),"repaired_value_mismatches":len(fixed),
   "base_incomplete_to_head_equal":len(added),"both_equal":len(stable),"head_regression":len(regress),
   "unknown":len(unknown)},
  "minimum_value_witness":min(fixed,key=key) if fixed else None,
  "minimum_new_support_witness":min(added,key=key) if added else None,
  "method_author":"HUMAN_WRITTEN_GENERIC_SOURCE_TEST_SYNTAX_MINER",
  "operation_origins":"ORIGINAL_UPSTREAM_TEST_LITERAL_NOT_INVENTED",
  "native_reference":c["reference_name"],
  "autonomous_method_generator":"NO","action_authorization":"NONE",
  "baseline_reviewer_advantage":"NOT_PROVEN","human_time_delta":"NOT_MEASURED",
  "nonclaims":["No general semantic theorem","No autonomous operation invention","No outside customer adoption",
   "Original upstream contributor authored the fix and initial test"],
  "observations":observed}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--config",required=True);p.add_argument("--out",required=True)
 p.add_argument("--ablate-reference",action="store_true")
 p.add_argument("--withdraw",action="store_true")
 p.add_argument("--ablate-tests",action="store_true")
 a=p.parse_args()
 c=json.loads(pathlib.Path(a.config).read_text())
 need(c.get("schema")=="metalogic.source-native-runner-config.v2","WRONG_CONFIG_SCHEMA")
 r=evaluate(c,a.ablate_reference,a.withdraw,a.ablate_tests)
 dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("SOURCE_V2 "+json.dumps({"family":c["family"],"verdict":r["result"],
  "filters":len(r["extraction"]["admitted_filters"]),"counts":r.get("counts"),
  "baseline_advantage":"NOT_PROVEN"}))
 if not any([a.ablate_reference,a.withdraw,a.ablate_tests]) and r["result"]!="WARRANTED_BOUNDED_SOURCE_TEST_DERIVED":sys.exit(2)
if __name__=="__main__":main()
