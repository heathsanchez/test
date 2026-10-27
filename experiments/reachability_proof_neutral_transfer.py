#!/usr/bin/env python3
"""Strict replay of six source-hashed, officially accepted Reachability exports."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path("/tmp/reach-test")
OUT=Path("/tmp/reach-evidence");OUT.mkdir(parents=True,exist_ok=True)
BIN="metatron-kernel/target/release/metatron-kernel"
PINS={
"path_reachable":"96918fb408e535b34b50780d6b8fcbae51e5340659ec5a782d0cded926eae479",
"path_unreachable":"94936bd2b67b68ba3af0171995db66f5b5ed683b3133297476c129a5571a18b6",
"grid_reachable":"d1bff6435961f85499f3cc0786190c29356ddc6b8cde6ee7dbb5a832ed1ca989",
"random_reachable":"00bf8e4ec979a1cc5d99776b4dbcb5a23398945a123684fabd1c67515b233d2d",
"dag_reachable":"c2c0bf6baeeed8ef547daf4c1845767034abfa4d1ead62cbc1af9f8663ee6389",
"grid_shortest":"3b2a4f4dcad347f69501fc867ba648523e0c6c5900f2e80725dc6536a32ce023"}
ledger=json.loads(Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json").read_text())
report={"qualification":"UNKNOWN","rows":[],"source_commit":os.getenv("GITHUB_SHA"),"scope":"six exact historical official-ACCEPT whole exports; modes only"}
try:
  for name,h in PINS.items():
    path=ROOT/(name+".ndjson")
    data=path.read_bytes()
    assert hashlib.sha256(data).hexdigest()==h,(name,"SHA mismatch")
    assert json.loads(data.splitlines()[0])["meta"]["format"]["version"]=="3.1.0"
    entry={"name":name,"sha256":h,"modes":{}}
    for mode in ("original","historical-proof-neutral","origin-proof-neutral","origin-quotient-plus-historical"):
      env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
      if mode.startswith("origin"):
        env.update({"NUCLEUS_EXPERIMENTAL_"+f:"1" for f in ledger["origin_flags"]})
      if "proof-neutral" in mode or "historical" in mode:
        env["NUCLEUS_EXPERIMENTAL_EXACT_PROOF_NEUTRALS"]="1"
        env["NUCLEUS_TRACE_EXACT_PROOF_NEUTRALS"]="1"
      if "quotient" in mode or "historical" in mode:
        env["NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA"]="1"
        env["NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL"]="1"
      env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
      with path.open("rb") as inp:
        p=subprocess.run([BIN],stdin=inp,capture_output=True,timeout=180,env=env)
      entry["modes"][mode]={"rc":p.returncode,"stderr_tail":p.stderr.decode(errors="replace")[-1250:]}
      assert p.returncode in (0,2),("wrong REJECT or crash",name,mode,p.returncode)
    print(name,json.dumps({m:(v["rc"],v["stderr_tail"][-170:]) for m,v in entry["modes"].items()}),flush=True)
    report["rows"].append(entry)
  report["qualification"]="WARRANTED_BOUNDED_SIX_VERDICTS_AND_FIRST_OBSTRUCTIONS"
  rc=0
except Exception as e:
  report["error"]=repr(e);rc=1
finally:
  (OUT/"six-gated-verdicts.json").write_text(json.dumps(report,indent=2)+"\n")
  print("FINAL",report["qualification"],flush=True)
sys.exit(rc)
