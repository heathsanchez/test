#!/usr/bin/env python3
"""Extract and source-check first List.Perm.recOnSwap' original proof prefix."""
import hashlib,json,os,pathlib,subprocess,sys
Path=pathlib.Path
ROOT=Path("/tmp/recOnSwap")
E=ROOT/"evidence";E.mkdir(exist_ok=True,parents=True)
source=ROOT/"path_reachable.ndjson"
PIN="96918fb408e535b34b50780d6b8fcbae51e5340659ec5a782d0cded926eae479"
PREFIX="8ed3003a048e7ef131d068d9cd29c9814c962a29a5ed80c66868289f4c55e156"
TARGET="List.Perm.recOnSwap'"
report={"status":"UNKNOWN","source_sha256":PIN,"prefix_sha256":PREFIX,"results":{}}
def digest(b):return hashlib.sha256(b).hexdigest()
def run(binary,p,env,reference=False):
    try:
        with p.open("rb") as f:
            result=subprocess.run([str(binary),str(p)] if reference else [str(binary)],
                stdin=None if reference else f,
                capture_output=True,env=env,timeout=180)
        return {"exit":result.returncode,
                "stderr_tail":result.stderr.decode(errors="replace")[-4000:],
                "stdout_tail":result.stdout.decode(errors="replace")[-300:]}
    except subprocess.TimeoutExpired:
        return {"exit":124,"stderr_tail":"TIMEOUT"}
try:
    data=source.read_bytes()
    assert digest(data)==PIN
    names={0:""};end=None;thm=None
    lines=data.splitlines(keepends=True)
    for i,line in enumerate(lines):
        o=json.loads(line)
        if "in" in o:
            obj=o.get("str") or o.get("num")
            if obj:
                pre=obj["pre"]
                assert pre in names
                names[o["in"]]=names[pre]+("." if pre else "")+str(obj.get("str",obj.get("i")))
        if "thm" in o and names.get(o["thm"]["name"])==TARGET:
            assert end is None, "nonunique target"
            end=i+1
            thm=o["thm"]
    assert end==7872,(end,"historical source target shifted")
    prefix=b"".join(lines[:end])
    assert digest(prefix)==PREFIX
    path=ROOT/"recOnSwap-exact.ndjson"
    path.write_bytes(prefix)
    assert json.loads(lines[0])["meta"]["format"]["version"]=="3.1.0"
    official=Path("/tmp/arena-reference/checkers/official/.lake/build/bin/kernel")
    nucleus=Path("metatron-kernel/target/release/metatron-kernel")
    ledger=json.loads(Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json").read_text())
    base={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    report["target"]={"name":TARGET,"line":end,"bytes":len(prefix),"theorem":thm}
    ref=run(official,path,base,True)
    report["results"]["official"]=ref
    assert ref["exit"]==0,("original official Lean rejected prefix",ref)
    for mode in ("default","origin","quotient-proof","origin-quotient-proof"):
        env=dict(base)
        if mode in ("origin","origin-quotient-proof"):
            env.update({"NUCLEUS_EXPERIMENTAL_"+flag:"1" for flag in ledger["origin_flags"]})
        if "quotient-proof" in mode:
            env["NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA"]="1"
            env["NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL"]="1"
        env["NUCLEUS_TRACE_DOWNSTREAM"]="1"
        env["NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE"]="1"
        env["NUCLEUS_TRACE_VALUE_MISMATCH"]="1"
        env["NUCLEUS_TRACE_NEUTRAL_HEADS"]="1"
        result=run(nucleus,path,env)
        report["results"][mode]=result
        print(mode,result["exit"],result["stderr_tail"][-900:],flush=True)
        assert result["exit"] in (0,2),("valid proof REJECT/error",mode,result)
    report["status"]="WARRANTED_BOUND_PREFIX_OFFICIAL_ACCEPT"
    return_code=0
except Exception as ex:
    report["error"]=repr(ex)
    return_code=1
finally:
    (E/"recOnSwap-prefix-verdicts.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],
                      "exits":{k:v["exit"] for k,v in report["results"].items()}}),flush=True)
sys.exit(return_code)
