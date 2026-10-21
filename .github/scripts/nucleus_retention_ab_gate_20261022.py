#!/usr/bin/env python3
"""Exact original Lean-exported finite decision positive and negative A/B gate.

Four source-preserving cache/retention arms plus a budget-only countercontrol.
Only original Lean's source-derived positive may ACCEPT; the identical source
with false target Bool must never ACCEPT. All source bytes and artifact refs
are frozen before these experiments. No flag chooses an expected answer.

Diagnostic goal: Does work-limited exact recursor replay fail because
of 8192-entry saturation, or does a deeper projection/constructor fail
independently? A green CI can mean a negative result, not a semantic fix.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,os,subprocess,sys,time
if len(sys.argv)!=3:raise SystemExit("usage: GATE MICRO_DIR EVIDENCE_DIR")
inp,out=map(Path,sys.argv[1:])
out.mkdir(parents=True,exist_ok=True)
cases=(
 ("n7","positive","magma-list-pair-n7.ndjson-positive.ndjson","49731dc62ab70379f78fa8b4aa346a373ca2df5a2cf0bde8f713d1962d46f546"),
 ("n7","negative","magma-list-pair-n7.ndjson-negative.ndjson","658f1dbb5281237ff1112d67e9fd4a3da2960784d4a08c3c5b25b5a4e53683b7"),
 ("n21","positive","magma-list-pair-n21.ndjson-positive.ndjson","52dcb4dd5e3b427d820f72beca1d430740f25831e3d90f3e71a303884fcbd4af"),
 ("n21","negative","magma-list-pair-n21.ndjson-negative.ndjson","a5e0b2d6a56f95f4d6d7c187f29c7c2b2fb2f246faae8ed0e49d682f146cbb29"),
)
arms=("baseline","bindings","replays","both","fuel4x")
flags=("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE","SUBSTITUTION_RECLOSURE",
 "TYPED_VALUE_NORMALIZATION","PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
 "TYPED_RECEIVER","SOURCE_PAIR_DEPTH8","POLYMORPHIC_PROP_IRREL",
 "PROP_SINGLETON_2P1F","EXPECTED_LAMBDA")
env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
for flag in flags: env["NUCLEUS_EXPERIMENTAL_"+flag]="1"
env["NUCLEUS_TRACE_REPLAY_CACHE"]="1"
env["NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE"]="1"
env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
rows=[]
for case,kind,basename,expected in cases:
  path=inp/basename
  assert path.is_file(),path
  digest=hashlib.sha256(path.read_bytes()).hexdigest()
  assert digest==expected,("ORIGINAL_BYTE_IDENTITY_DRIFT",path,digest,expected)
  for arm in arms:
    exe=Path("/tmp/nucleus-retention/"+arm)
    assert exe.is_file(),exe
    started=time.monotonic()
    trial_env=env.copy()
    if arm in ("bindings","both"):
      trial_env["NUCLEUS_EXPERIMENTAL_BINDING_CACHE_GROWTH"]="1"
    if arm in ("replays","both"):
      trial_env["NUCLEUS_EXPERIMENTAL_REPLAY_CACHE_GROWTH"]="1"
    with path.open("rb") as f:
      try:
        run=subprocess.run([str(exe)],stdin=f,stdout=subprocess.DEVNULL,
          stderr=subprocess.PIPE,timeout=240,env=trial_env)
        rc=run.returncode
        stderr=run.stderr.decode(errors="replace")
      except subprocess.TimeoutExpired:
        rc=124
        stderr="TIMEOUT"
    if arm=="baseline": assert rc==2,(case,kind,rc,"BASELINE_DRIFT")
    if kind=="negative": assert rc in (1,2),("UNSAFE_FALSE_ACCEPT",case,arm,rc)
    else: assert rc in (0,2),("VALID_LEAN_PROOF_REJECTED",case,arm,rc)
    names=Counter()
    residuals=Counter()
    for l in stderr.splitlines():
      if l.startswith("NUCLEUS_"):
        names[l.split(":",1)[0]]+=1
        if l.startswith("NUCLEUS_NESTED_REPLAY_FAILURE:"):
          ix=l.find('ResidualId("')
          if ix>=0: residuals[l[ix+12:].split('"',1)[0]]+=1
    row={"case":case,"expected":kind,"arm":arm,"rc":rc,"input_sha256":digest,
      "wall_s":round(time.monotonic()-started,3),"trace_counts":dict(names),
      "nested_failure_residuals":dict(residuals),
      "capacity_traces":[l for l in stderr.splitlines()
           if "NUCLEUS_BETA_BINDING_CACHE:capacity" in l
              or "NUCLEUS_REPLAY_CACHE:capacity-skip" in l][:8],
      "terminal":[l for l in stderr.splitlines()
                 if l.startswith("NUCLEUS_DOWNSTREAM:")][-1:],
      "binary_sha256":hashlib.sha256(exe.read_bytes()).hexdigest()}
    rows.append(row)
    print("NUCLEUS_RETENTION_CASE="+json.dumps(row,sort_keys=True),flush=True)
positive=[x for x in rows if x["expected"]=="positive" and x["rc"]==0]
paired=[]
for p in positive:
    neg=next(x for x in rows if x["case"]==p["case"] and x["arm"]==p["arm"] and x["expected"]=="negative")
    paired.append({"arm":p["arm"],"case":p["case"],"valid_rc":p["rc"],"false_rc":neg["rc"]})
report={
 "baseline_source":"heathsanchez/test@ff003e7fad888d39a40cfd2375885fe20e3209fa",
 "input_source":"exact Lean-exported countermodel decidable subproof, original source and false-target controls",
 "untouched_semantic_rules":True,
 "valid_full_accepts":paired,
 "runs":rows,
 "decision":"PROMISING_SUBPROOF_CHECK_WHOLE196" if paired else "NO_FULL_SUBPROOF_GAIN_RETAIN_ORIGINAL",
 "full_196_qualified":False,
 "source-verified_correctness":"untouched rules, limited 2 positive and 2 adversarial fixtures; not proof of soundness",
}
(out/"retention-ab.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print("NUCLEUS_RETENTION_DECISION="+json.dumps({"decision":report["decision"],
 "full_subproof_accepts":paired,
 "capacity_hits":{arm:sum(bool(x["capacity_traces"]) for x in rows if x["arm"]==arm) for arm in arms}
}),flush=True)
