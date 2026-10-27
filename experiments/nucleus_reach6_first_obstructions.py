#!/usr/bin/env python3
"""Recover the first authentic, source-pinned Reachability obstruction in Nucleus.

This is a diagnostic replay, not a semantic waiver. Original Lean-accepted
proofs must never turn into REJECT/ERROR; failure receipts are retained.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

INPUT = Path("/tmp/reach6/inputs")
OUTPUT = Path("/tmp/reach6/evidence")
BIN = Path("metatron-kernel/target/release/metatron-kernel")
LEDGER = Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
PINS = {
    "path_reachable": "96918fb408e535b34b50780d6b8fcbae51e5340659ec5a782d0cded926eae479",
    "path_unreachable": "94936bd2b67b68ba3af0171995db66f5b5ed683b3133297476c129a5571a18b6",
    "grid_reachable": "d1bff6435961f85499f3cc0786190c29356ddc6b8cde6ee7dbb5a832ed1ca989",
    "random_reachable": "00bf8e4ec979a1cc5d99776b4dbcb5a23398945a123684fabd1c67515b233d2d",
    "dag_reachable": "c2c0bf6baeeed8ef547daf4c1845767034abfa4d1ead62cbc1af9f8663ee6389",
    "grid_shortest": "3b2a4f4dcad347f69501fc867ba648523e0c6c5900f2e80725dc6536a32ce023",
}
OUTPUT.mkdir(parents=True,exist_ok=True)
report={"qualification":"UNKNOWN","inputs":[],"modes":{},"candidate_commit":os.environ.get("GITHUB_SHA")}
try:
    ledger=json.loads(LEDGER.read_text())
    raw={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    modes={"baseline-default":dict(raw),"candidate-origin":dict(raw)}
    modes["candidate-origin"].update({"NUCLEUS_EXPERIMENTAL_"+flag:"1" for flag in ledger["origin_flags"]})
    modes["candidate-origin"].update({
        "NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA":"1",
        "NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL":"1",
        "NUCLEUS_EXPERIMENTAL_NEUTRAL_PAIR_PROOF_IRREL":"1",
    })
    for mode in modes:
        modes[mode].update({
            "NUCLEUS_TRACE_DOWNSTREAM":"1",
            "NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE":"1",
            "NUCLEUS_TRACE_CAPTURED_PI_RECOVERY":"1",
        })
    for name, expected in PINS.items():
        source=INPUT/(name+".ndjson")
        assert source.is_file(),("missing exact original",name)
        actual=hashlib.sha256(source.read_bytes()).hexdigest()
        assert actual==expected,("source drift",name,actual)
        meta=json.loads(source.open("rb").readline())["meta"]
        assert meta["format"]["version"]=="3.1.0",meta
        report["inputs"].append({"case":name,"sha256":actual,"bytes":source.stat().st_size})
    for mode,env in modes.items():
        cases=[]
        for name in PINS:
            source=INPUT/(name+".ndjson")
            try:
                with source.open("rb") as handle:
                    result=subprocess.run([str(BIN)],stdin=handle,env=env,capture_output=True,timeout=240)
                exit_code=result.returncode
                stderr=result.stderr.decode(errors="replace")
            except subprocess.TimeoutExpired as exc:
                exit_code=124
                stderr=(exc.stderr or b"").decode(errors="replace")
            trace=[line for line in stderr.splitlines() if "NUCLEUS_DOWNSTREAM:" in line]
            appendix=[line for line in stderr.splitlines()
                if line.startswith("NUCLEUS_APPLICATION_FUNCTION_TYPE:")
                or line.startswith("NUCLEUS_CAPTURED_PI_RECOVERY:")]
            record={"case":name,"exit":exit_code,"first_downstream":trace[0] if trace else None,
                    "last_downstream":trace[-1] if trace else None,
                    "downstream_count":len(trace),
                    "first_type_obligation":appendix[0][:1500] if appendix else None}
            cases.append(record)
            (OUTPUT/(mode+"-"+name+".stderr.txt")).write_text(stderr[-500000:])
            print(json.dumps({"mode":mode,**record},ensure_ascii=False),flush=True)
            assert exit_code in (0,2),("valid Lean proof incorrectly rejected or errored",mode,name,exit_code)
        report["modes"][mode]=cases
    signatures={}
    for mode,cases in report["modes"].items():
        signatures[mode]={}
        for x in cases:
            reason=(x["first_downstream"] or "<unreported>")
            signatures[mode][reason]=signatures[mode].get(reason,0)+1
    report["shared_first_obstructions"]=signatures
    report["qualification"]="WARRANTED_EXACT_SIX_FIRST_OBSTRUCTION_DIAGNOSTICS"
    rc=0
except Exception as error:
    report["error"]=repr(error)
    rc=1
finally:
    (OUTPUT/"first-obstruction-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("FINAL",report["qualification"],flush=True)
sys.exit(rc)
