#!/usr/bin/env python3
"""Source-derived stuck-recursor projection A/B: NO constructor guesses.

Run same SHA-pinned original Nucleus with and without one opt-in semantic rule.
Preserve all 196 exact source hashes and existing valid/invalid verdicts, two
additional forged negatives, and four independent Lean-derived decide
subproofs (two valid / two false). Never infer victory from a green diagnostic.
"""
from pathlib import Path
import hashlib, json, os, subprocess, sys, time
if len(sys.argv)!=6:
    raise SystemExit("usage: gate.py PORTABLE MICRO CONTROL_BIN CANDIDATE_BIN EVIDENCE")
corpus,micro,base,candidate,out=map(Path,sys.argv[1:])
out.mkdir(exist_ok=True,parents=True)
manifest=Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
entries=json.loads(manifest.read_text())["modes"]["origin"]["rows"]
ground={r["case"]:r for r in entries}
assert len(entries)==196
flags=("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE","SUBSTITUTION_RECLOSURE",
       "TYPED_VALUE_NORMALIZATION","PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
       "TYPED_RECEIVER","SOURCE_PAIR_DEPTH8","POLYMORPHIC_PROP_IRREL",
       "PROP_SINGLETON_2P1F","EXPECTED_LAMBDA")
env_base={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
for flag in flags:
    env_base["NUCLEUS_EXPERIMENTAL_"+flag]="1"
env_base["NUCLEUS_TRACE_DOWNSTREAM"]="1"
def execute(binary:Path,file:Path,enabled:bool,trace:bool=False)->dict:
    env=env_base.copy()
    if enabled:
        env["NUCLEUS_EXPERIMENTAL_STUCK_RECURSOR_PROJECTION"]="1"
        if trace:env["NUCLEUS_TRACE_STUCK_RECURSOR_PROJECTION"]="1"
    t=time.monotonic()
    with file.open("rb") as fd:
        p=subprocess.run([str(binary.resolve())],stdin=fd,stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,timeout=180,env=env)
    lines=p.stderr.decode(errors="replace").splitlines()
    events=[x for x in lines if x.startswith("NUCLEUS_STUCK_RECURSOR_PROJECTION:")]
    tails=[x for x in lines if x.startswith("NUCLEUS_DOWNSTREAM:")][-1:]
    return {"rc":p.returncode,"wall_s":round(time.monotonic()-t,3),
            "events":len(events),"event_samples":[s[:500] for s in events[:5]],
            "terminal":tails}
micro_rows=[]
for source in sorted(micro.glob("magma-list-pair-*.ndjson-*.ndjson")):
    kind="positive" if "-positive.ndjson" in source.name else "negative"
    expected=0 if kind=="positive" else 1
    control=execute(base,source,False)
    changed=execute(candidate,source,True,True)
    assert control["rc"]==2,("MICRO_ORIGINAL_CHANGED",source.name,control)
    assert changed["rc"] in (expected,2),("MICRO_WRONG_VERDICT",source.name,changed)
    item={"source":source.name,"expect":expected,"sha":hashlib.sha256(source.read_bytes()).hexdigest(),
          "base":control,"candidate":changed}
    micro_rows.append(item)
    print("NUCLEUS_STUCK_PROJECTION_MICRO="+json.dumps({
        "source":source.name,"reference":expected,"base":control["rc"],"candidate":changed["rc"],
        "events":changed["events"],"terminal":changed["terminal"]}),flush=True)
assert len(micro_rows)==4,("MISSING_MICRO_PROOFS",len(micro_rows))
corpus_rows=[]
for kind in ("good","bad"):
    for path in sorted((corpus/kind).rglob("*.ndjson")):
        name=str(path.relative_to(corpus))
        entry=ground[name]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry["sha256"],("INPUT_HASH_DRIFT",name)
        control=execute(base,path,False)
        assert control["rc"]==entry["rc"],("ORIGINAL_CHECKER_VERDICT_DRIFT",name,control["rc"],entry["rc"])
        changed=execute(candidate,path,True,name.startswith("good/perf/magma"))
        rc=changed["rc"]
        assert rc in (0,1,2),("RUNTIME_ERROR",name,changed)
        if entry["rc"] in (0,1):
            assert rc==entry["rc"],("REGRESSION",name,entry["rc"],rc)
        else:
            assert rc==0 or rc==2,("UNSOUND_FALSE_REJECT",name,rc)
        assert kind=="good" or rc==1,("INVALID_CASE_NOT_REJECTED",name,rc)
        row={"case":name,"group":kind,"baseline":control["rc"],"candidate":rc,
             "sha":entry["sha256"],"candidate_events":changed["events"],
             "candidate_first_events":changed["event_samples"],
             "candidate_terminal":changed["terminal"],
             "candidate_wall":changed["wall_s"]}
        corpus_rows.append(row)
        if control["rc"]!=rc:
            print("NUCLEUS_STUCK_PROJECTION_CHANGED="+json.dumps(row),flush=True)
        if name.startswith("good/perf/magma"):
            print("NUCLEUS_STUCK_PROJECTION_TARGET="+json.dumps({
                "case":name,"baseline":control["rc"],"candidate":rc,
                "events":changed["events"],"terminal":changed["terminal"]}),flush=True)
assert len(corpus_rows)==196
counts={str(k):sum(x["candidate"]==k for x in corpus_rows) for k in (0,1,2)}
assert counts["1"]==71 and counts["0"]>=119 and counts["2"]<=6,counts
adversarial=[]
for p in (Path("metatron-kernel/tests/fixtures/protected-false-index.ndjson"),
          Path("metatron-kernel/tests/fixtures/protected-eta-ctor-alias.ndjson")):
    for arm,binary,enabled in (("base",base,False),("candidate",candidate,True)):
        r=execute(binary,p,enabled)
        assert r["rc"] in (1,2),("FORGED_INVALID_ACCEPT",p,arm,r)
        adversarial.append({"fixture":p.name,"variant":arm,"rc":r["rc"],"sha":hashlib.sha256(p.read_bytes()).hexdigest()})
new=[x["case"] for x in corpus_rows if x["baseline"]==2 and x["candidate"]==0]
decision="BOUNDED_CANDIDATE_NEW_ACCEPT_NEEDS_FULL_ARENA" if new else "NO_NEW_WHOLE_ACCEPT_DO_NOT_PROMOTE"
report={"upstream_independent_nucleus":"ff003e7fad888d39a40cfd2375885fe20e3209fa",
        "original_manifest_sha":hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "binaries_sha256":{"base":hashlib.sha256(base.read_bytes()).hexdigest(),
                           "candidate":hashlib.sha256(candidate.read_bytes()).hexdigest()},
        "rule":"source-qualified neutral recursor projection; never guess a constructor",
        "source_commit":os.environ.get("GITHUB_SHA"),
        "micro":micro_rows,"frozen196":corpus_rows,"frozen196_counts":counts,
        "protected":adversarial,"new_whole_accepts":new,"decision":decision,
        "actual_full_mathlib_ACCEPT":False,"official_arena_rank":False}
(out/"decision.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print("NUCLEUS_STUCK_PROJECTION_DECISION="+json.dumps({
    "counts":counts,"new_whole_accepts":new,"decision":decision,
    "micro":{r["source"]:r["candidate"]["rc"] for r in micro_rows}}),flush=True)
