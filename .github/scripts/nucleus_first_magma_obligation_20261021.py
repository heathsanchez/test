#!/usr/bin/env python3
"""First missing source-derived Nucleus operation across six frozen Arena positives.

This is a DIAGNOSTIC ONLY. The checker under test is identical to the source
qualified at ff003e7fad888d39a40cfd2375885fe20e3209fa. No new equality
rule, inferred constructor or proof-irrelevance allowance is installed.

The frozen 196-case manifest provides each SHA256 and baseline expected exit.
Trace flags must not change any verdict. The four Magma cases share an original
countermodel source declaration but need not share a sufficient repair.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

if len(sys.argv) != 4:
    raise SystemExit("usage: script.py ORIGINAL_FROZEN_CORPUS NUCLEUS_BINARY EVIDENCE_DIR")
corpus, binary, out = map(Path, sys.argv[1:])
out.mkdir(parents=True, exist_ok=True)
assert binary.is_file()
manifest=Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
pinned=json.loads(manifest.read_text())["modes"]
origins={r["case"]:r for r in pinned["origin"]["rows"]}
demand={r["case"]:r for r in pinned["demand"]["rows"]}

focus=(
 "good/init-prelude.ndjson",
 "good/perf/magma-list-pair-n7.ndjson",
 "good/perf/magma-list-pair-n21.ndjson",
 "good/perf/magma-list-deep-n21.ndjson",
 "good/perf/magma-list-deep-n36.ndjson",
 "good/perf/grind-ring-5.ndjson",
 "good/perf/fueled-chain.ndjson",
)
magma=tuple(x for x in focus if "/magma-" in x)
for name in focus:
    path=corpus/name
    assert path.is_file(), name
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    assert origins[name]["sha256"]==actual,(name,"original-source-hash-mismatch")
    assert demand[name]["sha256"]==actual,(name,"demand-source-hash-mismatch")

flags=("RELEVANCE","CONTEXT_BINDER","TYPED_LINEAGE","SUBSTITUTION_RECLOSURE",
 "TYPED_VALUE_NORMALIZATION","PROJECTION_CONTEXT","PROJECTION_CROSSFRAME_512",
 "TYPED_RECEIVER","SOURCE_PAIR_DEPTH8","POLYMORPHIC_PROP_IRREL",
 "PROP_SINGLETON_2P1F","EXPECTED_LAMBDA")
base_env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
for f in flags:
    base_env["NUCLEUS_EXPERIMENTAL_"+f]="1"
base_env["NUCLEUS_TRACE_DOWNSTREAM"]="1"

trace_flags=(
 "NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE",
 "NUCLEUS_TRACE_FIRST_TYPED_CONTINUATION",
 "NUCLEUS_TRACE_DECIDABLE_MAJOR_CHAIN",
 "NUCLEUS_TRACE_PROJECTION_FIELD_FAILURE",
 "NUCLEUS_TRACE_NESTED_RECURSOR_IOTA",
)
def extract_original_source(case: str) -> dict:
    path=corpus/case
    # The source record is authoritative even where the checker returns UNKNOWN.
    names={}
    targets=[]
    lines=0
    with path.open("rb") as fd:
        for raw in fd:
            lines+=1
            obj=json.loads(raw)
            if "in" in obj:
                names[obj["in"]]=obj
            for kind in ("def","thm","opaque","axiom"):
                v=obj.get(kind)
                if isinstance(v,dict):
                    targets.append((kind,v))
    def name(n:int,seen=None)->str:
        if not n:
            return ""
        if seen is None: seen=set()
        if n in seen or len(seen)>32:
            return "<cyclic-name>"
        row=names.get(n)
        if row is None:
            return f"<name:{n}>"
        data=row.get("str") or row.get("num") or {}
        if not isinstance(data,dict):
            return f"<name:{n}>"
        parent=data.get("pre",0)
        part=data.get("str",data.get("i",""))
        prefix=name(parent,seen|{n})
        return (prefix+"." if prefix else "")+str(part)
    decls=[]
    selected=Counter()
    for kind,record in targets:
        fullname=name(record.get("name",0))
        if fullname.endswith(".countermodel") or fullname=="countermodel":
            decls.append({"kind":kind,"name":fullname,"type_expr":record.get("type"),
                          "value_expr":record.get("value"),
                          "level_parameters":record.get("levelParams",[])})
        if fullname in ("Decidable.rec","Bool.rec","Nat.rec","Eq.refl","Bool.true"):
            selected[fullname]+=1
    return {"case":case,"records":lines,"countermodel_declarations":decls[:6],
            "declared_recursor_name_occurrences":dict(selected)}

def run_case(case:str,mode:str,trace:bool)->dict:
    path=corpus/case
    env=base_env.copy()
    if mode=="demand":
        env["NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR"]="1"
    if trace:
        for key in trace_flags:
            env[key]="1"
    started=time.monotonic()
    with path.open("rb") as f:
        proc=subprocess.run([str(binary.resolve())],stdin=f,capture_output=True,
                            timeout=180,env=env)
    duration=time.monotonic()-started
    raw=proc.stderr.decode(errors="replace")
    # Each diagnostic source remains attached to the exact original case.
    prefix="".join(c if c.isalnum() or c in "._-" else "_" for c in case)
    tag=f"{prefix}-{mode}-{'trace' if trace else 'reference'}"
    (out/(tag+".stderr")).write_text(raw[:1250000]+"\n...TRUNCATED\n" if len(raw)>1250000 else raw)
    lines=[line for line in raw.splitlines() if line.startswith("NUCLEUS_")]
    counts=Counter(line.split(":",1)[0] for line in lines)
    tags=(
      "NUCLEUS_DOWNSTREAM:","NUCLEUS_APPLICATION_FUNCTION_TYPE:",
      "NUCLEUS_NESTED_RECURSOR_IOTA:","NUCLEUS_DECIDABLE_MAJOR_CHAIN:",
      "NUCLEUS_FIRST_TYPED_CONTINUATION:",
      "NUCLEUS_PROJECTION_FIELD_FAILURE:",
    )
    interesting={tag[:-1]:[s[:1700] for s in lines if s.startswith(tag)][-8:]
                 for tag in tags}
    terminal=[x for x in lines if x.startswith("NUCLEUS_DOWNSTREAM:")][-1:]
    expected=(origins if mode=="origin" else demand)[case]["rc"]
    assert proc.returncode==expected,(case,mode,trace,"UNEXPECTED_VERDICT",proc.returncode,expected,terminal)
    assert proc.returncode in (0,1,2)
    assert not (case.startswith("good/") and proc.returncode==1)
    row={"case":case,"mode":mode,"trace":trace,
         "rc":proc.returncode,"expected":expected,
         "elapsed_seconds":round(duration,3),
         "stderr_length":len(raw),"diagnostic_counts":dict(counts),
         "terminal":terminal,"selected_evidence":interesting}
    print("NUCLEUS_FIRST_MISSING="+json.dumps({"case":case,"mode":mode,
          "trace":trace,"rc":proc.returncode,"terminal":terminal,
          "diagnostics":dict(counts)},ensure_ascii=False),flush=True)
    return row

results=[]
for name in focus:
    results.append(run_case(name,"origin",False))
for name in magma:
    results.append(run_case(name,"origin",True))
# Inspect effect of the pre-existing alternative work scheduler separately.
for name in (magma[0],magma[2]):
    results.append(run_case(name,"demand",True))
# Original malformed indexed proof and forged constructor must remain non-ACCEPT.
for name in ("protected-false-index.ndjson","protected-eta-ctor-alias.ndjson"):
    path=Path("metatron-kernel/tests/fixtures")/name
    with path.open("rb") as f:
        p=subprocess.run([str(binary.resolve())],stdin=f,stdout=subprocess.DEVNULL,
                         stderr=subprocess.PIPE,timeout=40,env=base_env)
    assert p.returncode in (1,2),(name,p.returncode,p.stderr[-300:])
    results.append({"case":str(path),"mode":"origin","trace":False,"rc":p.returncode,
                    "protected_negative":True,
                    "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})

source=[extract_original_source(case) for case in magma]
report={"experiment":"first missing Nucleus obligation, unchanged real source",
        "qualified_source":"heathsanchez/test@ff003e7fad888d39a40cfd2375885fe20e3209fa",
        "source_tree_modified":False,
        "binary_sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),
        "immutable_manifest_sha256":hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "magma_source_declarations":source,"case_results":results,
        "decision":"DIAGNOSTIC_ONLY_NO_SEMANTIC_PROMOTION",
        "independent_full_mathlib_accepted":False,
        "claimed_new_accepted_proof":False}
(out/"first-missing-operation.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print("NUCLEUS_FIRST_MISSING_SUMMARY="+json.dumps({
 "magma_cases":len(magma),
 "magma_countermodel_source":{x["case"]:x["countermodel_declarations"] for x in source},
 "verdicts_unchanged":True,
 "decision":report["decision"]},ensure_ascii=False),flush=True)
