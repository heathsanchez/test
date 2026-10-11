#!/usr/bin/env python3
"""Protected three-arm Nucleus semantic and cost qualification.

EXACT: Nucleus frozen196 11272848230 at Arena b1d6e91, with two protected
semantic negative controls. A locally successful warrant is NOT a Lean proof
certificate, nor a full Mathlib/Arena performance qualification.
"""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

sys.path.insert(0, ".github/scripts")
from nucleus_succle_separator import extract, false_index

OUT = Path("/tmp/nucleus-context-evidence")
ROOT = Path("/tmp/arena-tests")
BASE = {
    "NUCLEUS_EXPERIMENTAL_RELEVANCE":"1",
    "NUCLEUS_EXPERIMENTAL_CONTEXT_BINDER":"1",
    "NUCLEUS_EXPERIMENTAL_TYPED_LINEAGE":"1",
    "NUCLEUS_EXPERIMENTAL_SUBSTITUTION_RECLOSURE":"1",
    "NUCLEUS_EXPERIMENTAL_TYPED_VALUE_NORMALIZATION":"1",
}
ARMS = {
    "original":("/tmp/nucleus-original",{}),
    "field_application":("/tmp/nucleus-context",{
        "NUCLEUS_EXPERIMENTAL_CERTIFIED_FIELD_APPLICATION":"1",
    }),
    "proof_irrelevance":("/tmp/nucleus-context",{
        "NUCLEUS_EXPERIMENTAL_CERTIFIED_FIELD_APPLICATION":"1",
        "NUCLEUS_EXPERIMENTAL_FIELD_ARG_PROOF_IRREL":"1",
    }),
}
CASES = [
    "init-prelude",
    "perf/grind-ring-5",
    "perf/magma-list-pair-n7",
    "perf/magma-list-deep-n21",
    "perf/magma-list-deep-n36",
    "perf/fueled-chain",
]

def run(binary, source, mode, timeout=180, performance=False, suffix=""):
    env = os.environ.copy()
    env.update(BASE)
    env.update(ARMS[mode][1])
    if performance:
        env["NUCLEUS_TRACE_CONTEXT_MEMO"]="1"
        env["NUCLEUS_TRACE_CAPTURE_SUPPORT"]="1"
        env["NUCLEUS_TRACE_CERTIFIED_FIELD_APPLICATION"]="1"
        env["NUCLEUS_TRACE_FIELD_ARG_PROOF_IRREL"]="1"
    metrics = OUT / ("rusage_"+suffix+".txt")
    cmd = [binary]
    if performance:
        cmd = ["/usr/bin/time","-f","%U %S %M","-o",str(metrics),binary]
    start = time.monotonic()
    with open(source,"rb") as inp:
        p = subprocess.run(cmd,stdin=inp,stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE,env=env,timeout=timeout)
    result = {
        "rc":p.returncode,
        "wall_seconds":round(time.monotonic()-start,4),
        "memo_hits_logged":p.stderr.count(b"NUCLEUS_CONTEXT_MEMO_HIT:"),
        "support_warrants_logged":p.stderr.count(b"NUCLEUS_CAPTURE_SUPPORT_CERT:"),
        "field_app_warrants_logged":p.stderr.count(b"NUCLEUS_FIELD_APP_PROVEN:"),
        "arg_proof_irrel_warrants_logged":p.stderr.count(b"NUCLEUS_FIELD_ARG_PROOF_IRREL:"),
    }
    if performance:
        # GNU time may prepend an exit-status message for UNKNOWN (exit 2).
        # Parse only the final machine-readable three-column measurement.
        measured = metrics.read_text().splitlines()[-1].split()
        assert len(measured) == 3, (str(metrics), measured)
        user, system, rss = measured
        result.update(cpu_seconds=round(float(user)+float(system),4),
                      max_rss_kb=int(rss))
    return result

