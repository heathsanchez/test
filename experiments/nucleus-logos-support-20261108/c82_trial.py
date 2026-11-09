"""C82 repeat-after-failure observer on unchanged original n7.

A source-owned continuation is potentially useful across whole calls only if
a formerly failed *exact root* is later retried under the same authority,
definitions, registered rules, goal, spine, and captured environment.
This is diagnostics only; no proof, cache or ACCEPT can follow from a match.
"""
from pathlib import Path
import hashlib,json,os,subprocess

INPUT=Path("arena207/good/perf/magma-list-pair-n7.ndjson").read_bytes()
SHA=hashlib.sha256(INPUT).hexdigest()
assert SHA=="abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
FLAGS=json.loads(Path("base/flags.json").read_text())
assert len(FLAGS)==24 and set(FLAGS.values())=={"1"}
RESULT={0:"ACCEPT",1:"REJECT",2:"UNKNOWN",3:"ERROR"}
rows=[]
Path("reports").mkdir(exist_ok=True)
for budget,resume,expect in [(262144,False,"UNKNOWN"),(262144,True,"UNKNOWN"),
                              (4194304,True,"UNKNOWN"),(8388608,True,"ACCEPT")]:
    env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(FLAGS)
    env.update({
        "NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE":"1",
        "NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE":"1",
        "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR":"8837",
        "NUCLEUS_DIAGNOSTIC_C50_STATE_LOSS":"1",
        "NUCLEUS_DIAGNOSTIC_C55_APP_SHAPE":"1",
        "NUCLEUS_DIAGNOSTIC_C56_NEUTRAL_PAIR":"1",
        "NUCLEUS_C82_EXACT_REPEAT":"1",
    })
    if resume:env["NUCLEUS_EXPERIMENTAL_RESUMABLE_EXPOSURE"]="1"
    proc=subprocess.run(["candidate/nucleus-diagnostic",str(budget)],input=INPUT,
                        capture_output=True,env=env,timeout=180)
    verdict=RESULT.get(proc.returncode,"ERROR")
    assert verdict==expect,(budget,resume,verdict,expect)
    lines=proc.stderr.decode(errors="replace").splitlines()
    found=[x for x in lines if x.startswith("NUCLEUS_C82_SUMMARY:")]
    assert len(found)==1,("missing exact-root census",budget,resume)
    obj=json.loads(found[0].split(":",1)[1])
    assert obj["kernel_accept_authority"]=="NONE"
    assert not obj["continuation_resume_implemented"]
    assert obj["exact_failed_then_retried"]<=obj["exact_reentries"]<=obj["entries"]
    name=f"{budget}-{'resume' if resume else 'baseline'}"
    Path("reports/c82-"+name+".stderr").write_bytes(proc.stderr)
    row={"budget":budget,"resume":resume,"verdict":verdict,
         "source_sha256":SHA,"summary":obj,
         "stderr_sha256":hashlib.sha256(proc.stderr).hexdigest()}
    print("C82_ORIGINAL_ARM="+json.dumps(row,sort_keys=True),flush=True)
    rows.append(row)
out={
  "experiment":"C82 exact source-owned recursor root retry-after-failure census",
  "original_sha256":SHA,
  "source_unchanged":True,
  "all_verdicts_pinned":True,
  "selected_checker_changed":False,
  "new_proof_rules":False,
  "original_standard_accepts":0,
  "resumable_worklist_not_implemented":True,
  "protected_403_not_run":True,
  "rows":rows,
}
Path("reports/c82.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
