#!/usr/bin/env python3
"""Source-committed Nucleus formed-Pi guarded-conversion A/B qualification.

Source authoritative baseline: ff003e7fad888d39a40cfd2375885fe20e3209fa
Only semantic difference in the research branch: opt-in fail-closed recovery
of an independently checked Π-vs-source Π type conversion.

No benchmark-name logic, proof erasure, FreeId alias, guess or new axiom.
Protected all196 exact input hashes and individual original accepted/rejected
verdicts; candidate is allowed to turn UNKNOWN into ACCEPT only.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import hashlib,json,os,subprocess,sys,time

if len(sys.argv)!=5:
    raise SystemExit("usage: gate.py SOURCE_CORPUS BASE_BINARY CANDIDATE_BINARY EVIDENCE")
corpus,base,candidate,output=map(Path,sys.argv[1:])
output.mkdir(parents=True,exist_ok=True)
pinned_file=Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
pinned=json.loads(pinned_file.read_text())["modes"]["origin"]["rows"]
baseline={r["case"]:r for r in pinned}
flags=("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE","SUBSTITUTION_RECLOSURE",
       "TYPED_VALUE_NORMALIZATION","PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
       "TYPED_RECEIVER","SOURCE_PAIR_DEPTH8","POLYMORPHIC_PROP_IRREL",
       "PROP_SINGLETON_2P1F","EXPECTED_LAMBDA")
environment={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
for flag in flags:
    environment["NUCLEUS_EXPERIMENTAL_"+flag]="1"
cases=[(part,src) for part in ("good","bad") for src in sorted((corpus/part).rglob("*.ndjson"))]
assert len(cases)==196 and sum(part=="good" for part,_ in cases)==125
assert sum(part=="bad" for part,_ in cases)==71
rows=[]; changes=[]; firings=Counter()
def run(binary:Path, case:Path, candidate_on:bool, trace:bool):
    env=environment.copy()
    if candidate_on:
        env["NUCLEUS_EXPERIMENTAL_FORMED_PI_GUARD"]="1"
        if trace:
            env["NUCLEUS_TRACE_FORMED_PI_GUARD"]="1"
    env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
    start=time.monotonic()
    with case.open("rb") as f:
        r=subprocess.run([str(binary.resolve())],stdin=f,stdout=subprocess.DEVNULL,
                         stderr=subprocess.PIPE,env=env,timeout=180)
    lines=r.stderr.decode(errors="replace").splitlines()
    return r.returncode, {
      "duration":round(time.monotonic()-start,3),
      "terminal":[x for x in lines if x.startswith("NUCLEUS_DOWNSTREAM:")][-1:],
      "candidate_witnesses":[x[:1500] for x in lines if x.startswith("NUCLEUS_FORMED_PI_GUARD:")][:36],
    }
targeted={"good/perf/magma-list-deep-n21.ndjson","good/perf/magma-list-deep-n36.ndjson",
          "good/perf/magma-list-pair-n7.ndjson","good/perf/magma-list-pair-n21.ndjson",
          "good/perf/grind-ring-5.ndjson","good/perf/fueled-chain.ndjson"}
for part,case in cases:
    name=str(case.relative_to(corpus))
    reference=baseline[name]
    sha=hashlib.sha256(case.read_bytes()).hexdigest()
    assert reference["sha256"]==sha,("INPUT_SHA_DRIFT",name)
    control,control_evidence=run(base,case,False,False)
    assert control==reference["rc"],("PINNED_REFERENCE_VERDICT_DRIFT",name,control,reference["rc"])
    experimental,experimental_evidence=run(candidate,case,True,name in targeted)
    assert experimental in (0,1,2),("CANDIDATE_RUNTIME_FAILURE",name,experimental)
    if reference["rc"] in (0,1):
        assert experimental==reference["rc"],("PROTECTED_VERDICT_REGRESSION",name,reference["rc"],experimental)
    else:
        assert experimental in (0,2),("FALSE_REJECT_VALID",name,experimental)
    assert (part!="bad" or experimental==1),("BAD_TEST_NOT_REJECTED",name,experimental)
    count=len(experimental_evidence["candidate_witnesses"])
    if count:
        firings[name]=count
    row={"case":name,"group":part,"sha256":sha,"baseline_rc":control,
         "candidate_rc":experimental,"original":control_evidence,"candidate":experimental_evidence}
    rows.append(row)
    if control!=experimental:
        changes.append(row)
        print("NUCLEUS_PI_RECOVERY_CHANGED="+json.dumps({"case":name,"old":control,"new":experimental},ensure_ascii=False),flush=True)
    if name in targeted:
        print("NUCLEUS_PI_RECOVERY_TARGET="+json.dumps({
            "case":name,"baseline":control,"candidate":experimental,
            "trace_firings":count,"terminal":experimental_evidence["terminal"]},ensure_ascii=False),flush=True)
counts={str(rc):sum(r["candidate_rc"]==rc for r in rows) for rc in (0,1,2)}
base_counts={str(rc):sum(r["baseline_rc"]==rc for r in rows) for rc in (0,1,2)}
assert base_counts=={"0":119,"1":71,"2":6},base_counts
assert counts["1"]==71 and counts["0"]>=119 and counts["2"]<=6,counts
protected=[]
for name in ("protected-false-index.ndjson","protected-eta-ctor-alias.ndjson"):
    p=Path("metatron-kernel/tests/fixtures")/name
    for side,binary,enabled in (("original",base,False),("candidate",candidate,True)):
        rc,details=run(binary,p,enabled,False)
        assert rc in (1,2),("FALSE_ACCEPT_PROTECTED_NEGATIVE",name,side,rc)
        protected.append({"source":name,"variant":side,"rc":rc,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
report={"independent_kernel":"metatron-kernel",
        "baseline_source":"heathsanchez/test@ff003e7fad888d39a40cfd2375885fe20e3209fa",
        "candidate_source":os.environ.get("GITHUB_SHA"),
        "instrumentation":"opt-in exact-source formed Pi guarded recovery only",
        "input_sha256_manifest":hashlib.sha256(pinned_file.read_bytes()).hexdigest(),
        "binary_sha256":{"baseline":hashlib.sha256(base.read_bytes()).hexdigest(),"candidate":hashlib.sha256(candidate.read_bytes()).hexdigest()},
        "frozen196":{"baseline":base_counts,"candidate":counts},
        "new_full_accepts":[x["case"] for x in changes if x["candidate_rc"]==0],
        "candidate_firing_cases":dict(firings),"all_rows":rows,
        "protected_negative_controls":protected,
        "verdicts_preserved":True,
        "decision":"CANDIDATE_NEW_FULL_ACCEPT_PENDING_BROADER_GATES" if changes else "NO_NEW_FULL_ACCEPT_DO_NOT_PROMOTE",
        "qualified_current_arena":False,"full_mathlib_accepted":False,
        "official_rank_measured":False}
(output/"candidate-results.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print("NUCLEUS_PI_RECOVERY_DECISION="+json.dumps({k:report[k] for k in
   ("frozen196","new_full_accepts","candidate_firing_cases","decision")}),flush=True)
