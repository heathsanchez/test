#!/usr/bin/env python3
"""Experimental getElem budget-reserve Nucleus corpus protection: 196 x three modes.

This experiment preserves the qualified original case-by-case verdict ledger,
retains every unsoundness negative, and requires two independently exported
positive whole proofs (one genuine previously UNKNOWN beta theorem).
No public merge, hardware performance or Mathlib acceptance is implied.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

FROZEN = Path("/tmp/quotient-qualify/frozen")
TARGET = Path("/tmp/quotient-qualify/target")
EVIDENCE = Path("/tmp/quotient-qualify/evidence")
BASELINE = Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
CHECKER = Path("metatron-kernel/target/release/metatron-kernel")
EVIDENCE.mkdir(parents=True, exist_ok=True)
report = {"status":"UNKNOWN", "modes":{}, "heldout":{}, "source_commit":os.environ.get("GITHUB_SHA")}
PROTECTED = Path("metatron-kernel/tests/fixtures")
POSITIVE_SHA = {
    "authentic.ndjson": "da02144b2d6109c86e5067b1e987744c2122820629bc8ece04dfb276f243239b",
    "indirect-beta.ndjson": "50f67b6a84e486407be251043051177e2baf5b8948bf750074a63c8a62ddcbce",
}
NEGATIVE_SHA = "a4425142910417814594d555ccec8ac1b29bbe8d18f12993f20fa1c0253fd692"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(path, env):
    with path.open("rb") as inp:
        proc = subprocess.run([str(CHECKER)], stdin=inp, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=180, env=env)
    return proc.returncode

def mode_env(mode, ledger):
    env = {key:value for key,value in os.environ.items() if not key.startswith("NUCLEUS_")}
    if mode != "default":
        env.update({"NUCLEUS_EXPERIMENTAL_"+flag:"1" for flag in ledger["origin_flags"]})
    if mode == "demand":
        env["NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR"]="1"
    env["NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA"]="1"
    env["NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL"]="1"
    env["NUCLEUS_EXPERIMENTAL_CAPTURED_PI_LOWBUDGET"]="1"
    env["NUCLEUS_EXPERIMENTAL_RECEIVER_BUDGET_RESERVE"]="1"
    env["NUCLEUS_EXPERIMENTAL_NEUTRAL_PAIR_PROOF_IRREL"]="1"
    return env

try:
    ledger = json.loads(BASELINE.read_text())
    for name, expected in {**POSITIVE_SHA, "mutated.ndjson":NEGATIVE_SHA}.items():
        p=TARGET/name
        assert p.is_file() and digest(p)==expected, ("heldout hash mismatch",name)
    source_meta=json.loads((TARGET/"authentic.ndjson").read_text().splitlines()[0])["meta"]
    assert source_meta["format"]["version"]=="3.1.0",source_meta
    assert source_meta["lean"]["githash"]=="5045d0056413266e57c625dcd7c365b10e377c52"
    for mode in ("default","origin","demand"):
        env=mode_env(mode,ledger)
        rows=ledger["modes"][mode]["rows"]
        assert len(rows)==196
        checked=[]; additions=[]
        for n, row in enumerate(rows):
            path=FROZEN/row["case"]
            assert path.is_file() and digest(path)==row["sha256"],row["case"]
            verdict=check(path,env)
            old=row["rc"]
            group="good" if row["case"].startswith("good/") else "bad"
            assert verdict in (0,1,2), ("execution error", mode,row["case"],verdict)
            # Never lose a previously warranted ACCEPT or REJECT. A valid,
            # previously unhandled whole theorem may become ACCEPT.
            if old in (0,1):
                assert verdict==old,("protected regression",mode,row["case"],old,verdict)
            elif old == 2:
                if group=="good":
                    assert verdict in (0,2),("valid incorrectly REJECTED",mode,row["case"],verdict)
                    if verdict==0: additions.append(row["case"])
                else:
                    assert verdict in (1,2),("invalid incorrectly ACCEPTED",mode,row["case"],verdict)
            checked.append({"case":row["case"],"sha256":row["sha256"],"before":old,"after":verdict})
            if n%45==0:
                print(mode,n+1,"/196",flush=True)
        controls={}
        for neg in ("protected-false-index.ndjson","protected-eta-ctor-alias.ndjson"):
            p=PROTECTED/neg
            assert p.is_file()
            v=check(p,env)
            assert v in (1,2),("adversarial ACCEPT or error",mode,neg,v)
            controls[neg]={"exit":v,"sha256":digest(p)}
        held={}
        for target_file in ("authentic.ndjson","indirect-beta.ndjson","mutated.ndjson"):
            v=check(TARGET/target_file,env)
            required=1 if target_file=="mutated.ndjson" else 0
            assert v==required,("held-out mismatch",mode,target_file,v,required)
            held[target_file]={"exit":v,"sha256":digest(TARGET/target_file)}
        report["modes"][mode]={
            "status":"PASS","checked":196,"new_accepts":additions,
            "counts":{"accept":sum(v["after"]==0 for v in checked),
                      "reject":sum(v["after"]==1 for v in checked),
                      "unknown":sum(v["after"]==2 for v in checked)},
            "controls":controls,"heldout":held,"rows":checked,
        }
        print(json.dumps({"mode":mode,"new_accepts":additions,
                          "counts":report["modes"][mode]["counts"]}),flush=True)
    report["status"]="WARRANTED_BOUNDED_GETELEM_RESERVE_588_CORPUS_6_ADVERSARIES_6_POSITIVE_3_FORGED"
    result=0
except Exception as error:
    report["error"]=repr(error)
    result=1
finally:
    (EVIDENCE/"promotion-gate.json").write_text(json.dumps(report,indent=2)+"\n")
    print("FINAL",report["status"],flush=True)
sys.exit(result)
