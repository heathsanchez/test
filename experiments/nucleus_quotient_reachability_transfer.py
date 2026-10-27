#!/usr/bin/env python3
"""Independent source-pinned six-Reachability-export Nucleus transfer gate."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

EXPORT = Path("/tmp/reachability-inputs")
EVIDENCE = Path("/tmp/reachability-evidence")
CHECKER = Path("metatron-kernel/target/release/metatron-kernel")
OFFICIAL = Path("/tmp/arena-reference/checkers/official/.lake/build/bin/kernel")
DECLS = {
    "path_reachable":"96918fb408e535b34b50780d6b8fcbae51e5340659ec5a782d0cded926eae479",
    "path_unreachable":"94936bd2b67b68ba3af0171995db66f5b5ed683b3133297476c129a5571a18b6",
    "grid_reachable":"d1bff6435961f85499f3cc0786190c29356ddc6b8cde6ee7dbb5a832ed1ca989",
    "random_reachable":"00bf8e4ec979a1cc5d99776b4dbcb5a23398945a123684fabd1c67515b233d2d",
    "dag_reachable":"c2c0bf6baeeed8ef547daf4c1845767034abfa4d1ead62cbc1af9f8663ee6389",
    "grid_shortest":"3b2a4f4dcad347f69501fc867ba648523e0c6c5900f2e80725dc6536a32ce023",
}
LEDGER = Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
EVIDENCE.mkdir(parents=True, exist_ok=True)
report={"status":"UNKNOWN", "rows":[], "reach_sha":"d822b1c70b4a6ec858b54ee51f12b0cb30628982",
        "exporter_sha":"076e8e57707e813375e8f9da8bf989799ace9680",
        "source_commit":os.getenv("GITHUB_SHA"),"modes":{}}

def run(exe,path,env,timeout=180):
    now=time.monotonic()
    try:
        with path.open("rb") as inp:
            r=subprocess.run([str(exe),str(path)] if exe==OFFICIAL else [str(exe)],
                             stdin=None if exe==OFFICIAL else inp,
                             env=env,capture_output=True,timeout=timeout)
        return {"exit":r.returncode,"duration_seconds":round(time.monotonic()-now,3),
                "stdout_tail":r.stdout.decode(errors="replace")[-600:],
                "stderr_tail":r.stderr.decode(errors="replace")[-2000:]}
    except subprocess.TimeoutExpired:
        return {"exit":124,"duration_seconds":round(time.monotonic()-now,3),
                "stderr_tail":"TIMEOUT"}

try:
    assert CHECKER.exists() and OFFICIAL.exists()
    pins=json.loads(LEDGER.read_text())
    raw={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    modes={"default":dict(raw),"origin":dict(raw)}
    modes["origin"].update({"NUCLEUS_EXPERIMENTAL_"+flag:"1" for flag in pins["origin_flags"]})
    for env in modes.values():
        env["NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA"]="1"
        env["NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL"]="1"
        env["NUCLEUS_EXPERIMENTAL_NEUTRAL_PAIR_PROOF_IRREL"]="1"
        env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
    for name,sha in DECLS.items():
        source=EXPORT/(name+".ndjson")
        assert source.is_file()
        content=source.read_bytes()
        assert hashlib.sha256(content).hexdigest()==sha,("upstream source drift",name)
        meta=json.loads(content.split(b"\n",1)[0])["meta"]
        assert meta["format"]["version"]=="3.1.0",meta
        assert meta["lean"]["version"]=="4.34.1",meta
        official=run(OFFICIAL,source,raw,180)
        assert official["exit"]==0,("official Lean rejected valid export",name,official)
        verdicts={mode:run(CHECKER,source,env,180) for mode,env in modes.items()}
        record={"name":name,"sha256":sha,"bytes":len(content),
                "official":official,"candidate":verdicts}
        report["rows"].append(record)
        print(json.dumps({k:record[k] for k in ("name","sha256","bytes")},
                         separators=(",",":")),json.dumps({
                             "official":official["exit"],
                             "default":verdicts["default"]["exit"],
                             "origin":verdicts["origin"]["exit"]}),flush=True)
        assert all(v["exit"] in (0,2) for v in verdicts.values()),(
            "incorrect REJECT, crash or timeout on authentic valid proof",name,verdicts)
    for mode in modes:
        accepted=[r["name"] for r in report["rows"] if r["candidate"][mode]["exit"]==0]
        report["modes"][mode]={"accepted":accepted,"accepted_count":len(accepted),
                              "unknown_count":6-len(accepted)}
    report["status"]="WARRANTED_BOUNDED_SIX_SOURCE_HASHES_REFERENCE_AND_CANDIDATE_REPLAY"
    status=0
except Exception as error:
    report["error"]=repr(error)
    status=1
finally:
    (EVIDENCE/"six-reachability-report.json").write_text(
        json.dumps(report,indent=2)+"\n")
    print("FINAL",report["status"],json.dumps(report["modes"]),flush=True)
sys.exit(status)
