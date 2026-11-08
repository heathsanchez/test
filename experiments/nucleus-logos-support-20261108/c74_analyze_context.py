"""C74: actual binder distinction, never a source-equality certificate."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

source=Path("arena207/good/perf/magma-list-pair-n7.ndjson").read_bytes()
digest=hashlib.sha256(source).hexdigest()
assert digest=="abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
flags=json.loads(Path("base/flags.json").read_text())
assert len(flags)==24 and set(flags.values())=={"1"}
records={}
for label,budget,expected in (("standard",262144,"UNKNOWN"),("diagnostic",8388608,"ACCEPT")):
    env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(flags)
    env.update({
        "NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE":"1",
        "NUCLEUS_EXPERIMENTAL_RESUMABLE_EXPOSURE":"1",
        "NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE":"1",
        "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR":"8837",
        "NUCLEUS_DIAGNOSTIC_C48_SOURCE_TRANSITIONS":"1",
        "NUCLEUS_DIAGNOSTIC_C49_CONTENT_FINGERPRINT":"1",
        "NUCLEUS_DIAGNOSTIC_C50_STATE_LOSS":"1",
        "NUCLEUS_C74_CAPTURE_CONTEXT":"1",
    })
    run=subprocess.run(["candidate/nucleus-diagnostic",str(budget)],input=source,
                       capture_output=True,env=env,timeout=180)
    verdict={0:"ACCEPT",1:"REJECT",2:"UNKNOWN",3:"ERROR"}.get(run.returncode,"ERROR")
    assert verdict==expected,("C74 altered baseline verdict",label,verdict,expected)
    Path("reports/c74-"+label+".stderr").write_bytes(run.stderr)
    lines=run.stderr.decode(errors="replace").splitlines()
    contexts=[json.loads(s.split("NUCLEUS_C74_CONTEXT:",1)[1])
              for s in lines if s.startswith("NUCLEUS_C74_CONTEXT:")]
    assert contexts,("source contexts missing",label)
    assert all(x["no_source_equality_or_proof_authority"] for x in contexts)
    event_26=next((x for x in contexts if x["seq"]==26),None)
    assert event_26 is not None,(label,"event26 capture missing",contexts)
    record={"verdict":verdict,"contexts":contexts,
            "stderr_sha256":hashlib.sha256(run.stderr).hexdigest()}
    records[label]=record
    print("C74_SOURCE_CONTEXT="+json.dumps({"label":label,"verdict":verdict,"seq26":event_26},sort_keys=True),flush=True)

def normalized(binding):
    # Allocation IDs are not semantic equality; only compare reported
    # binding tags and expression shape, not environment addresses.
    if binding is None:return None
    idx,text=binding
    if text.startswith("closure:"):
        return (idx,text.split(":captured_env=")[0])
    return (idx,text)

difference={}
a={x["seq"]:x for x in records["standard"]["contexts"]}
b={x["seq"]:x for x in records["diagnostic"]["contexts"]}
for seq in sorted(set(a)&set(b)):
    x,y=a[seq],b[seq]
    first=None
    for i,(left,right) in enumerate(zip(x["sampled_binders"],y["sampled_binders"])):
        if normalized(left)!=normalized(right):
            first={"position":i,"left":left,"right":right}
            break
    difference[str(seq)]={
       "same_source_expr":x["source_expr"]==y["source_expr"],
       "same_recursor":x["recursor"]==y["recursor"],
       "same_content_hash":x["source_env_fingerprint"]==y["source_env_fingerprint"],
       "same_universe_entries":x["source_level_entries"]==y["source_level_entries"],
       "first_sampled_binding_difference":first,
       "left_sample_count":len(x["sampled_binders"]),
       "right_sample_count":len(y["sampled_binders"]),
       "sampled_binding_match_is_not_a_proof_of_context_equivalence":True,
    }
    print("C74_BINDER_SEPARATOR="+json.dumps({"seq":seq,**difference[str(seq)]},sort_keys=True),flush=True)
out={"experiment":"C74 exact source context observation only",
     "source_sha256":digest,"selected_checker_changed":False,
     "proof_rules_changed":False,"new_original_standard_accepts":0,
     "same_binary":True,"results":records,"comparison":difference}
Path("reports/c74.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
