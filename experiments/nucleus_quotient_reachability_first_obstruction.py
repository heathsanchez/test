#!/usr/bin/env python3
"""Byte-pinned first-obstruction differential against protected Nucleus baseline."""
import hashlib,json,os,pathlib,subprocess,sys
P=pathlib.Path
INPUT=P("/tmp/reachability-originals")
OUT=P("/tmp/reachability-first-obstruction")
OUT.mkdir(exist_ok=True,parents=True)
EXPECTED={
"path_reachable":"96918fb408e535b34b50780d6b8fcbae51e5340659ec5a782d0cded926eae479",
"path_unreachable":"94936bd2b67b68ba3af0171995db66f5b5ed683b3133297476c129a5571a18b6",
"grid_reachable":"d1bff6435961f85499f3cc0786190c29356ddc6b8cde6ee7dbb5a832ed1ca989",
"random_reachable":"00bf8e4ec979a1cc5d99776b4dbcb5a23398945a123684fabd1c67515b233d2d",
"dag_reachable":"c2c0bf6baeeed8ef547daf4c1845767034abfa4d1ead62cbc1af9f8663ee6389",
"grid_shortest":"3b2a4f4dcad347f69501fc867ba648523e0c6c5900f2e80725dc6536a32ce023"}
# Fixed typo-sensitive hashes are authoritative; reject any drift.
EXPECTED["dag_reachable"]="c2c0bf6baeeed8ef547daf4c1845767034abfa4d1ead62cbc1af9f8663ee6389"
LEDGER=json.loads(P("baseline/metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json").read_text())
CAND="/tmp/nucleus-current"
BASE="/tmp/nucleus-protected"
M={"protected-default":(BASE,[]),"protected-origin":(BASE,LEDGER["origin_flags"]),
   "current-default":(CAND,[]),"current-origin":(CAND,LEDGER["origin_flags"])}
R={"status":"UNKNOWN","source_base":"ff003e7fad888d39a40cfd2375885fe20e3209fa","rows":[]}
try:
 for name,expected in EXPECTED.items():
  source=INPUT/(name+".ndjson")
  data=source.read_bytes()
  assert hashlib.sha256(data).hexdigest()==expected,(name,"hash mismatch")
  meta=json.loads(data.split(b"\n",1)[0])["meta"]
  assert meta["format"]["version"]=="3.1.0"
  result={"name":name,"sha256":expected,"variants":{}}
  for mode,(binary,flags) in M.items():
   env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
   env.update({"NUCLEUS_EXPERIMENTAL_"+flag:"1" for flag in flags})
   if binary==CAND:env.update(NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA="1",NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL="1")
   env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
   with source.open("rb") as inp:
    p=subprocess.run([binary],stdin=inp,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=180)
   trace=p.stderr.decode(errors="replace")
   traces=[x for x in trace.splitlines() if x.startswith("NUCLEUS_DOWNSTREAM:")]
   result["variants"][mode]={"exit":p.returncode,"first_obstruction":traces[0] if traces else None}
   assert p.returncode in (0,2),(name,mode,p.returncode)
  R["rows"].append(result)
  print(json.dumps(result),flush=True)
 R["status"]="WARRANTED_SOURCE_HASHED_FOUR_ARM_REACHABILITY_DIFFERENTIAL"
 rc=0
except Exception as e:
 R["error"]=repr(e)
 rc=1
finally:
 (OUT/"first-obstruction.json").write_text(json.dumps(R,indent=2)+"\n")
 print("FINAL",R["status"],flush=True)
sys.exit(rc)