def qualification():
    fixtures = [
        (bucket+"/"+str(path.relative_to(ROOT/bucket)),path,expected)
        for bucket,expected in (("good",0),("bad",1))
        for path in sorted((ROOT/bucket).rglob("*.ndjson"))
    ]
    assert len(fixtures)==196,len(fixtures)
    rows=[]
    for mode,(binary,_) in ARMS.items():
        def check(item):
            name,path,expected=item
            return dict(name=name,expected=expected,mode=mode,
                        **run(binary,path,mode))
        # Independent cases: no sharing of process/heap state across inputs.
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            group=list(pool.map(check,fixtures))
        rows.extend(group)
        summary = {
            "ACCEPT":sum(r["rc"]==0 for r in group),
            "REJECT":sum(r["rc"]==1 for r in group),
            "UNKNOWN":sum(r["rc"]==2 for r in group),
            "wrong":sum(r["rc"] in (0,1) and r["rc"]!=r["expected"] for r in group),
            "errors":sum(r["rc"] not in (0,1,2) for r in group),
        }
        print("NUCLEUS_CONTEXT_FRONTIER="+json.dumps({"mode":mode,**summary}),flush=True)
        assert summary["wrong"]==summary["errors"]==0,summary
        assert summary["REJECT"]==71,summary
        if mode=="original":
            assert (summary["ACCEPT"],summary["UNKNOWN"])==(118,7),summary

    old={r["name"]:r for r in rows if r["mode"]=="original"}
    changes={}
    for mode in ["field_application","proof_irrelevance"]:
        cand={r["name"]:r for r in rows if r["mode"]==mode}
        diff=[
            {"case":k,"old":r["rc"],"new":cand[k]["rc"]}
            for k,r in old.items() if r["rc"]!=cand[k]["rc"]
        ]
        assert not [x for x in diff if x["old"] in (0,1)],diff
        changes[mode]=diff
        print("NUCLEUS_CONTEXT_VERDICT_DIFF="+json.dumps({"mode":mode,"diff":diff}),flush=True)

    # A passed 196-case replay is NOT a proof that a candidate is sound.
    # Preserve source-specific false-index and structurally malformed recursor.
    positive_init=(ROOT/"good/init-prelude.ndjson").read_bytes()
    falsifier=false_index(extract(positive_init))
    assert hashlib.sha256(falsifier).hexdigest()==(
        "2a090edfcfa2a16191f17a433617aaf045fc9b11cd0e2a93405b705d8a899688")
    controls=[
        ("false-index",falsifier,(1,2)),
        ("nested-unused-param",(ROOT/"bad/bugs/nested-unused-param.ndjson").read_bytes(),(1,)),
    ]
    negatives=[]
    for mode,(binary,extras) in ARMS.items():
        for name,data,allowed in controls:
            p=subprocess.run([binary],input=data,stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,timeout=90,env=os.environ|BASE|extras)
            record={"mode":mode,"case":name,"rc":p.returncode,
                    "sha256":hashlib.sha256(data).hexdigest()}
            print("NUCLEUS_PROTECTED_NEGATIVE="+json.dumps(record),flush=True)
            assert p.returncode in allowed,record
            negatives.append(record)
    frontiers={
        mode:{
            "ACCEPT":sum(r["rc"]==0 for r in rows if r["mode"]==mode),
            "REJECT":sum(r["rc"]==1 for r in rows if r["mode"]==mode),
            "UNKNOWN":sum(r["rc"]==2 for r in rows if r["mode"]==mode)
        } for mode in ARMS
    }
    result={
        "source":os.environ.get("GITHUB_SHA"),
        "frozen_arena":os.environ.get("ARENA_SHA"),
        "frozen_artifact":os.environ.get("ARENA_ARTIFACT"),
        "frontiers":frontiers,"changes":changes,
        "protected_controls":negatives,
        "new_complete_accept":max(frontiers[mode]["ACCEPT"] for mode in ("field_application","proof_irrelevance"))>118,
        "official_arena_status":"UNKNOWN",
        "mathlib_status":"UNKNOWN",
        "independent_certificate_replay":"UNIMPLEMENTED",
    }
    (OUT/"protected-rows.json").write_text(json.dumps(rows,indent=2)+"\n")
    (OUT/"protected-summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("NUCLEUS_CONTEXT_PROMOTION="+json.dumps(result),flush=True)

def performance():
    rows=[]
    arms=list(ARMS.items())
    for case in CASES:
        p=ROOT/"good"/(case+".ndjson")
        for trial in range(2):
            order=arms if trial%2==0 else list(reversed(arms))
            for mode,(binary,_) in order:
                item=dict(case=case,mode=mode,repetition=trial,
                    **run(binary,p,mode,performance=True,
                          suffix=case.replace("/","_")+"_"+mode+"_"+str(trial)))
                print("NUCLEUS_CONTEXT_COST="+json.dumps(item),flush=True)
                assert item["rc"] in (0,2),item
                rows.append(item)
    totals={
        mode:{
            "cpu_seconds":round(sum(x["cpu_seconds"] for x in rows if x["mode"]==mode),4),
            "wall_seconds":round(sum(x["wall_seconds"] for x in rows if x["mode"]==mode),4),
            "peak_rss_kb":max(x["max_rss_kb"] for x in rows if x["mode"]==mode),
            "logged_memo_hits_max96_per_process":sum(x["memo_hits_logged"] for x in rows if x["mode"]==mode),
            "logged_support_warrants_max96_per_process":sum(x["support_warrants_logged"] for x in rows if x["mode"]==mode),
            "logged_field_app_warrants_max96_per_process":sum(x["field_app_warrants_logged"] for x in rows if x["mode"]==mode),
            "logged_proof_irrel_warrants_max96_per_process":sum(x["arg_proof_irrel_warrants_logged"] for x in rows if x["mode"]==mode),
        }
        for mode in ARMS
    }
    (OUT/"performance-rows.json").write_text(json.dumps(rows,indent=2)+"\n")
    (OUT/"performance-summary.json").write_text(json.dumps({
        "source":os.environ.get("GITHUB_SHA"),
        "qualification":"six frozen cases, two repetitions each",
        "not_measured":"retired instructions, full Mathlib, official score",
        "totals":totals},indent=2)+"\n")
    print("NUCLEUS_CONTEXT_COST_SUMMARY="+json.dumps(totals),flush=True)

if __name__=="__main__":
    OUT.mkdir(parents=True,exist_ok=True)
    if sys.argv[1]=="qualification":
        qualification()
    elif sys.argv[1]=="performance":
        performance()
    else:
        raise SystemExit("usage: gate.py qualification|performance")
