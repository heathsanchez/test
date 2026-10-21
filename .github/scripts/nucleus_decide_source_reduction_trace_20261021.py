#!/usr/bin/env python3
"""Observe original Lean finite-decision proof reduction in Nucleus, unchanged source.

Inputs are the byte-pinned original source subproofs separately validated by
the distinct public reference checker. A valid Eq.refl Bool.true of the
original decide=true proposition is UNKNOWN in Nucleus. Find where it stops:
opaque/neutral head mismatch, incomplete recursor major, or source delta.

No semantic source code changes or case-specific acceptance rules.
"""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

if len(sys.argv)!=4:
    raise SystemExit("usage: trace.py MICRO_SOURCE_DIR NUCLEUS_BINARY EVIDENCE_DIR")
root,binary,out=map(Path,sys.argv[1:])
out.mkdir(parents=True,exist_ok=True)
expected={
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
for f in flags: base_env["NUCLEUS_EXPERIMENTAL_"+f]="1"
base_env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
trial_flags=(
 "NUCLEUS_TRACE_NEUTRAL_HEADS",
 "NUCLEUS_TRACE_DECIDABLE_MAJOR_CHAIN",
 "NUCLEUS_TRACE_NESTED_RECURSOR_IOTA_FAILURE",
 "NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE",
 "NUCLEUS_TRACE_LAZY_DELTA",
 "NUCLEUS_TRACE_LITERAL_CONVERSION",
 "NUCLEUS_TRACE_DEPENDENCY_GAP",
 "NUCLEUS_TRACE_SOURCE_TYPE_RECOVERY",
 "NUCLEUS_TRACE_NAT_IOTA",
)
categories=(
 "NUCLEUS_DOWNSTREAM:","NUCLEUS_NEUTRAL_HEAD_MISMATCH:",
 "NUCLEUS_FIN_LOCAL_PAIR:","NUCLEUS_DECIDABLE_MAJOR_CHAIN:",
 "NUCLEUS_NESTED_REPLAY_FAILURE:","NUCLEUS_APPLICATION_FUNCTION_TYPE:",
 "NUCLEUS_LAZY_HEAD_DELTA:","NUCLEUS_LITERAL_CONVERSION:",
 "NUCLEUS_DEPENDENCY_GAP:","NUCLEUS_SOURCE_TYPE_RECOVERY:",
 "NUCLEUS_NAT_IOTA:",
)
results=[]
for filename,digest in expected.items():
    case=root/filename
    assert case.is_file(),filename
    assert hashlib.sha256(case.read_bytes()).hexdigest()==digest,("INVALID_SOURCE",filename)
    names={}
    with case.open("r") as f:
        for raw in f:
            obj=json.loads(raw)
            if "in" in obj:names[obj["in"]]=obj
    def full_name(i:int):
        if i==0:return ""
        obj=names.get(i)
        if obj is None:return f"NameId#{i}"
        data=obj.get("str") or obj.get("num")
        if not isinstance(data,dict):return f"NameId#{i}"
        parent=data.get("pre",0)
        return (full_name(parent)+"." if parent else "")+str(data.get("str",data.get("i","")))
    for mode in (("origin","demand") if "positive" in filename else ("origin",)):
        for trace in (False,True) if "positive" in filename else (False,):
            env=base_env.copy()
            if mode=="demand":env["NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR"]="1"
            if trace:
                for f in trial_flags:env[f]="1"
            with tempfile.TemporaryFile() as stderr:
                with case.open("rb") as src:
                    p=subprocess.run([str(binary.resolve())],stdin=src,stdout=subprocess.DEVNULL,
                      stderr=stderr,timeout=140,env=env)
                stderr.seek(0)
                raw=stderr.read(16_000_000).decode(errors="replace")
            assert p.returncode==2,(filename,mode,trace,p.returncode,raw[-400:])
            lines=raw.splitlines()
            count=collections.Counter(x.split(":",1)[0] for x in lines if x.startswith("NUCLEUS_"))
            name_id=re.compile(r"NameId\((\d+)\)")
            def label(x):
                s=x[:5000]
                return name_id.sub(lambda m: f"NameId({m.group(1)}:{full_name(int(m.group(1)))})",s)
            items={}
            for prefix in categories:
                subset=[x for x in lines if x.startswith(prefix)]
                items[prefix[:-1]]={
                    "count":len(subset),
                    "first":[label(x) for x in subset[:3]],
                    "last":[label(x) for x in subset[-15:]],
                }
            row={"input":filename,"sha256":digest,"mode":mode,"trace":trace,
                 "rc":p.returncode,"log_prefix_bytes":len(raw),"counts":dict(count),"events":items}
            results.append(row)
            print("NUCLEUS_DECIDE_SOURCE_TRACE="+json.dumps({
                 "input":filename,"mode":mode,"trace":trace,"rc":p.returncode,
                 "counts":{k:v for k,v in count.items() if v>0},
                 "last_neutral":items["NUCLEUS_NEUTRAL_HEAD_MISMATCH"]["last"][-2:],
                 "last_major":items["NUCLEUS_NESTED_REPLAY_FAILURE"]["last"][-2:],
                 "terminal":items["NUCLEUS_DOWNSTREAM"]["last"][-1:],
            },ensure_ascii=False),flush=True)
            # Archive bounded excerpts only; preserve all computed category
            # observations in the machine-readable report.
assert all(x["rc"]==2 for x in results)
report={"source_sha":"ff003e7fad888d39a40cfd2375885fe20e3209fa",
        "verified_reference_positive":"ACCEPT, distinct checker and exact original source",
        "verified_reference_negative":"REJECT, changed only final expected Boolean",
        "checker_source_modified":False,
        "proofs_accepted":0,
        "rows":results,
        "decision":"DIAGNOSTIC_FIRST_CAUSE_NO_SEMANTIC_PROMOTION"}
(out/"decide-source-reduction-diagnostic.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print("NUCLEUS_DECIDE_SOURCE_DECISION="+json.dumps({
 "rows":len(results),"verified_byte_sources":len(expected),
 "decision":report["decision"]}),flush=True)
