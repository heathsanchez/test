#!/usr/bin/env python3
"""Human-written whole-source-observation extractor, no operation-name rules.

Reads complete expression fields in original added Go tests and executable
documentation examples, rather than individually valid nested string fragments.
Delegates native execution/typed comparison to the earlier V2 test framework.
NOT autonomous method invention; original upstream author supplies test idea.
"""
import argparse,hashlib,json,os,pathlib,re,subprocess,sys
import source_grammar_v2 as old
TICK=chr(96)
RAW=re.compile(TICK+"([^"+TICK+"\\n]{1,1200})"+TICK)
QUOTED=re.compile(r'"(?:\\.|[^"\\])*"')
def observations(diff):
 out=[];seen=set();file="";role=None
 for i,line in enumerate(diff.splitlines(),1):
  if line.startswith("+++ b/"):
   file=line[6:];bn=pathlib.PurePosixPath(file).name.lower()
   role=("GO_TEST" if bn.endswith("_test.go") else
     "RUST_TEST" if file.endswith(".rs") and ("test" in file.lower() or "spec" in file.lower()) else
     "DOC" if file.endswith((".md",".dj",".markdown")) else None)
   continue
  if role is None or not line.startswith("+") or line.startswith("+++"):continue
  raw=line[1:];sources=[]
  if role=="GO_TEST":
   m=re.match(r'\s*(?:expression|filter|script|query)\s*:\s*(.*)',raw)
   if m:
    p=RAW.search(m.group(1))
    if p:sources=[(p.group(1),"GO_FULL_EXPRESSION_FIELD")]
    else:
     q=QUOTED.search(m.group(1))
     if q:
      try:sources=[(json.loads(q.group()),"GO_FULL_QUOTED_EXPRESSION_FIELD")]
      except ValueError:pass
  elif role=="RUST_TEST" and re.search(r'\b(?:yields|give|check|test_case|assert_eval)\s*!\s*\(',raw):
   sources=[(v,"RUST_TEST_MACRO_LITERAL") for v in old.literals(raw)[:4]]
  elif role=="DOC":
   for token in RAW.findall(raw):
    if "-->" in token:sources.append((token.split("-->",1)[0].strip(),"DOC_AUTHOR_RESULT"))
    elif "=>" in token:sources.append((token.split("=>",1)[0].strip(),"DOC_AUTHOR_RESULT"))
   if raw.lstrip().startswith(("$ ","jq ","jaq ","yq ")):
    m=re.findall(r"'([^'\n]{1,1200})'",raw)
    if m:sources.append((m[0],"DOC_AUTHOR_CLI_EXAMPLE"))
  for program,origin_role in sources:
   if not isinstance(program,str) or not program or len(program)>1200:continue
   key=(file,program)
   if key in seen:continue
   seen.add(key)
   out.append({"program":program,"source_file":file,"diff_line":i,
     "source_role":origin_role,"program_sha256":hashlib.sha256(program.encode()).hexdigest()})
 return out
def extract(config):
 s=config["source"];old.exact(s["base_dir"],s["base_sha"]);old.exact(s["head_dir"],s["head_sha"])
 diff=subprocess.run(["git","-C",s["head_dir"],"diff","--unified=0",
   s["base_sha"],s["head_sha"],"--","*.go","**/*.go","*.rs","**/*.rs",
   "*.md","**/*.md","*.dj","**/*.dj"],check=True,text=True,capture_output=True,timeout=30).stdout
 source=observations(diff);admitted=[]
 for x in source:
  if old.syntactic(x["program"]):
   admitted.append(x)
   if len(admitted)>=30:break
 return {"source_program_count":len(source),"source_programs":source,
  "reference_grammar_admitted":len(admitted),"admitted":admitted,
  "source_diff_sha256":hashlib.sha256(diff.encode()).hexdigest()}
