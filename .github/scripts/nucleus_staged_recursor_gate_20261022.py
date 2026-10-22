#!/usr/bin/env python3
"""Causal source-pinned A/B for resumable *checked* nested recursor iota.

Candidate changes only evaluator scheduling, never the Lean rules, proof
irrelevance, constructors, terms, universes or authority. Successful iota
steps can be reused but remain incomplete until actual nested source
evaluation produces a constructor/result.

Correctness gate: two positive / two falsified Lean-exported decide witnesses,
individual 196 SHA-frozen Arena verdicts, original 71 REJECT and both known
forged negatives. A green diagnostic is NOT full Mathlib or Arena eligibility.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,collections

if len(sys.argv)!=6:
    raise SystemExit("usage: gate.py ARENA_CORPUS MICRO_DIR BASE_BINARY CAND_BINARY EVIDENCE_DIR")
root,micro,base,candidate,evidence=map(Path,sys.argv[1:])
evidence.mkdir(parents=True,exist_ok=True)
manifest=Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
baselines=json.loads(manifest.read_text())["modes"]["origin"]["rows"]
pinned={x["case"]:x for x in baselines}
assert len(pinned)==196
flags=("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE","SUBSTITUTION_RECLOSURE",
"TYPED_VALUE_NORMALIZATION","PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
"TYPED_RECEIVER","SOURCE_PAIR_DEPTH8","POLYMORPHIC_PROP_IRREL",
"PROP_SINGLETON_2P1F","EXPECTED_LAMBDA")
baseline_env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
baseline_env.update({"NUCLEUS_EXPERIMENTAL_"+k:"1" for k in flags})
baseline_env["NUCLEUS_TRACE_DOWNSTREAM"]="1"

micro_sha={
"magma-list-pair-n7.ndjson-positive.ndjson":"49731dc62ab70379f78fa8b4aa346a373ca2df5a2cf0bde8f713d1962d46f546",
"magma-list-pair-n7.ndjson-negative.ndjson":"658f1dbb5281237ff1112d67e9fd4a3da2960784d4a08c3c5b25b5a4e53683b7",
"magma-list-pair-n21.ndjson-positive.ndjson":"52dcb4dd5e3b427d820f72beca1d430740f25831e3d90f3e71a303884fcbd4af",
"magma-list-pair-n21.ndjson-negative.ndjson":"a5e0b2d6a56f95f4d6d7c187f29c7c2b2fb2f246faae8ed0e49d682f146cbb29"}
def run(path,binary,enabled,tag,timeout=180,trace=False):
    env=baseline_env.copy()
    if enabled:
        env["NUCLEUS_EXPERIMENTAL_STAGED_IOTA_REPLAY"]="1"
        if trace:env["NUCLEUS_TRACE_STAGED_IOTA"]="1"
    started=time.monotonic()
    with path.open("rb") as src:
        proc=subprocess.run([str(binary.resolve())],stdin=src,
           stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env,timeout=timeout)
    data=proc.stderr.decode(errors="replace")
    counts=collections.Counter(t.split(":",2)[1] for t in data.splitlines()
            if t.startswith("NUCLEUS_STAGED_IOTA:"))
    terminal=[t for t in data.splitlines() if t.startswith("NUCLEUS_DOWNSTREAM:")][-1:]
    if trace:
        (evidence/(tag+".stderr")).write_text(data[:400000])
    return {"rc":proc.returncode,"seconds":round(time.monotonic()-started,4),
            "stage_events":dict(counts),"terminal":terminal,
            "stage_samples":[t for t in data.splitlines() if t.startswith("NUCLEUS_STAGED_IOTA:")][:28]}

micro_rows=[]
for filename,expected_sha in micro_sha.items():
    source=micro/filename
    assert source.is_file(),filename
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected_sha,("SOURCE_HASH_DRIFT",filename)
    rows={}
    for tag,binary,enabled in (("original",base,False),("staged",candidate,True)):
        rows[tag]=run(source,binary,enabled,filename+"-"+tag,120,True)
    assert rows["original"]["rc"]==2,("INVALID_MICRO_BASELINE",filename,rows)
    assert rows["staged"]["rc"] in ((0,2) if "-positive." in filename else (1,2)),("UNSAFE_MICRO",filename,rows)
    rec={"name":filename,"sha256":expected_sha,**rows}
    micro_rows.append(rec)
    print("NUCLEUS_STAGED_MICRO="+json.dumps(rec,ensure_ascii=False),flush=True)

cases=[(bucket,p) for bucket in ("good","bad")
       for p in sorted((root/bucket).rglob("*.ndjson"))]
assert len(cases)==196
full=[]
for bucket,path in cases:
    name=str(path.relative_to(root))
    actual_sha=hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual_sha==pinned[name]["sha256"],("INPUT_SHA_DRIFT",name)
    original=run(path,base,False,name+"-original",185)
    assert original["rc"]==pinned[name]["rc"],("ORIGINAL_VERDICT_DRIFT",name,original)
    new=run(path,candidate,True,name+"-staged",185, name.startswith("good/perf/"))
    assert new["rc"] in (0,1,2),("UNEXPECTED_EXIT",name,new)
    if pinned[name]["rc"] in (0,1):
        assert new["rc"]==pinned[name]["rc"],("PROTECTED_VERDICT_CHANGED",name,original,new)
    else:
        assert new["rc"] in (0,2),("NEW_INVALID_REJECT",name,new)
    assert (bucket!="bad" or new["rc"]==1),("INVALID_PROOF_WAS_NOT_REJECTED",name,new)
    rec={"case":name,"sha256":actual_sha,"original":original,"candidate":new}
    full.append(rec)
    if name.startswith("good/perf/"):
        print("NUCLEUS_STAGED_TARGET="+json.dumps(rec,ensure_ascii=False),flush=True)

extra=[]
for name in ("protected-false-index.ndjson","protected-eta-ctor-alias.ndjson"):
    path=Path("metatron-kernel/tests/fixtures")/name
    for label,binary,enabled in (("original",base,False),("staged",candidate,True)):
        result=run(path,binary,enabled,name+"-"+label,40)
        assert result["rc"] in (1,2),("FALSE_ACCEPT",name,label,result)
        extra.append({"name":name,"arm":label,"result":result,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
base_count={str(v):sum(row["original"]["rc"]==v for row in full) for v in (0,1,2)}
new_count={str(v):sum(row["candidate"]["rc"]==v for row in full) for v in (0,1,2)}
assert base_count=={"0":119,"1":71,"2":6},base_count
assert new_count["1"]==71 and new_count["0"]>=119
new_full=[row["case"] for row in full
          if row["original"]["rc"]==2 and row["candidate"]["rc"]==0]
new_micro=[row["name"] for row in micro_rows
           if row["original"]["rc"]==2 and row["staged"]["rc"]==0]
stage_counts=collections.Counter()
for row in micro_rows:
    stage_counts.update(row["staged"]["stage_events"])
for row in full:
    stage_counts.update(row["candidate"]["stage_events"])
report={"candidate_commit":os.getenv("GITHUB_SHA"),"baseline_commit":"ff003e7fad888d39a40cfd2375885fe20e3209fa",
        "original_source_corpus":"official Lean original frozen196 and native decidable microexports",
        "change_scope":"source-certified intermediate iota replay scheduling; no semantic shortcut",
        "binary_sha256":{"baseline":hashlib.sha256(base.read_bytes()).hexdigest(),
                         "candidate":hashlib.sha256(candidate.read_bytes()).hexdigest()},
        "micro":micro_rows,"frozen196":full,"other_protected":extra,
        "counts":{"original":base_count,"candidate":new_count},
        "first_positive_micro_accepts":new_micro,"new_196_accepts":new_full,
        "stage_counts":dict(stage_counts),
        "decision":"PROMOTION_REVIEW_REQUIRED" if new_full else ("NARROW_MICRO_ADVANCE_ONLY" if new_micro else "NO_COMPLETE_GAIN_DO_NOT_PROMOTE"),
        "full_mathlib_accepted":False,"official_rank_qualified":False}
(evidence/"decision.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print("NUCLEUS_STAGED_DECISION="+json.dumps({
    "counts":report["counts"],"micro_gains":new_micro,"new_full_accepts":new_full,
    "stage_counts":report["stage_counts"],"decision":report["decision"]},ensure_ascii=False),flush=True)
