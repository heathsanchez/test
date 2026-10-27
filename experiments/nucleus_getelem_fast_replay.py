#!/usr/bin/env python3
"""Fast, source-hash-gated Nucleus Eq.ndrec transfer experiment.

The authentic NDJSON is reconstructed by reversing ONE independently verified
receiver mutation in retained Arena evidence. Exact authentic SHA is required.
No approval derives from expected proof identity or from this reconstruction:
official Lean had separately ACCEPTed the authentic input in archived run
40573804820; this checks Nucleus's new candidate only.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path("/tmp/nucleus-getelem-fast")
REPORT=ROOT/"evidence"
REPORT.mkdir(parents=True,exist_ok=True)
OFFICIAL_RUN="https://github.com/heathsanchez/test/actions/runs/40573804820"
DIGESTS={
    "authentic":"fa21f2a48d84f66aeffc252e988d370634db1ad0706ebc717efdd7d5d379b71a",
    "receiver-forged":"4883556bc4956db44688d560a472940837a3defa40cdad77d3b6caeda7773332",
    "index-forged":"3653b131393012eb60b6b749ebc3c652b79a3b7601981cbacaff0106919e9263",
}
report={"status":"UNKNOWN","official_reference_run":OFFICIAL_RUN,"input_hashes":DIGESTS,
        "source_commit":os.environ.get("GITHUB_SHA"),"modes":{}}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def run(input_path,env):
    with input_path.open("rb") as inp:
        r=subprocess.run(["metatron-kernel/target/release/metatron-kernel"],
                         stdin=inp,capture_output=True,timeout=150,env=env)
    return {"exit":r.returncode,"stderr_tail":r.stderr.decode(errors="replace")[-4200:]}
try:
    forged=ROOT/"forged-dependent-motive.ndjson"
    wrong=ROOT/"forged-dependent-index.ndjson"
    assert sha(forged.read_bytes())==DIGESTS["receiver-forged"]
    assert sha(wrong.read_bytes())==DIGESTS["index-forged"]
    lines=forged.read_bytes().splitlines(keepends=True)
    hits=[]
    for i,line in enumerate(lines):
        if b'"ie":84272' in line:
            node=json.loads(line)
            if node.get("ie")==84272:hits.append((i,node))
    assert len(hits)==1
    i,node=hits[0]
    assert node["app"]=={"arg":84153,"fn":84260}
    node["app"]["arg"]=84271
    lines[i]=(json.dumps(node,separators=(",",":"),ensure_ascii=False)+"\n").encode()
    original=b"".join(lines)
    assert len(original)==4928625 and sha(original)==DIGESTS["authentic"]
    assert json.loads(original.splitlines()[0])["meta"]["format"]["version"]=="3.1.0"
    auth=ROOT/"authentic.ndjson"
    auth.write_bytes(original)
    ledger=json.loads(Path(
        "metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json"
    ).read_text())
    clean={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    modes={
        "default":dict(clean),
        "combined-origin":dict(clean),
        "budget-split":dict(clean),
        "typed-receiver":dict(clean),
    }
    for mode in ("combined-origin","budget-split","typed-receiver"):
        modes[mode].update({"NUCLEUS_EXPERIMENTAL_"+x:"1" for x in ledger["origin_flags"]})
        modes[mode]["NUCLEUS_EXPERIMENTAL_EXACT_PROOF_NEUTRALS"]="1"
        modes[mode]["NUCLEUS_TRACE_DOWNSTREAM"]="1"
        modes[mode]["NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA"]="1"
        modes[mode]["NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL"]="1"
    for mode in ("budget-split","typed-receiver"):
        modes[mode]["NUCLEUS_EXPERIMENTAL_RECEIVER_BUDGET_SPLIT"]="1"
    modes["typed-receiver"]["NUCLEUS_EXPERIMENTAL_TYPED_RECEIVER_ARGUMENT"]="1"
    modes["typed-receiver"]["NUCLEUS_TRACE_TYPED_RECEIVER_SOURCE_FAILURE"]="1"
    for mode,env in modes.items():
        verdicts={
            "authentic":run(auth,env),
            "receiver-forged":run(forged,env),
            "index-forged":run(wrong,env),
        }
        report["modes"][mode]=verdicts
        assert verdicts["authentic"]["exit"] in (0,2),(
            "official-valid proof incorrectly rejected or errored",mode,verdicts)
        for label in ("receiver-forged","index-forged"):
            assert verdicts[label]["exit"] in (1,2),(
                "forged dependent evidence incorrectly accepted or errored",mode,label,verdicts)
        print(mode,{k:v["exit"] for k,v in verdicts.items()},flush=True)
    report["status"]="WARRANTED_BOUNDED_PINNED_FAST_REPLAY"
    status=0
except Exception as e:
    report["error"]=repr(e)
    status=1
finally:
    (REPORT/"fast-replay.json").write_text(json.dumps(report,indent=2)+"\n")
    print("FINAL",report["status"],flush=True)
sys.exit(status)
