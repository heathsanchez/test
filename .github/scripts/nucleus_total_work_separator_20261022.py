#!/usr/bin/env python3
"""Causal separator: is original valid Lean by-decide stuck on paid-work alone?

The exact native Nucleus checker remains unchanged except for OPT-IN finite
total-work ceilings (65,536 baseline; 2x,4x,8x,16x). Changing the ceiling
does not prove correctness; it is diagnostics, NOT a promotion candidate.

Run original SHA-verified positive and falsified Lean micro proofs and
protected counterexamples, report the first causal reduction obstruction.
Never claim ACCEPT without the exact original source passing the checker.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,collections,tempfile
if len(sys.argv)!=4:raise SystemExit("usage: gate.py MICRO_DIR NUCLEUS_BINARY EVIDENCE_DIR")
micro,binary,out=map(Path,sys.argv[1:])
out.mkdir(parents=True,exist_ok=True)
sha={
"magma-list-pair-n7.ndjson-positive.ndjson":"49731dc62ab70379f78fa8b4aa346a373ca2df5a2cf0bde8f713d1962d46f546",
"magma-list-pair-n7.ndjson-negative.ndjson":"658f1dbb5281237ff1112d67e9fd4a3da2960784d4a08c3c5b25b5a4e53683b7",
"magma-list-pair-n21.ndjson-positive.ndjson":"52dcb4dd5e3b427d820f72beca1d430740f25831e3d90f3e71a303884fcbd4af",
"magma-list-pair-n21.ndjson-negative.ndjson":"a5e0b2d6a56f95f4d6d7c187f29c7c2b2fb2f246faae8ed0e49d682f146cbb29"}
flags=("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE","SUBSTITUTION_RECLOSURE",
"TYPED_VALUE_NORMALIZATION","PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
"TYPED_RECEIVER","SOURCE_PAIR_DEPTH8","POLYMORPHIC_PROP_IRREL",
"PROP_SINGLETON_2P1F","EXPECTED_LAMBDA")
envbase={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
envbase.update({"NUCLEUS_EXPERIMENTAL_"+f:"1" for f in flags)
envbase["NUCLEUS_TRACE_DOWNSTREAM"]="1"
envbase["NUCLEUS_TRACE_WORK_CEILING"]="1"
envbase["NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE"]="1"
ceilings=(65536,131072,262144,524288,1048576)
rows=[]
for filename,digest in sha.items():
    source=micro/filename
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,("INVALID_ORIGINAL_SOURCE",filename)
    variants={}
    for steps in ceilings:
        env=envbase.copy()
        if steps!=65536:env["NUCLEUS_EXPERIMENTAL_WORK_CEILING"]=str(steps)
        start=time.monotonic()
        with tempfile.TemporaryFile() as sink, source.open("rb") as inp:
            p=subprocess.run([str(binary.resolve())],stdin=inp,stdout=subprocess.DEVNULL,
                             stderr=sink,env=env,timeout=125)
            sink.seek(0)
            log=sink.read(8000000).decode(errors="replace")
        lines=log.splitlines()
        bads=[x for x in lines if x.startswith("NUCLEUS_NESTED_REPLAY_FAILURE:")]
        reasons=collections.Counter()
        for x in bads:
            reasons[x.split('ResidualId("',1)[1].split('")',1)[0] if 'ResidualId("' in x else "unknown"]+=1
        variant={"rc":p.returncode,"seconds":round(time.monotonic()-start,3),
            "work_report":[x for x in lines if x.startswith("NUCLEUS_WORK_CEILING:")][-1:],
            "nested_failure_count":len(bads),"nested_failure_reasons":dict(reasons),
            "last_nested_failure":[x[:1500] for x in bads[-5:]],
            "terminal":[x for x in lines if x.startswith("NUCLEUS_DOWNSTREAM:")][-1:]}
        assert variant["work_report"]==[f"NUCLEUS_WORK_CEILING:steps={steps}"],(filename,steps,variant)
        variants[str(steps)]=variant
        print("NUCLEUS_TOTAL_WORK_CASE="+json.dumps({"case":filename,"steps":steps,**variant},ensure_ascii=False),flush=True)
    assert variants["65536"]["rc"]==2,("PINNED_BASELINE_DRIFT",filename)
    rows.append({"case":filename,"sha256":digest,"arms":variants})
protect=[]
for filename in ("protected-false-index.ndjson","protected-eta-ctor-alias.ndjson"):
    source=Path("metatron-kernel/tests/fixtures")/filename
    for steps in (65536,1048576):
        env=envbase.copy()
        if steps!=65536:env["NUCLEUS_EXPERIMENTAL_WORK_CEILING"]=str(steps)
        with source.open("rb") as src:
            p=subprocess.run([str(binary.resolve())],stdin=src,stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,env=env,timeout=125)
        protect.append({"fixture":filename,"sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
                        "steps":steps,"rc":p.returncode})
        assert p.returncode in (1,2),("UNSAFE_FORGED_PROOF",filename,steps,p.returncode)
valid=[r for r in rows if "positive" in r["case"]]
invalid=[r for r in rows if "negative" in r["case"]]
valid_errors=[(r["case"],steps) for r in valid for steps,v in r["arms"].items() if v["rc"] not in (0,2)]
false_accepts=[(r["case"],steps) for r in invalid for steps,v in r["arms"].items() if v["rc"] not in (1,2)]
accepted=[(r["case"],steps) for r in valid for steps,v in r["arms"].items() if v["rc"]==0]
rejected=[(r["case"],steps) for r in invalid for steps,v in r["arms"].items() if v["rc"]==1]
decision=("DIAGNOSTIC_UNSAFE_DO_NOT_USE" if valid_errors or false_accepts
    else "PURE_FINITE_WORK_BOUNDARY" if accepted
    else "NO_COMPLETE_PROOF_AT_16X_WORK_REQUIRES_SEMANTIC_OR_REUSE_REPAIR")
report={"base_sha":"ff003e7fad888d39a40cfd2375885fe20e3209fa",
"research_sha":os.getenv("GITHUB_SHA"),
"scope":"opt-in total-work diagnostic only; no change in kernel reduction/equality rules",
"original_lean_sources":rows,"forged_negative_controls":protect,
"valid_new_accepts":accepted,"false_proof_rejections":rejected,
"incorrect_valid_rejects":valid_errors,"incorrect_false_accepts":false_accepts,
"decision":decision,"full196_qualified":False,"production_promotion":False}
(out/"decision.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print("NUCLEUS_TOTAL_WORK_DECISION="+json.dumps({
    "decision":decision,"positive_accepts":accepted,"negative_rejects":rejected,
    "errors":valid_errors,"false_accepts":false_accepts},ensure_ascii=False),flush=True)
assert not valid_errors and not false_accepts,"INVALID_DIAGNOSTIC_RESULT"
