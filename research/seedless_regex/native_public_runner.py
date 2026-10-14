#!/usr/bin/env python3
"""Read-only source-native public-rule four-arm validation. No outside writes."""
import argparse,hashlib,json,pathlib,subprocess,time,sys
def demand(ok,msg):
    if not ok:raise RuntimeError(msg)
def run(worktree,package,name):
    command=["go","test","-json","-count=1","-timeout=5m","-run","^"+name+"$","./"+package]
    start=time.perf_counter()
    try:
        p=subprocess.run(command,cwd=worktree,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         text=True,check=False,timeout=360)
    except subprocess.TimeoutExpired:
        return dict(status="TIMEOUT_UNKNOWN",duration_s=360)
    events=[]
    for line in p.stdout.splitlines():
        try:events.append(json.loads(line))
        except json.JSONDecodeError:pass
    trace=[e for e in events if e.get("Test")==name]
    actions=[e.get("Action") for e in trace if e.get("Action") in ("run","pass","fail","skip")]
    failures=[e.get("Output","") for e in trace if
              "native rule " in e.get("Output","") or "inverted oracle " in e.get("Output","")]
    if p.returncode==0 and "pass" in actions and "run" in actions:status="NATIVE_PASS"
    elif p.returncode!=0 and "fail" in actions and "run" in actions and failures:status="NATIVE_ASSERTION_FAIL"
    elif p.returncode==0 and not actions:status="UNKNOWN_NAMED_TEST_NOT_EXECUTED"
    else:status="UNKNOWN_SETUP_OR_NONBEHAVIORAL_FAILURE"
    return {"status":status,"exit_code":p.returncode,"named_test_actions":actions,
            "assertion_examples":failures[:6],"duration_s":round(time.perf_counter()-start,3),
            "stdout_sha256":hashlib.sha256(p.stdout.encode()).hexdigest(),
            "stderr_tail":p.stderr[-380:],"command":command}
def main():
    p=argparse.ArgumentParser()
    for n in ("manifest","root","out"):p.add_argument("--"+n,required=True)
    a=p.parse_args()
    m=json.loads(pathlib.Path(a.manifest).read_text())
    demand(m["schema"]=="metalogic.go-source-regexp-to-public-validation-rule.v1","WRONG_NATIVE_BRIDGE_SCHEMA")
    root=pathlib.Path(a.root)
    package=pathlib.Path(m["test_file"]).parent.as_posix()
    name=m["test_name"]
    obs={}
    for arm in ("base","head","negative","pristine"):
        obs[arm]=run(root/arm,package,name)
        print("GO_PUBLIC_RULE_NATIVE",arm,obs[arm]["status"],
              "actions",obs[arm]["named_test_actions"],flush=True)
    decision=(obs["base"]["status"]=="NATIVE_ASSERTION_FAIL" and
              obs["head"]["status"]=="NATIVE_PASS" and
              obs["negative"]["status"]=="NATIVE_ASSERTION_FAIL" and
              obs["pristine"]["status"]=="UNKNOWN_NAMED_TEST_NOT_EXECUTED")
    result={
      "schema":"metalogic.go-source-regex-to-public-native-causality.v1",
      "verdict":"WARRANTED_BOUNDED_PUBLIC_NATIVE_RULE_CAUSAL_TRANSITION" if decision else "UNKNOWN_OR_REFUTED_NATIVE_RULE_BRIDGE",
      "source":m["source"],"binding":m["binding"],
      "test_name":name,"test_file":m["test_file"],"synthesized_input":m["source_only_witness"],
      "observation_arms":obs,"source_test_authorship":"MATHGRAPH_HUMAN_WRITTEN_AST_BRIDGE",
      "input_generator":"SEEDLESS_REGEXP_AST_SYNTAX",
      "public_rule_binding":"AST_DERIVED_NARROW_NEWSTRINGRULEWITHERROR",
      "native_program_exec":True,
      "external_spec_compliance":"NOT_VERIFIED",
      "strong_conventional_baseline_same_information":"CAN_REPRODUCE",
      "human_review_time_savings":"NOT_MEASURED",
      "autonomous_generator_of_generators":"NOT_DEMONSTRATED",
      "action_authorization":"NONE"}
    target=pathlib.Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+chr(10))
    print("PUBLIC_GO_NATIVE_CAUSAL_VERDICT",result["verdict"],flush=True)
    demand(decision,"GO_NATIVE_BEFORE_AFTER_OR_ABLATION_NOT_QUALIFIED")
if __name__=="__main__":main()
