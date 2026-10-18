#!/usr/bin/env python3
"""First eligible real future for frozen regex-terminal operator family.

Never reselect based on method success. No post-future method edit or self-warrant.
"""
import json
from pathlib import Path
import subprocess
import sys
import time

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as pool
from research.unified_consequence_runtime import g2_regex_terminal_genesis_v1 as acquired
from research.unified_consequence_runtime import g2_cross_source_future_probe_v1 as native_trial

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
FREEZE="c334208685d25c3f1254b77e2e88d0f7efdd7975"
PROTOCOL="32de5bd464208dc14e0f374db31cfaeae72288db"

def frozen_bytes(rev,path):
    return subprocess.check_output(["git","-C",str(ROOT),"show",rev+":"+path],timeout=40)

def preflight():
    p=U+"G2_REGEX_ACQUIRED_OPERATOR_PRE_FUTURE_FREEZE_V1.json"
    raw=(ROOT/p).read_bytes()
    assert raw==frozen_bytes(FREEZE,p),"FUTURE_FREEZE_MODIFIED"
    f=json.loads(raw)
    assert f["G2"]=="UNKNOWN" and len(f["futures_in_order"])==3
    old=f["acquired"]
    assert old["kind"]=="strict_terminal_anchor"
    assert (ROOT/old["code_file"]).read_bytes()==frozen_bytes(old["code_git_commit"],old["code_file"])
    proto=U+"G2_REGEX_BOUNDARY_SOURCE_DISTINCT_V1_FROZEN_PROTOCOL.md"
    assert (ROOT/proto).read_bytes()==frozen_bytes(PROTOCOL,proto)
    return f

def task_from_row(row):
    return {"repo":row["repo"],"pr":row["pr"],
            "base":row["base"],"head":row["head"],
            "production":row["production"],"author_test":row["test"]}

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    report={"schema":"G2_REGEX_TERMINAL_PROSPECTIVE_SOURCE_DISTINCT_FUTURE_V1",
            "status":"UNKNOWN_ENVIRONMENT","G2":"UNKNOWN",
            "Lean":"NOT_EXECUTED","CLC":"NOT_EXECUTED","FLASH":"NOT_EXECUTED",
            "future_roles":[],"acquired_method_changed":False,
            "strong_agent_comparator":"NOT_RUN"}
    st=time.monotonic()
    try:
        freeze=preflight()
        report["freeze_commit"]=FREEZE
        report["acquired_method_git_blob"]=freeze["acquired"]["code_git_blob"]
        selected=None
        for idx,row in enumerate(freeze["futures_in_order"]):
            # Name and role were frozen before any future source was read.
            task=task_from_row(row)
            rec=pool.one(task,idx,out/("future-admission-%02d"%idx))
            report["future_roles"].append({
                "order":idx,"repo":row["repo"],"pr":row["pr"],
                "status":rec["status"],"native":rec.get("native"),
                "protected_nodes":rec.get("protected_nodes"),
                "source_sha256":rec.get("source_sha256")
            })
            c=rec.get("native",{}).get("counts",{})
            eligible=(rec["status"]=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE"
                      and c.get("failures",0)>0 and c.get("errors",1)==0
                      and c.get("skipped",1)==0 and c.get("tests",0)>0
                      and c["tests"]>=len(rec.get("protected_nodes",[])))
            if eligible:
                selected=(task,rec)
                break
        if selected is None:
            report["status"]="UNKNOWN_NO_AUTHENTIC_SOURCE_NATIVE_FAIL_IN_FROZEN_POOL"
            return
        task,rec=selected
        report["selected_future"]={"repo":task["repo"],"pr":task["pr"],
              "base":task["base"],"production":task["production"],
              "head_author_tests_only":task["author_test"],
              "original_source_sha256":rec["source_sha256"],
              "original_native":rec["native"],
              "protected_nodes":rec["protected_nodes"]}
        work=Path(rec["work_dir"]);py=Path(rec["interpreter"])
        prod=work/task["production"]
        original=prod.read_bytes()
        source=original.decode("utf-8")
        assert native_trial.sha(original)==rec["source_sha256"]
        assert native_trial.status_allowed(work,task,False)
        all_candidates=acquired.enumerate_candidates(source)
        new=[{**x,"if_line":x["line"]} for x in all_candidates if x["kind"]=="strict_terminal_anchor"]
        comparator=[{**x,"if_line":x["line"]} for x in all_candidates if x["kind"]=="whole_input_match"]
        report["acquired_candidate_count"]=len(new)
        report["comparator_candidate_count"]=len(comparator)
        original_native=rec["native"]
        assert native_trial.original_fails(original_native)
        # Matched comparator executes first, fixed selection and native budget.
        report["comparison"]=native_trial.trial_arm("whole-input-comparator",comparator,
                         source,original,work,py,task,rec["protected_nodes"],original_native,out)
        if report["comparison"]["status"].startswith("UNKNOWN"):
            report["status"]="UNKNOWN_COMPARATOR_NATIVE_APPARATUS"
            return
        report["acquired"]=native_trial.trial_arm("acquired-strict-anchor",new,
                         source,original,work,py,task,rec["protected_nodes"],original_native,out)
        if report["acquired"]["status"].startswith("UNKNOWN"):
            report["status"]="UNKNOWN_ACQUIRED_NATIVE_APPARATUS"
            return
        qualified=report["acquired"].get("winner")
        comparison_success=report["comparison"].get("winner")
        if not qualified:
            report["status"]=("REJECTED_FROZEN_METHOD_INAPPLICABLE" if not new
                              else "REJECTED_FROZEN_METHOD_NATIVE")
        elif comparison_success:
            report["status"]="CANDIDATE_CROSS_SOURCE_METHOD_TRANSFERS_BUT_BASELINE_TIES"
        else:
            report["status"]="CANDIDATE_CROSS_SOURCE_FAMILY_GAIN_AWAITING_AUDIT"
        assert prod.read_bytes()==original and native_trial.status_allowed(work,task,False)
    except Exception as exc:
        report["status"]="UNKNOWN_PROSPECTIVE_APPARATUS"
        report["error"]=type(exc).__name__+": "+str(exc)
    finally:
        report["wall_seconds"]=round(time.monotonic()-st,3)
        report["G2"]="UNKNOWN"
        (out/"RESULT.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
        print(json.dumps({k:report.get(k) for k in (
             "status","G2","selected_future","acquired_candidate_count",
             "comparator_candidate_count","Lean","CLC","FLASH")},sort_keys=True),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: g2_regex_prospective_future_v1.py FRESH_OUTPUT")
    main(Path(sys.argv[1]).resolve())
