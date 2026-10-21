#!/usr/bin/env python3
"""Evaluate a source-visible, opt-in delayed projection on original Lean exports.

FROZEN SOURCE: independent Nucleus ff003e7fad888d39a40cfd2375885fe20e3209fa
- Original positive and false Bool subproofs, byte-pinned from Lean.
- All 196 original Arena fixtures, exact per-file hashes and verdicts.
- Two independent malformed controls for FreeId and constructor alias.
- Zero synthetically selected constructor / proof-irrelevance/axiom relaxations.
Every source-valid full proof must not be REJECT. Every original invalid must
remain REJECT. New ACCEPT must be from the actual proof checker only.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,os,subprocess,sys,time
if len(sys.argv)!=5:
  raise SystemExit("usage: gate.py ORIGINAL196 MICRODIR BASE_BIN CANDIDATE_BIN OUTDIR")
corpus,micro,original,candidate,out=map(Path,sys.argv[1:])
out.mkdir(parents=True,exist_ok=True)
controls={
 "n7-pos":("magma-list-pair-n7.ndjson-positive.ndjson","49731dc62ab70379f78fa8b4aa346a373ca2df5a2cf0bde8f713d1962d46f546",True),
 "n7-neg":("magma-list-pair-n7.ndjson-negative.ndjson","658f1dbb5281237ff1112d67e9fd4a3da2960784d4a08c3c5b25b5a4e53683b7",False),
 "n21-pos":("magma-list-pair-n21.ndjson-positive.ndjson","52dcb4dd5e3b427d820f72beca1d430740f25831e3d90f3e71a303884fcbd4af",True),
 "n21-neg":("magma-list-pair-n21.ndjson-negative.ndjson","a5e0b2d6a56f95f4d6d7c187f29c7c2b2fb2f246faae8ed0e49d682f146cbb29",False),
}
flags=("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE","SUBSTITUTION_RECLOSURE",
 "TYPED_VALUE_NORMALIZATION","PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
 "TYPED_RECEIVER","SOURCE_PAIR_DEPTH8","POLYMORPHIC_PROP_IRREL",
 "PROP_SINGLETON_2P1F","EXPECTED_LAMBDA")
common={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
for flag in flags:common["NUCLEUS_EXPERIMENTAL_"+flag]="1"
common["NUCLEUS_TRACE_DOWNSTREAM"]="1"
def invoke(exe,path,on=False,trace=False,secs=220):
  env=common.copy()
  if on:env["NUCLEUS_EXPERIMENTAL_DELAY_RECURSOR_PROJECTION"]="1"
  if on and trace:env["NUCLEUS_TRACE_DELAY_RECURSOR_PROJECTION"]="1"
  if trace:env["NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE"]="1"
  start=time.monotonic()
  with path.open("rb") as f:
    p=subprocess.run([str(exe.resolve())],stdin=f,stdout=subprocess.DEVNULL,
                     stderr=subprocess.PIPE,env=env,timeout=secs)
  lines=p.stderr.decode(errors="replace").splitlines()
  return dict(rc=p.returncode,elapsed_s=round(time.monotonic()-start,3),
     delayed=[x for x in lines if x.startswith("NUCLEUS_DELAY_RECURSOR_PROJECTION:")][:32],
     recursor_failure_counts=dict(Counter(
       x.split('ResidualId("',1)[1].split('"',1)[0]
       for x in lines if x.startswith("NUCLEUS_NESTED_REPLAY_FAILURE:") and 'ResidualId("' in x)),
     terminal=[x for x in lines if x.startswith("NUCLEUS_DOWNSTREAM:")][-1:])
micro_rows=[]
for name,(filename,expected,valid) in controls.items():
  src=micro/filename
  sha=hashlib.sha256(src.read_bytes()).hexdigest()
  assert sha==expected,("SOURCE_BYTES_CHANGED",name,sha)
  for arm,exe,on in (("baseline",original,False),("candidate-off",candidate,False),("candidate-on",candidate,True)):
    run=invoke(exe,src,on,True)
    if arm in ("baseline","candidate-off"):assert run["rc"]==2,("BASELINE_DIFFERENCE",name,arm,run)
    elif valid: assert run["rc"] in (0,2),("REJECTED_VALID_PROOF",name,run)
    else: assert run["rc"] in (1,2),("ACCEPTED_FALSE_BOOL",name,run)
    row={"case":name,"arm":arm,"input_sha256":sha,**run}
    micro_rows.append(row)
    print("NUCLEUS_DELAY_PROJECTION_MICRO="+json.dumps(row,ensure_ascii=False),flush=True)
frozen=Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
manifest=json.loads(frozen.read_text())["modes"]["origin"]["rows"]
expected={x["case"]:x for x in manifest}
assert len(expected)==196
rows=[]
for group in ("good","bad"):
  for path in sorted((corpus/group).rglob("*.ndjson")):
    name=str(path.relative_to(corpus))
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    assert sha==expected[name]["sha256"],("ARENA_BYTES_CHANGED",name,sha)
    trial=invoke(candidate,path,True, name in ("good/perf/magma-list-pair-n7.ndjson","good/perf/magma-list-pair-n21.ndjson",
       "good/perf/magma-list-deep-n21.ndjson","good/perf/magma-list-deep-n36.ndjson"),180)
    reference=expected[name]["rc"];rc=trial["rc"]
    assert rc in (0,1,2),("NATIVE_CHECKER_ERROR",name,rc)
    if reference in (0,1):assert rc==reference,("PROTECTED_VERDICT_REGRESSION",name,reference,rc)
    else: assert rc in (0,2),("FALSE_REJECT_VALID",name,rc)
    assert not (group=="bad" and rc!=1),("BAD_ARENA_NOT_REJECTED",name,rc)
    rows.append({"case":name,"group":group,"sha256":sha,"previous_rc":reference,"new_rc":rc,**trial})
    if rc!=reference or trial["delayed"] or name in ("good/perf/magma-list-pair-n7.ndjson","good/perf/magma-list-pair-n21.ndjson"):
      print("NUCLEUS_DELAY_PROJECTION_ARENA="+json.dumps({"case":name,"prev":reference,"new":rc,
           "delayed":len(trial["delayed"]),"terminal":trial["terminal"]},ensure_ascii=False),flush=True)
assert len(rows)==196
counts={str(code):sum(x["new_rc"]==code for x in rows) for code in (0,1,2)}
assert counts["1"]==71 and counts["0"]>=119 and counts["2"]<=6,counts
extra=[]
for name in ("protected-false-index.ndjson","protected-eta-ctor-alias.ndjson"):
  path=Path("metatron-kernel/tests/fixtures")/name
  for arm,exe,on in (("baseline",original,False),("candidate",candidate,True)):
    trial=invoke(exe,path,on,False,40)
    assert trial["rc"] in (1,2),("PROTECTED_FORGED_ACCEPT",name,arm,trial["rc"])
    extra.append({"name":name,"arm":arm,"rc":trial["rc"],
      "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
gains=[x["case"] for x in rows if x["previous_rc"]==2 and x["new_rc"]==0]
report={"baseline_source":"ff003e7fad888d39a40cfd2375885fe20e3209fa",
  "candidate_source":os.environ.get("GITHUB_SHA"),
  "mechanism":"retains original registered recursor projection as StuckProjection, never manufactures a constructor or permits equality",
  "source":{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in
    (("baseline_binary",original),("candidate_binary",candidate),("frozen_baseline",frozen))},
  "micro":micro_rows,"official_frozen_196":{"counts":counts,"rows":rows},
  "additional_forged":extra,"new_whole_accepts":gains,
  "decision":"POSSIBLE_SEMANTIC_GAIN_REQUIRES_BROADER_REVIEW" if gains else "NO_WHOLE_PROOF_GAIN_DO_NOT_PROMOTE",
  "full_mathlib_qualified":False,"official_arena_rank":False}
(out/"source-delayed-projection-ab.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print("NUCLEUS_DELAY_PROJECTION_DECISION="+json.dumps({"counts":counts,"new_accepts":gains,
     "positive_micro":[{"case":r["case"],"rc":r["rc"],"delayed":len(r["delayed"])}
       for r in micro_rows if r["arm"]=="candidate-on" and "-pos" in r["case"]],
      "decision":report["decision"]}),flush=True)
