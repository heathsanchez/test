#!/usr/bin/env python3
"""Factorial major/RHS recursor budget transport under one unchanged total account.

The only candidate difference is how the existing account is distributed
between verified source-owned major and RHS reductions: 512 or up to 4096.
No new proof equality, Nat value inference, axiom, or additional global fuel.

Require original Lean positive/false micro proof pairs, original SHA-pinned
Arena196 and protected invalids. Re-run all196 for the combined arm even
if no sampled improvement, because a safe performance/semantic side effect
must not silently change the protected corpus.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,collections
if len(sys.argv)!=6:raise SystemExit("usage: gate.py MICRO_DIR ARENA_DIR BASE_BIN CANDIDATE_BIN EVIDENCE_DIR")
micro,arena,baseline,candidate,out=map(Path,sys.argv[1:])
out.mkdir(parents=True,exist_ok=True)
pinned_file=Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
pinned={r["case"]:r for r in json.loads(pinned_file.read_text())["modes"]["origin"]["rows"]}
assert len(pinned)==196
known={
"magma-list-pair-n7.ndjson-positive.ndjson":"49731dc62ab70379f78fa8b4aa346a373ca2df5a2cf0bde8f713d1962d46f546",
"magma-list-pair-n7.ndjson-negative.ndjson":"658f1dbb5281237ff1112d67e9fd4a3da2960784d4a08c3c5b25b5a4e53683b7",
"magma-list-pair-n21.ndjson-positive.ndjson":"52dcb4dd5e3b427d820f72beca1d430740f25831e3d90f3e71a303884fcbd4af",
"magma-list-pair-n21.ndjson-negative.ndjson":"a5e0b2d6a56f95f4d6d7c187f29c7c2b2fb2f246faae8ed0e49d682f146cbb29",
}
modes=("baseline","candidate_off","major","rhs","both")
flags=("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE","SUBSTITUTION_RECLOSURE",
"TYPED_VALUE_NORMALIZATION","PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
"TYPED_RECEIVER","SOURCE_PAIR_DEPTH8","POLYMORPHIC_PROP_IRREL",
"PROP_SINGLETON_2P1F","EXPECTED_LAMBDA")
baseenv={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
for k in flags:baseenv["NUCLEUS_EXPERIMENTAL_"+k]="1"
baseenv["NUCLEUS_TRACE_DOWNSTREAM"]="1"

def run(path,mode,trace=False,timeout=180):
    env=baseenv.copy()
    if mode in ("major","both"):env["NUCLEUS_EXPERIMENTAL_RECURSOR_MAJOR_TRANSPORT"]="1"
    if mode in ("rhs","both"):env["NUCLEUS_EXPERIMENTAL_RECURSOR_RHS_TRANSPORT"]="1"
    if trace:env["NUCLEUS_TRACE_RECURSOR_BUDGET_TRANSPORT"]="1"
    binary=baseline if mode=="baseline" else candidate
    start=time.monotonic()
    with path.open("rb") as source:
        p=subprocess.run([str(binary.resolve())],stdin=source,
                        stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                        env=env,timeout=timeout)
    stderr=p.stderr.decode(errors="replace")
    lines=stderr.splitlines()
    traces=[z for z in lines if z.startswith("NUCLEUS_RECURSOR_BUDGET_TRANSPORT:")]
    failures=[z for z in lines if z.startswith("NUCLEUS_NESTED_REPLAY_FAILURE:")]
    return {"rc":p.returncode,"elapsed_s":round(time.monotonic()-start,3),
            "phase_counts":dict(collections.Counter(
               z.split(":phase=",1)[1].split(":",1)[0] for z in traces)),
            "traces":traces[:12],"failures":failures[-6:],
            "terminal":[z for z in lines if z.startswith("NUCLEUS_DOWNSTREAM:")][-1:]}

micro_rows=[]
for name,digest in known.items():
    file=micro/name
    assert hashlib.sha256(file.read_bytes()).hexdigest()==digest,("MICRO_HASH_DRIFT",name)
    variants={mode:run(file,mode,mode in ("major","rhs","both"),180) for mode in modes}
    assert variants["baseline"]["rc"]==variants["candidate_off"]["rc"]==2,("UNSAFE_OPTOUT",name)
    for mode in modes[2:]:
        assert variants[mode]["rc"] in ((0,2) if "positive" in name else (1,2)),("UNSAFE_MICRO",name,mode,variants[mode])
    micro_rows.append({"case":name,"sha256":digest,"variants":variants})
    print("NUCLEUS_BUDGET_MICRO="+json.dumps({"case":name,"variants":{k:{"rc":v["rc"],"phase_counts":v["phase_counts"],"terminal":v["terminal"]} for k,v in variants.items()}},ensure_ascii=False),flush=True)

targets=("good/init-prelude.ndjson","good/perf/magma-list-pair-n7.ndjson","good/perf/magma-list-pair-n21.ndjson",
         "good/perf/magma-list-deep-n21.ndjson","good/perf/magma-list-deep-n36.ndjson",
         "good/perf/grind-ring-5.ndjson","good/perf/fueled-chain.ndjson")
target_rows=[]
for name in targets:
    path=arena/name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==pinned[name]["sha256"]
    variants={m:run(path,m, m in ("major","rhs","both"),185) for m in modes}
    assert variants["baseline"]["rc"]==variants["candidate_off"]["rc"]==pinned[name]["rc"],("BAD_CONTROL",name,variants)
    for m in modes[2:]:
        assert variants[m]["rc"] in ((0,2) if pinned[name]["rc"]==2 else (pinned[name]["rc"],)),("INVALID_TARGET",name,m,variants[m])
    target_rows.append({"case":name,"sha256":pinned[name]["sha256"],"variants":variants})
    print("NUCLEUS_BUDGET_TARGET="+json.dumps({"case":name,"variants":{k:{"rc":v["rc"],"phase_counts":v["phase_counts"],"terminal":v["terminal"]} for k,v in variants.items()}},ensure_ascii=False),flush=True)

positive_modes=[]
for mode in modes[2:]:
    if any(x["variants"][mode]["rc"]==0 and x["variants"]["baseline"]["rc"]==2 for x in micro_rows+target_rows):
        positive_modes.append(mode)
chosen=sorted(set(["both",*positive_modes]),key=lambda s:modes.index(s))
all_cases=[(bucket,p) for bucket in ("good","bad") for p in sorted((arena/bucket).rglob("*.ndjson"))]
assert len(all_cases)==196
full_rows=[]
for bucket,p in all_cases:
    name=str(p.relative_to(arena))
    assert hashlib.sha256(p.read_bytes()).hexdigest()==pinned[name]["sha256"],("INPUT_DRIFT",name)
    outcome={"case":name,"source_sha256":pinned[name]["sha256"],"baseline_rc":pinned[name]["rc"]}
    for mode in chosen:
        v=run(p,mode,False,185)
        assert v["rc"] in (0,1,2),("RUNTIME_ERROR",name,mode,v)
        if pinned[name]["rc"] in (0,1):
            assert v["rc"]==pinned[name]["rc"],("PROTECTED_VERDICT_REGRESSION",name,mode,v)
        else:
            assert v["rc"] in (0,2),("VALID_PROOF_REJECTED",name,mode,v)
        assert (bucket!="bad" or v["rc"]==1),("BAD_PROOF_NOT_REJECTED",name,mode,v)
        outcome[mode]=v["rc"]
    full_rows.append(outcome)
counts={mode:{str(rc):sum(row[mode]==rc for row in full_rows) for rc in (0,1,2)} for mode in chosen}
assert all(x["1"]==71 and x["0"]>=119 for x in counts.values())
protect=[]
for name in ("protected-false-index.ndjson","protected-eta-ctor-alias.ndjson"):
    p=Path("metatron-kernel/tests/fixtures")/name
    outcomes={mode:run(p,mode)["rc"] for mode in (*modes[0:1],*chosen)}
    assert all(v in (1,2) for v in outcomes.values()),("FORGED_PROOF_ACCEPTED",name,outcomes)
    protect.append({"name":name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"outcomes":outcomes})

micro_gains={mode:[x["case"] for x in micro_rows if x["variants"][mode]["rc"]==0] for mode in modes[2:]}
full_gains={mode:[x["case"] for x in full_rows if x[mode]==0 and x["baseline_rc"]==2] for mode in chosen}
status="NEW_FULL_POSITIVE_CANDIDATE" if any(full_gains.values()) else ("MICRO_POSITIVE_ONLY" if any(micro_gains.values()) else "NO_NEW_PROOF_ACCEPT_NO_PROMOTION")
report={"source_base":"heathsanchez/test@ff003e7fad888d39a40cfd2375885fe20e3209fa",
        "source_candidate":os.getenv("GITHUB_SHA"),
        "intervention":"reuse existing finite global work across source-checked recursor major/RHS without changing source iota rules",
        "unchanged_global_budget":65536,
        "micro":micro_rows,"target":target_rows,"full_rows":full_rows,
        "modes_full196":chosen,"counts":counts,"protect":protect,
        "micro_gains":micro_gains,"full_gains":full_gains,"decision":status,
        "qualified_full_mathlib":False,"official_arena_rank":False}
(out/"decision.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print("NUCLEUS_BUDGET_DECISION="+json.dumps({k:report[k] for k in ("modes_full196","counts","micro_gains","full_gains","decision")},ensure_ascii=False),flush=True)
