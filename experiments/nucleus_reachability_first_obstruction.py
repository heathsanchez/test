#!/usr/bin/env python3
"""First authentic, source-order Reachability obstruction; no repair or promotion.

Pin the six proof bytes before reading. Cut the shortest complete NDJSON stream
through the *original* List.Perm.recOnSwap' declaration; never invent a theorem,
reorder a declaration, or replace dependent premise evidence. Official Lean
acceptance of this exact prefix is mandatory.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys
ROOT=Path("/tmp/reachability-first")
INPUT=ROOT/"inputs"
OUTPUT=ROOT/"evidence"
OUTPUT.mkdir(parents=True,exist_ok=True)
EXPECTED={
"path_reachable.ndjson":"96918fb408e535b34b50780d6b8fcbae51e5340659ec5a782d0cded926eae479",
"grid_shortest.ndjson":"3b2a4f4dcad347f69501fc867ba648523e0c6c5900f2e80725dc6536a32ce023",
}
PIN="List.Perm.recOnSwap'"
CHECKER=Path("metatron-kernel/target/release/metatron-kernel")
REFERENCE=Path("/tmp/arena-reference/checkers/official/.lake/build/bin/kernel")
report={"status":"UNKNOWN","scope":"two authentic source-ordered declaration prefixes; diagnostics only","cases":[]}
def sha(b):return hashlib.sha256(b).hexdigest()
def run(binary,path,env,official=False):
    with path.open("rb") as handle:
        r=subprocess.run([str(binary),str(path)] if official else [str(binary)],
                         stdin=None if official else handle,capture_output=True,env=env,timeout=180)
    return {"exit":r.returncode,"stderr":r.stderr.decode(errors="replace")[-11000:],
            "stdout":r.stdout.decode(errors="replace")[-800:]}
try:
    assert CHECKER.is_file() and REFERENCE.is_file()
    ledger=json.loads(Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json").read_text())
    for name,expected in EXPECTED.items():
        data=(INPUT/name).read_bytes()
        assert sha(data)==expected,(name,"source hash mismatch")
        found=[]
        names={0:""}
        for n,line in enumerate(data.splitlines(keepends=True),1):
            record=json.loads(line)
            if "in" in record:
                val=record.get("str") or record.get("num")
                assert val is not None
                base=val["pre"]
                assert base in names,("unknown name prefix",base)
                names[record["in"]]=names[base]+("." if base else "")+str(val.get("str",val.get("i")))
            if "thm" in record and names.get(record["thm"]["name"])==PIN:
                found.append(n)
        assert len(found)==1,(name,found)
        prefix=b"".join(data.splitlines(keepends=True)[:found[0]])
        p=OUTPUT/(name.replace(".ndjson","-perm-prefix.ndjson"))
        p.write_bytes(prefix)
        meta=json.loads(prefix.split(b"\n",1)[0])["meta"]
        assert meta["format"]["version"]=="3.1.0"
        official=run(REFERENCE,p,os.environ,True)
        assert official["exit"]==0,("official prefix not ACCEPT",name,official)
        test={}
        for mode in ["default","origin","quot-source-proof","origin-quot-source-proof","neutral-pair","origin-neutral-pair","origin-neutral-pair-quot"]:
            env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
            if mode in ("origin","origin-quot-source-proof","origin-neutral-pair","origin-neutral-pair-quot"):
                env.update({"NUCLEUS_EXPERIMENTAL_"+f:"1" for f in ledger["origin_flags"]})
            if "quot-source-proof" in mode:
                env["NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA"]="1"
                env["NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL"]="1"
            if "neutral-pair" in mode:
                env["NUCLEUS_EXPERIMENTAL_NEUTRAL_PAIR_PROOF_IRREL"]="1"
                env["NUCLEUS_TRACE_NEUTRAL_PAIR_PROOF"]="1"
            if mode=="origin-neutral-pair-quot":
                env["NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA"]="1"
                env["NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL"]="1"
            env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
            env["NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE"]="1"
            env["NUCLEUS_TRACE_CAPTURED_PI_RECOVERY"]="1"
            env["NUCLEUS_TRACE_NEUTRAL_HEADS"]="1"
            env["NUCLEUS_TRACE_VALUE_MISMATCH"]="1"
            test[mode]=run(CHECKER,p,env)
            assert test[mode]["exit"] in (0,2),("valid source falsely REJECTED",name,mode,test[mode])
            print(name,mode,test[mode]["exit"],test[mode]["stderr"][-1300:],flush=True)
        report["cases"].append({"name":name,"full_sha256":expected,
                                "record":found[0],"prefix_sha256":sha(prefix),
                                "prefix_bytes":len(prefix),"official":official,"nucleus":test})
    report["status"]="WARRANTED_SOURCE_PINNED_FIRST_OBSTRUCTION_DIAGNOSIS"
    status=0
except Exception as e:
    report["error"]=repr(e)
    status=1
finally:
    (OUTPUT/"first-obstruction.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("FINAL",report["status"],flush=True)
sys.exit(status)