def experiment(c,ablate_source=False,ablate_reference=False,withdraw=False):
 e=extract(c)
 if ablate_source:return {"result":"UNKNOWN_SOURCE_TEST_WITHDRAWN","extraction":e,"observations":[]}
 if not e["admitted"]:return {"result":"UNKNOWN_NO_COMPLETE_SOURCE_ADMITTED_PROGRAM",
   "extraction":e,"observations":[]}
 bindir=os.environ.get("NATIVE_BIN_DIR","")
 old.need(bindir and pathlib.Path(bindir).exists(),"NATIVE_BIN_DIR_MISSING")
 observed=[];inputs=c.get("domain",old.SEEDS)
 for item in e["admitted"]:
  for inp in inputs:
   if len(observed)>=360:break
   stdin=old.canon(inp)+"\n";arms={}
   for role,prefix in c["runners"].items():
    if role=="reference" and ablate_reference:arms[role]={"status":"REFERENCE_REMOVED"}
    else:arms[role]=old.proc([v.replace("__BIN__",bindir) for v in prefix]+[item["program"]],stdin)
   observed.append({"original_source_program":item,"input":inp,"arms":arms,
     "base_reference":old.compare(arms["base"],arms["reference"]),
     "head_reference":old.compare(arms["head"],arms["reference"])})
 vals=[x for x in observed if x["base_reference"]=="DIFFERENT"]
 fixed=[x for x in vals if x["head_reference"]=="EQUAL"]
 gained=[x for x in observed if x["base_reference"]=="UNKNOWN_INCOMPLETE" and
    x["head_reference"]=="EQUAL" and x["arms"]["reference"]["status"]=="VALUE"]
 stable=[x for x in observed if x["base_reference"]=="EQUAL" and x["head_reference"]=="EQUAL"]
 unclear=[x for x in observed if "UNKNOWN" in x["base_reference"] or "UNKNOWN" in x["head_reference"]]
 worsening=[x for x in observed if x["base_reference"]=="EQUAL" and x["head_reference"]=="DIFFERENT"]
 key=lambda x:(len(old.canon([x["original_source_program"]["program"],x["input"]])),
     old.canon([x["original_source_program"]["program"],x["input"]]))
 return {"schema":"metalogic.mathgraph.whole-observation.v3",
   "family":c["family"],"source_pins":c["source"],"extraction":e,
   "result":"STALE_EVIDENCE_WITHDRAWN" if withdraw else "UNKNOWN_REFERENCE_ABLATED" if ablate_reference else
     "WARRANTED_BOUNDED_SOURCE_COMPATIBILITY" if fixed or gained else
     "REFUTED_BOUNDED_UNREPAIRED" if vals else "UNKNOWN_NO_NATIVE_EXECUTABLE_WITNESS",
   "counts":{"cases":len(observed),"value_disagreements":len(vals),
     "repaired_value_disagreements":len(fixed),"unsupported_to_compatible":len(gained),
     "both_equal_controls":len(stable),"unknown_cases":len(unclear),"new_regressions":len(worsening)},
   "minimal_native_repair":min(fixed,key=key) if fixed else None,
   "minimal_new_support":min(gained,key=key) if gained else None,
   "method_authorship":"HUMAN_WRITTEN_OBSERVER_ROLE_PARSER",
   "operation_input_author":"ORIGINAL_UPSTREAM_SOURCE_AUTHOR",
   "action_authorization":"NONE","baseline_advantage":"NOT_PROVEN",
   "human_time_savings":"NOT_MEASURED","autonomous_new_generator":"NO",
   "observations":observed}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--config",required=True);p.add_argument("--out",required=True)
 p.add_argument("--ablate-source",action="store_true")
 p.add_argument("--ablate-reference",action="store_true")
 p.add_argument("--withdraw",action="store_true")
 a=p.parse_args()
 cfg=json.loads(pathlib.Path(a.config).read_text())
 r=experiment(cfg,a.ablate_source,a.ablate_reference,a.withdraw)
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("WHOLE_SOURCE_V3 "+json.dumps({"family":cfg["family"],"result":r["result"],
   "source_observations":r["extraction"]["source_program_count"],
   "admitted":r["extraction"]["reference_grammar_admitted"],
   "counts":r.get("counts"),"fully_informed_baseline_win":"NOT_PROVEN"}))
 if not (a.ablate_source or a.ablate_reference or a.withdraw) and r["result"]!="WARRANTED_BOUNDED_SOURCE_COMPATIBILITY":
  sys.exit(2)
