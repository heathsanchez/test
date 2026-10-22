#!/usr/bin/env python3
"""Locate original-source binder ownership of nested recursor majors in Nucleus.

Diagnostic only: compare the unchanged independently qualified checker to a
byte-equivalent checker plus opt-in cfg(diagnostics) trace. Neither evaluator
nor typechecking rules change. Every source input has a pinned SHA256.
"""
import hashlib,json,os,pathlib,re,subprocess,sys,collections,time
if len(sys.argv)!=5:
    raise SystemExit("usage: script.py MICRO_DIR BASE_BIN DIAGNOSTIC_BIN EVIDENCE_DIR")
folder,original,diagnostic,out=map(pathlib.Path,sys.argv[1:])
out.mkdir(parents=True,exist_ok=True)
hashes={
    "magma-list-pair-n7.ndjson-positive.ndjson":"49731dc62ab70379f78fa8b4aa346a373ca2df5a2cf0bde8f713d1962d46f546",
    "magma-list-pair-n7.ndjson-negative.ndjson":"658f1dbb5281237ff1112d67e9fd4a3da2960784d4a08c3c5b25b5a4e53683b7",
    "magma-list-pair-n21.ndjson-positive.ndjson":"52dcb4dd5e3b427d820f72beca1d430740f25831e3d90f3e71a303884fcbd4af",
    "magma-list-pair-n21.ndjson-negative.ndjson":"a5e0b2d6a56f95f4d6d7c187f29c7c2b2fb2f246faae8ed0e49d682f146cbb29"
}
flags=("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE","SUBSTITUTION_RECLOSURE",
       "TYPED_VALUE_NORMALIZATION","PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
       "TYPED_RECEIVER","SOURCE_PAIR_DEPTH8","POLYMORPHIC_PROP_IRREL",
       "PROP_SINGLETON_2P1F","EXPECTED_LAMBDA")
base_env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
base_env.update({"NUCLEUS_EXPERIMENTAL_"+flag:"1" for flag in flags})
base_env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
pattern=re.compile(r"^NUCLEUS_PROJECTION_MAJOR_BINDING:")
rows=[]
for filename,sha in hashes.items():
    path=folder/filename
    assert path.is_file(),filename
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha,("INPUT_SOURCE_SHA_DRIFT",filename)
    record={"case":filename,"sha256":sha,"arms":{}}
    for arm,exe,trace in [("original",original,False),("trace_only",diagnostic,True)]:
        env=base_env.copy()
        if trace:env["NUCLEUS_TRACE_PROJECTION_MAJOR_BINDING"]="1"
        begin=time.monotonic()
        with path.open("rb") as source:
            result=subprocess.run([str(exe.resolve())],stdin=source,
                stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env,timeout=160)
        stderr=result.stderr.decode(errors="replace")
        assert result.returncode==2,(filename,arm,"VERDICT_DRIFT",result.returncode,stderr[-400:])
        traces=[x for x in stderr.splitlines() if pattern.match(x)]
        terminal=[x for x in stderr.splitlines() if x.startswith("NUCLEUS_DOWNSTREAM:")][-1:]
        category=collections.Counter(
            ("actual_source_bvar" if "source_major=Some(Closure { expr: ExprId(6)" in x
                else "other_major")
            for x in traces
        )
        record["arms"][arm]={
            "rc":result.returncode,"seconds":round(time.monotonic()-begin,4),
            "terminal":terminal,"event_count":len(traces),"source_class_counts":dict(category),
            "events":traces
        }
        print("NUCLEUS_MAJOR_BINDING="+json.dumps({
            "input":filename,"arm":arm,"rc":result.returncode,
            "events":len(traces),"samples":traces[:6],"terminal":terminal
        },ensure_ascii=False),flush=True)
    assert record["arms"]["trace_only"]["terminal"]==record["arms"]["original"]["terminal"],filename
    rows.append(record)
assert any(x["arms"]["trace_only"]["event_count"]>0 for x in rows),"NO_ACTUAL_MAJOR_BINDINGS_OBSERVED"
neg=[]
for file in ("protected-false-index.ndjson","protected-eta-ctor-alias.ndjson"):
    path=pathlib.Path("metatron-kernel/tests/fixtures")/file
    assert path.is_file()
    for arm,exe in [("original",original),("trace_only",diagnostic)]:
        with path.open("rb") as source:
            proc=subprocess.run([str(exe.resolve())],stdin=source,
                stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=base_env,timeout=45)
        assert proc.returncode in (1,2),(file,arm,proc.returncode)
        neg.append({"fixture":file,"mode":arm,"rc":proc.returncode,
                    "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
report={"source_authority":"heathsanchez/test@ff003e7fad888d39a40cfd2375885fe20e3209fa",
        "source_tree_modified":"machine.rs diagnostic-only, no semantic edits",
        "original_baseline_nonaccept":True,
        "rows":rows,"forged_negative_controls":neg,
        "decision":"BINDING_PROVENANCE_DIAGNOSTIC_ONLY",
        "candidate_repair_accepted":False}
(out/"major-binding-source.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print("NUCLEUS_MAJOR_BINDING_DECISION="+json.dumps({
 "decision":report["decision"],"traces":sum(x["arms"]["trace_only"]["event_count"] for x in rows),
 "frozen_verdicts_unchanged":True}),flush=True)
