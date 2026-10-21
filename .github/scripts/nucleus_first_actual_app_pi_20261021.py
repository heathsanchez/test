#!/usr/bin/env python3
"""First failed REAL application-function Pi on untouched independent Nucleus.

Differentiates (A) missing infer of function, (B) inferred term without Pi
exposure, and (C) apparent Pi exposed only under Full transparency. Unlike
diagnostic_neutral_source_telescope, these events come from infer_in(Expr::App)
on the original source and within its actual binder environment.

No source changes. Freeze exact hashed Lean Arena input and expected verdict
per case. All protected bads must retain their prior nonaccept verdict.
"""
from pathlib import Path
import collections, hashlib, json, os, re, subprocess, sys, time

if len(sys.argv)!=4:
    raise SystemExit("usage: app_first_pi.py ORIGINAL_CORPUS CHECKER_BINARY OUT")
root,binary,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=True)
baseline_file=Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
data=json.loads(baseline_file.read_text())["modes"]
pinned={mode:{r["case"]:r for r in info["rows"]} for mode,info in data.items()}
frozen=(
 "good/perf/magma-list-deep-n21.ndjson",
 "good/perf/magma-list-deep-n36.ndjson",
 "good/perf/magma-list-pair-n7.ndjson",
 "good/perf/magma-list-pair-n21.ndjson",
 "good/perf/grind-ring-5.ndjson",
 "good/perf/fueled-chain.ndjson",
 "good/init-prelude.ndjson"
)
flags=("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE","SUBSTITUTION_RECLOSURE",
 "TYPED_VALUE_NORMALIZATION","PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
 "TYPED_RECEIVER","SOURCE_PAIR_DEPTH8","POLYMORPHIC_PROP_IRREL",
 "PROP_SINGLETON_2P1F","EXPECTED_LAMBDA")
env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
for f in flags: env["NUCLEUS_EXPERIMENTAL_"+f]="1"
env["NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE"]="1"
env["NUCLEUS_TRACE_DOWNSTREAM"]="1"

def classify(line):
    # The kernel itself emits the complete actual function inference result.
    # Labels distinguish first Pi failure classes, without inferring an
    # absent rule or treating input shape as type authority.
    def extract(prop,end):
        if prop not in line:return "missing"
        fragment=line.split(prop,1)[1].split(end,1)[0]
        if "Unknown {" in fragment:return "UNKNOWN"
        if "Refuted {" in fragment:return "REFUTED"
        if "Proven {" in fragment:
            if "value: Pi {" in fragment:return "PROVEN_PI"
            if "value: Term(" in fragment:return "PROVEN_TERM"
            return "PROVEN_OTHER"
        return fragment[:100].strip()
    return {
       "function_type":extract("function_type=","reducible="),
       "reducible":extract("reducible=","full="),
       "full":extract("full=","<end>"),
    }

rows=[]
for name in frozen:
    source=root/name
    if not source.is_file():raise AssertionError("MISSING_CORPUS_CASE "+name)
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    assert sha==pinned["origin"][name]["sha256"],("SOURCE_DRIFT",name)
    for mode in ("origin","demand") if "/magma" in name else ("origin",):
        settings=env.copy()
        if mode=="demand": settings["NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR"]="1"
        started=time.monotonic()
        with source.open("rb") as inp:
            process=subprocess.run([str(binary.resolve())],stdin=inp,
                stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=settings,
                timeout=180)
        assert process.returncode==pinned[mode][name]["rc"],("VERDICT_CHANGED",name,mode,process.returncode)
        raw=process.stderr.decode(errors="replace")
        (out/(name.replace("/","_")+"_"+mode+".stderr")).write_text(raw)
        application=[x for x in raw.splitlines() if x.startswith("NUCLEUS_APPLICATION_FUNCTION_TYPE:")]
        failures=[{"original":text[:4600], "classification":classify(text)} for text in application]
        terminal=[x for x in raw.splitlines() if x.startswith("NUCLEUS_DOWNSTREAM:")][-1:]
        counts=collections.Counter((v["classification"]["function_type"],v["classification"]["reducible"],v["classification"]["full"]) for v in failures)
        entry={"case":name,"mode":mode,"sha256":sha,"rc":process.returncode,
            "application_pi_failures":len(application),"classes":[{"type":k,"count":v} for k,v in counts.items()],
            "first":failures[:3],"last":failures[-3:],"terminal":terminal,
            "elapsed_seconds":round(time.monotonic()-started,3)}
        rows.append(entry)
        print("NUCLEUS_APP_FIRST_PI="+json.dumps({
            "case":name,"mode":mode,"n_failures":len(application),"classes":entry["classes"],
            "first":entry["first"][:1],"last":entry["last"][-1:],"terminal":terminal,
        },ensure_ascii=False),flush=True)

controls=[]
for fixture in ("protected-false-index.ndjson","protected-eta-ctor-alias.ndjson"):
    src=Path("metatron-kernel/tests/fixtures")/fixture
    with src.open("rb") as f:
        p=subprocess.run([str(binary.resolve())],stdin=f,
                         stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                         env=env,timeout=80)
    assert p.returncode in (1,2),("UNSOUND_PROTECTED_ACCEPT",fixture,p.returncode)
    controls.append({"name":fixture,"sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"rc":p.returncode})

assert sum(row["application_pi_failures"] for row in rows)>0,"NO_REAL_PI_OBSTRUCTION_CAPTURED"
result={
 "source_sha":"ff003e7fad888d39a40cfd2375885fe20e3209fa",
 "semantic_modification":False,
 "original_hashes_verified":True,
 "no_verdict_changes":True,"controls":controls,
 "source":"original infer_in(Expr::App) printed under actual lexical Gamma",
 "binary_sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),
 "rows":rows,
 "decision":"DIAGNOSTIC_ONLY_NO_SEMANTIC_PROMOTION",
}
(out/"first-actual-application-pi.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
print("NUCLEUS_APP_FIRST_PI_DONE="+json.dumps({"cases":len(rows),"captured_pi_failures":sum(r["application_pi_failures"] for r in rows),"decision":result["decision"]}),flush=True)
