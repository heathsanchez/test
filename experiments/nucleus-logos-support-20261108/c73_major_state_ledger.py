"""C73 original n7 source-owned inner-state divergence, using C65 binary.

Reuses proven C48/C49/C50 diagnostic observers instead of inventing another
kernel rule or repeatedly changing a local grant. Histories are never proofs.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_c48_first_divergence import (
    parse_trace, first_divergence, first_content_divergence,
)
from probe_c50_loss_ledger import parse_loss_events, summarize_losses

ROOT=Path("arena207")
BINARY=Path("qualified/candidate/nucleus-diagnostic").resolve()
FLAGS=json.loads(Path("qualified/base/flags.json").read_text())
assert len(FLAGS)==24 and set(FLAGS.values())=={"1"}
ORIG=ROOT.joinpath("good/perf/magma-list-pair-n7.ndjson").read_bytes()
SHA=hashlib.sha256(ORIG).hexdigest()
assert SHA=="abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
REPORT=Path("reports");REPORT.mkdir(exist_ok=True)
cases=[
    ("standard-baseline",262144,False,"UNKNOWN"),
    ("standard-resume",262144,True,"UNKNOWN"),
    ("4m-resume",4194304,True,"UNKNOWN"),
    ("8m-resume",8388608,True,"ACCEPT"),
]
results={}
for label,budget,resume,expected in cases:
    env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(FLAGS)
    env.update({
        "NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE":"1",
        "NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE":"1",
        "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR":"8837",
        "NUCLEUS_DIAGNOSTIC_C48_SOURCE_TRANSITIONS":"1",
        "NUCLEUS_DIAGNOSTIC_C49_CONTENT_FINGERPRINT":"1",
        "NUCLEUS_DIAGNOSTIC_C50_STATE_LOSS":"1",
        "NUCLEUS_DIAGNOSTIC_C65_PREFIX_CENSUS":"1",
    })
    if resume:env["NUCLEUS_EXPERIMENTAL_RESUMABLE_EXPOSURE"]="1"
    p=subprocess.run([str(BINARY),str(budget)],input=ORIG,capture_output=True,env=env,timeout=180)
    verdict={0:"ACCEPT",1:"REJECT",2:"UNKNOWN",3:"ERROR"}.get(p.returncode,"ERROR")
    assert verdict==expected,(label,verdict,expected)
    (REPORT/("c73-"+label+".stderr")).write_bytes(p.stderr)
    events=parse_trace(p.stderr)
    losses=parse_loss_events(p.stderr)
    assert events,(label,"no C48 source transitions")
    assert losses,(label,"no C50 worklist losses")
    stage=Counter(e["stage"] for e in events)
    by_name=Counter(e["recursor"] for e in events if e["stage"]=="enter")
    exact=Counter((e["recursor"],e["major_expr"],e["major_env"]) for e in events if e["stage"]=="enter")
    fingerprint=Counter((e["recursor"],e["major_expr"],e.get("major_env_content_fingerprint")) for e in events
                        if e["stage"]=="enter" and e.get("major_env_content_fingerprint") is not None)
    repeats={
        "sampled_exact_environment_revisit_count":sum(n-1 for n in exact.values() if n>1),
        "sampled_content_fingerprint_revisit_count":sum(n-1 for n in fingerprint.values() if n>1),
        "sampled_distinct_exact_environment_keys":len(exact),
        "sampled_distinct_content_fingerprints":len(fingerprint),
        "fingerprint_is_not_a_kernel_equality":True,
        "possibly_truncated_first_512":len(events)>=512,
    }
    res={"label":label,"budget":budget,"resume":resume,"verdict":verdict,
         "event_count":len(events),"loss_event_count":len(losses),
         "stages":dict(stage),"recursors":dict(by_name),"repeats":repeats,
         "loss_summary":summarize_losses(losses),
         "stderr_sha256":hashlib.sha256(p.stderr).hexdigest(),
         "first_events":events[:40],"first_losses":losses[:40],
         "_events":events}
    results[label]=res
    print("C73_ARM="+json.dumps({k:v for k,v in res.items() if k not in ("first_events","first_losses","_events","loss_summary")},sort_keys=True),flush=True)

comparisons={}
for low in ("standard-baseline","standard-resume","4m-resume"):
    left,right=results[low]["_events"],results["8m-resume"]["_events"]
    comparisons[low+"__to__8m-resume"]={
        "exact_event_first_divergence":first_divergence(left,right),
        "content_grouping_first_divergence":first_content_divergence(left,right),
        "not_a_proof_of_equivalence":True,
    }
    print("C73_FIRST_DIVERGENCE="+json.dumps({"pair":low+"__to__8m-resume",**comparisons[low+"__to__8m-resume"]},sort_keys=True),flush=True)
for r in results.values():del r["_events"]
out={"experiment":"C73 exact original source C65 unfinished major worklist root",
     "source_sha256":SHA,"input_unchanged":True,"selected_checker_changed":False,
     "proof_rules_changed":False,"resume_experiment_flag_semantically_reuses_only_source_prefix":True,
     "same_binary_for_every_arm":True,"binary_sha256":hashlib.sha256(BINARY.read_bytes()).hexdigest(),
     "standard_accepts_new":0,"full_protected_403_not_run":True,
     "results":results,"comparisons":comparisons}
(REPORT/"c73.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print("C73_FIRST_SOURCE_MAJOR_LEDGER_PRESERVED",flush=True)
