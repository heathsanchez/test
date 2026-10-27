#!/usr/bin/env python3
"""Source-hashed Reachability List.getElem?_eq_getElem exact prefix sensitivity.

An increase to bounded diagnostic fuel is NEVER itself an authorization to
admit a proof or to promote a semantic rule. The independent official Lean
kernel must accept the unchanged prefix before candidate results count.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

OUT = Path("/tmp/nucleus-getelem/evidence")
ZIP = Path("/tmp/nucleus-getelem/archive/inputs.zip")
PREFIX = OUT / "List.getElemQ_eq_getElem-exact-prefix.ndjson"
NAMES = {0:""}
NAME = "List.getElem?_eq_getElem"
SOURCE_SHA = "96918fb408e535b34b50780d6b8fcbae51e5340659ec5a782d0cded926eae479"
PREFIX_SHA = "fa21f2a48d84f66aeffc252e988d370634db1ad0706ebc717efdd7d5d379b71a"
LEAN_SHA = "5045d0056413266e57c625dcd7c365b10e377c52"
CHECKER = Path("metatron-kernel/target/release/metatron-kernel")
OFFICIAL = Path("/tmp/arena-reference/checkers/official/.lake/build/bin/kernel")
OUT.mkdir(parents=True,exist_ok=True)
report={"status":"UNKNOWN","verdicts":{},"source_sha256":SOURCE_SHA,"prefix_sha256":PREFIX_SHA}

def sha(bs):
    return hashlib.sha256(bs).hexdigest()

def run(exe, path, env, args):
    start=time.monotonic()
    try:
        with path.open("rb") as stream:
            p=subprocess.run([str(exe),*args],stdin=stream if not args else None,
                             capture_output=True,env=env,timeout=150)
        stderr=p.stderr.decode(errors="replace")
        first_function_type=next((x for x in stderr.splitlines()
            if x.startswith("NUCLEUS_APPLICATION_FUNCTION_TYPE:")),None)
        return {"exit":p.returncode,"seconds":round(time.monotonic()-start,3),
                "stderr_tail":stderr[-2200:],
                "first_function_type":first_function_type,
                "stdout_tail":p.stdout.decode(errors="replace")[-250:]}
    except subprocess.TimeoutExpired:
        return {"exit":124,"seconds":round(time.monotonic()-start,3),"error":"timeout"}

try:
    assert ZIP.is_file() and OFFICIAL.is_file() and CHECKER.is_file()
    with zipfile.ZipFile(ZIP) as archive:
        source=archive.read("path_reachable.ndjson")
    assert sha(source)==SOURCE_SHA, "source bytes not historically authorized"
    whole_source = ZIP.parent / "path_reachable-original.ndjson"
    whole_source.write_bytes(source)
    lines=source.splitlines(keepends=True)
    assert json.loads(lines[0])["meta"]["lean"]["githash"]==LEAN_SHA
    match=[]
    for i,line in enumerate(lines):
        o=json.loads(line)
        if "in" in o:
            t=o.get("str") or o.get("num")
            if t:
                parent=t["pre"]
                assert parent in NAMES,("name table lineage missing",i,parent)
                NAMES[o["in"]]=NAMES[parent]+("." if parent else "")+str(t.get("str",t.get("i")))
        if "thm" in o and NAMES.get(o["thm"]["name"])==NAME:
            match.append((i,o["thm"]))
    assert len(match)==1,("target name missing/duplicate",match)
    idx,record=match[0]
    assert idx+1==95635,("declaration moved",idx+1)
    PREFIX.write_bytes(b"".join(lines[:idx+1]))
    assert sha(PREFIX.read_bytes())==PREFIX_SHA, "unexpected prefix bytes"
    report["source"]={"name":NAME,"record_line":idx+1,"bytes":PREFIX.stat().st_size,
                      "theorem_type_expr":record["type"],"theorem_value_expr":record["value"]}
    empty={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    official=run(OFFICIAL,PREFIX,empty,[str(PREFIX)])
    report["official"]=official
    print("official prefix",official,flush=True)
    assert official["exit"]==0,("reference kernel rejected exact prefix",official)
    full_official = run(OFFICIAL,whole_source,empty,[str(whole_source)])
    report["official_whole"] = full_official
    assert full_official["exit"]==0,("reference kernel rejected original complete input",full_official)
    print("official whole",full_official,flush=True)

    ledger=json.loads(Path(
      "metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json"
    ).read_text())
    origin=dict(empty)
    origin.update({"NUCLEUS_EXPERIMENTAL_"+flag:"1" for flag in ledger["origin_flags"]})
    origin.update({
        "NUCLEUS_EXPERIMENTAL_CERTIFIED_QUOT_IOTA":"1",
        "NUCLEUS_EXPERIMENTAL_SOURCE_PROOF_IRREL":"1",
        "NUCLEUS_EXPERIMENTAL_NEUTRAL_PAIR_PROOF_IRREL":"1",
        "NUCLEUS_TRACE_DOWNSTREAM":"1",
    })
    budgets=(65536,524288) if os.environ.get("NUCLEUS_DIAG_TRACE_COMPARISON")=="1" else (
        (65536,) if os.environ.get("NUCLEUS_DIAG_ONE_BUDGET")=="1" else (65536,131072,262144,524288)
    )
    for budget in budgets:
        env=dict(origin)
        env["NUCLEUS_DIAG_JUDGMENT_STEPS"]=str(budget)
        if os.environ.get("NUCLEUS_DIAG_TRACE_COMPARISON")=="1":
            env["NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE"]="1"
        if budget == 65536:
            prefix_recheck=run(CHECKER,PREFIX,env,[])
            report["verdicts"][str(budget)]=prefix_recheck
            assert prefix_recheck["exit"] in (0,2),(
                "invalid REJECT/ERROR on official-accepted prefix",budget,prefix_recheck)
        result=run(CHECKER,whole_source,env,[])
        report.setdefault("whole_verdicts",{})[str(budget)]=result
        print("whole budget",budget,"verdict",result["exit"],
              "seconds",result["seconds"],"tail",result.get("stderr_tail","")[-650:],flush=True)
        assert result["exit"] in (0,2),("invalid REJECT/ERROR on official-accepted complete export",budget,result)
    report["status"]="WARRANTED_BOUNDED_PREFIX_AND_WHOLE_BUDGET_DIAGNOSTIC"
    rc=0
except Exception as error:
    report["error"]=repr(error)
    rc=1
finally:
    (OUT/"getelem-prefix-budget.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("FINAL",report["status"],flush=True)
sys.exit(rc)
