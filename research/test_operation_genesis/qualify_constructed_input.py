#!/usr/bin/env python3
"""New-input causal evaluator over actual native Go original source/author assertions.

The human-coded source AST mutation primitive is not an autonomous method inventor.
No source target names, date/time format or Go library special cases in runner.
"""
import argparse,copy,hashlib,json,pathlib,re,subprocess,time

def verify(v,s):
 if not v:raise RuntimeError(s)
def gitrev(p):
 z=subprocess.run(["git","-C",str(p),"rev-parse","HEAD"],capture_output=True,text=True,check=True)
 return z.stdout.strip()
def sha(data):return hashlib.sha256(data).hexdigest()

def native(test,package,cwd):
 regex="^("+re.escape(test)+")$"
 t=time.monotonic()
 cmd=["go","test","-json","-count=1","-timeout=2m","-run",regex,package]
 try:r=subprocess.run(cmd,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
    text=True,timeout=150,check=False)
 except subprocess.TimeoutExpired:return {"status":"TIMEOUT_UNKNOWN","exit":None,"subtest_count":0}
 events=[]
 for line in r.stdout.splitlines():
  try:events.append(json.loads(line))
  except json.JSONDecodeError:pass
 selected=[e.get("Action") for e in events if e.get("Test")==test and
           e.get("Action") in ("run","fail","pass")]
 sub=[e for e in events if str(e.get("Test","")).startswith(test+"/") and
      e.get("Action")=="run"]
 outputs="".join(str(e.get("Output","")) for e in events if e.get("Action")=="output")
 fail_assert=bool(re.search(r"(?m)\.go:\d+:",outputs)) and
             any(e.get("Action")=="fail" and str(e.get("Test","")).startswith(test)
                 for e in events)
 # No arbitrary process/non-test error may be promoted as native behavioural witness.
 return {"status":"COMPLETE" if "run" in selected else "NO_TEST_EXECUTED",
         "exit":r.returncode,"selected_parent_actions":selected,
         "subtest_count":len(sub),"has_source_test_assertion":fail_assert,
         "go_stdout_sha256":sha(r.stdout.encode()),
         "elapsed_seconds":round(time.monotonic()-t,3),
         "test_output_tail":outputs[-1100:]}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--manifest",type=pathlib.Path,required=True)
 p.add_argument("--proposal",type=pathlib.Path,required=True)
 p.add_argument("--base",type=pathlib.Path,required=True)
 p.add_argument("--head",type=pathlib.Path,required=True)
 p.add_argument("--out",type=pathlib.Path,required=True)
 a=p.parse_args()
 m=json.loads(a.manifest.read_text())
 proposal=json.loads(a.proposal.read_text())
 verify(gitrev(a.base)==m["base_sha"] and gitrev(a.head)==m["head_sha"],
        "SOURCE_REVISIONS_NOT_FROZEN")
 verify(proposal["base_sha"]==m["base_sha"] and proposal["head_sha"]==m["head_sha"] and
        proposal["test_file"]==m["selected"][0]["file"] and
        proposal["test_function"]==m["selected"][0]["function"],
        "GENERATED_OPERATION_SCOPE_MISMATCH")
 orig=(a.head/proposal["test_file"]).read_bytes()
 baseorig=(a.base/proposal["test_file"]).read_bytes()
 verify(sha(orig)==sha(baseorig)==proposal["original_head_test_sha256"],"ORIGINAL_TEST_BYTES_CHANGED")
 test=proposal["test_function"]
 package=m["selected"][0]["package"]
 evaluated=[]
 winner=None
 for c in proposal["candidates"]:
  newbytes=pathlib.Path(c["mutated_test_file"]).read_bytes()
  verify(sha(newbytes)==c["mutated_test_sha256"] and
         c["new_literal"]!=c["original_literal"] and
         c["new_literal"] not in proposal["original_author_literals"],
         "GENERATED_LITERAL_IDENTITY_FORGED")
  (a.head/proposal["test_file"]).write_bytes(newbytes)
  head=native(test,package,a.head)
  if head["status"]!="COMPLETE" or head["exit"]!=0 or
     head["subtest_count"]!=1 or "pass" not in head["selected_parent_actions"]:
   evaluated.append({"candidate_id":c["id"],"head":head,
      "status":"UNKNOWN_INVALID_OR_UNEXECUTED_NEW_LITERAL"})
   continue
  (a.base/proposal["test_file"]).write_bytes(newbytes)
  base=native(test,package,a.base)
  candidate={
   "candidate_id":c["id"],"original_literal":c["original_literal"],
   "new_literal":c["new_literal"],"generated_test_sha256":c["mutated_test_sha256"],
   "head":head,"base":base}
  # The assertion itself is upstream-authored; an original BASE failure
  # must witness the mutated literal rather than a remaining old case.
  proves=base["status"]=="COMPLETE" and base["exit"]!=0 and
         base["subtest_count"]==1 and base["has_source_test_assertion"] and
         c["new_literal"].strip() in base.get("test_output_tail","")
  candidate["source_native_new_literal_causes_regression"]=proves
  evaluated.append(candidate)
  if proves:
   winner=candidate
   break
 # Required removal ablation against original predecessor with TEST FUNCTION
 # present but ZERO generated input cases.
 absent=pathlib.Path(proposal["empty_ablation_file"]).read_bytes()
 verify(sha(absent)==proposal["empty_ablation_sha256"],"ABLATION_SOURCE_CHANGED")
 (a.base/proposal["test_file"]).write_bytes(absent)
 ablated=native(test,package,a.base)
 absent_ok=ablated["status"]=="COMPLETE" and ablated["exit"]==0 and
           ablated["subtest_count"]==0 and "pass" in ablated["selected_parent_actions"]
 result=("WARRANTED_BOUNDED_NEW_SOURCE_DERIVED_TEST_INPUT" if winner and absent_ok
   else "UNKNOWN_NO_CAUSAL_GENERATED_INPUT")
 record={
  "schema":"metalogic.constructed-native-original-test-input.v1",
  "result":result,"source_base":m["base_sha"],"source_head":m["head_sha"],
  "selected_original_test":test,"test_original_author":"UPSTREAM",
  "input_proposal_generator":"HUMAN_WRITTEN_GO_AST_DIGIT_MUTATION",
  "original_author_test_assertions_reused_unchanged":True,
  "new_literal_selected_from_original":False if winner else None,
  "evaluated_count":len(evaluated),"evaluations":evaluated,
  "selected_minimal_witness":winner,
  "generated_input_removed_ablation":{
    "status":"UNKNOWN_EMPTY_GENERATED_INPUTS" if absent_ok else "UNQUALIFIED_ABLATION",
    "native":ablated},
  "fully_informed_baseline_can_reproduce":"YES",
  "measured_cost_or_reviewer_decision_advantage":"NOT_MEASURED",
  "autonomous_self_authored_method_generator":"NOT_ESTABLISHED",
  "new_upstream_defect_discovered":"NO",
  "action_authorization":"NONE",
 }
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n")
 print("CONSTRUCTIVE_NATIVE_INPUT "+json.dumps({
   "result":result,"candidate_attempts":len(evaluated),
   "mutated_input_sha256":sha(winner["new_literal"].encode()) if winner else None,
   "original_test":test,"ablation":record["generated_input_removed_ablation"]["status"],
   "L7":"UNKNOWN"}))
 verify(result=="WARRANTED_BOUNDED_NEW_SOURCE_DERIVED_TEST_INPUT",
        "NEW_INPUT_CANNOT_BE_NATIVE_QUALIFIED")
if __name__=="__main__":
 main()
