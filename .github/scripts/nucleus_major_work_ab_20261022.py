#!/usr/bin/env python3
"""Soundness-aware A/B of source recursor-major LOCAL work limits.

The global Nucleus 65,536 judgment-step limit and all kernel rules remain
unchanged. Trial A increases registered nested-major exposure cap 512->2048;
trial B increases source-qualified Bool/Nat constructor-major cap 128/256->1024.
Factorial A/B is run on original Lean-exported finite-decision positives and
the same original source with only the expected Boolean falsified.

This is a bounded diagnostic, NOT a general soundness proof or whole Arena
qualification. A green workflow can report NO_GAIN.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
if len(sys.argv)!=3:raise SystemExit("usage: GATE ORIGINAL_MICROS EVIDENCE")
micro,out=map(Path,sys.argv[1:])
out.mkdir(parents=True,exist_ok=True)
names={
 "n7-pos":("magma-list-pair-n7.ndjson-positive.ndjson","49731dc62ab70379f78fa8b4aa346a373ca2df5a2cf0bde8f713d1962d46f546"),
 "n7-neg":("magma-list-pair-n7.ndjson-negative.ndjson","658f1dbb5281237ff1112d67e9fd4a3da2960784d4a08c3c5b25b5a4e53683b7"),
 "n21-pos":("magma-list-pair-n21.ndjson-positive.ndjson","52dcb4dd5e3b427d820f72beca1d430740f25831e3d90f3e71a303884fcbd4af"),
 "n21-neg":("magma-list-pair-n21.ndjson-negative.ndjson","a5e0b2d6a56f95f4d6d7c187f29c7c2b2fb2f246faae8ed0e49d682f146cbb29"),
}
arms=("baseline","nested","constructor","both")
flags=("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE","SUBSTITUTION_RECLOSURE",
 "TYPED_VALUE_NORMALIZATION","PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
 "TYPED_RECEIVER","SOURCE_PAIR_DEPTH8","POLYMORPHIC_PROP_IRREL",
 "PROP_SINGLETON_2P1F","EXPECTED_LAMBDA")
env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
for flag in flags:env["NUCLEUS_EXPERIMENTAL_"+flag]="1"
env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
env["NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE"]="1"
rows=[]
def invoke(binary,path,arm,trace):
    trial_env=env.copy()
    if arm in ("nested","both"):
        trial_env["NUCLEUS_EXPERIMENTAL_NESTED_MAJOR_2048"]="1"
        if trace:trial_env["NUCLEUS_TRACE_MAJOR_REBUDGET"]="1"
    if arm in ("constructor","both"):
        trial_env["NUCLEUS_EXPERIMENTAL_CONSTRUCTOR_MAJOR_1024"]="1"
    before=time.monotonic()
    with path.open("rb") as inp:
        r=subprocess.run([str(binary.resolve())],stdin=inp,stdout=subprocess.DEVNULL,
          stderr=subprocess.PIPE,env=trial_env,timeout=240)
    lines=r.stderr.decode(errors="replace").splitlines()
    return {"rc":r.returncode,"wall_s":round(time.monotonic()-before,3),
            "terminal":[l for l in lines if l.startswith("NUCLEUS_DOWNSTREAM:")][-1:],
            "nested_replay_failures":[l[:500] for l in lines if l.startswith("NUCLEUS_NESTED_REPLAY_FAILURE:")][-8:],
            "major_budget_events":[l[:500] for l in lines if l.startswith("NUCLEUS_MAJOR_REBUDGET:")][:8],
            "diagnostic_line_count":sum(l.startswith("NUCLEUS_") for l in lines)}
for case,(name,sha) in names.items():
    path=micro/name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha,("BYTE_IDENTITY",case)
    for arm in arms:
        binary=Path("/tmp/nucleus-major/"+("baseline" if arm=="baseline" else "candidate"))
        row=invoke(binary,path,arm,True)
        if arm=="baseline":assert row["rc"]==2,("BASELINE_DRIFT",case,row["rc"])
        if case.endswith("-pos"):assert row["rc"] in (0,2),("VALID_REJECTED",case,arm,row)
        else:assert row["rc"] in (1,2),("FALSE_ACCEPT",case,arm,row)
        entry={"case":case,"arm":arm,"input_sha256":sha,**row}
        rows.append(entry)
        print("NUCLEUS_MAJOR_WORK_CASE="+json.dumps(entry,ensure_ascii=False),flush=True)
extra=[]
for name in ("protected-false-index.ndjson","protected-eta-ctor-alias.ndjson"):
    p=Path("metatron-kernel/tests/fixtures")/name
    for arm in arms:
        binary=Path("/tmp/nucleus-major/"+("baseline" if arm=="baseline" else "candidate"))
        row=invoke(binary,p,arm,False)
        assert row["rc"] in (1,2),("FORGED_PROOF_ACCEPTED",name,arm,row)
        extra.append({"name":name,"arm":arm,"rc":row["rc"],"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
positives=[row for row in rows if row["case"].endswith("-pos") and row["rc"]==0]
report={"source_sha":"ff003e7fad888d39a40cfd2375885fe20e3209fa",
        "candidate_commit":os.environ.get("GITHUB_SHA"),
        "same_global_work_limit":True,"no_new_conversion_authority":True,
        "rows":rows,"protected_mutants":extra,
        "new_positive_subproofs":[{"case":row["case"],"arm":row["arm"]} for row in positives],
        "decision":"PROMISING_SUBPROOF_GO_196" if positives else "NO_POSITIVE_COMPLETION_DO_NOT_PROMOTE",
        "qualified_196":False,"full_mathlib":False}
(out/"major-work-ab.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print("NUCLEUS_MAJOR_WORK_DECISION="+json.dumps({
 "decision":report["decision"],"new_positive_subproofs":report["new_positive_subproofs"],
 "protected_mutants":len(extra)}),flush=True)
