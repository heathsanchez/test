#!/usr/bin/env python3
"""Generate finite, source-neutral terminal-boundary edits on exposed training.

Future metadata is frozen; this script NEVER opens future source or test bodies.
Passing training does NOT establish prospective G2, formal CLC or FLASH soundness.
"""
from __future__ import annotations
import ast
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as pool
from research.unified_consequence_runtime import g2_werkzeug_guard_genesis_v1 as native_gate

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
PROTOCOL="32de5bd464208dc14e0f374db31cfaeae72288db"
PACKAGE_BASE="332d716676eb934b67ede4054a3e3e0d4022b2d3"
PACKAGE_HEAD="a4f5d377a62e96759a4d9237256ec5dc3b19444e"
SOURCE_SHA="a10d2871bb4015855a6e894790949189afff40ae7364fe0210efa91e299fa32e"
MAX_CANDIDATES=32

def sha(data):
    return hashlib.sha256(data).hexdigest()

def pos(lines,row,col):
    return sum(len(s) for s in lines[:row-1])+col

def compile_names(tree):
    names=set()
    for n in ast.walk(tree):
        if not isinstance(n,(ast.Assign,ast.AnnAssign)):continue
        call=n.value
        if not isinstance(call,ast.Call) or not isinstance(call.func,ast.Attribute):continue
        if not (isinstance(call.func.value,ast.Name) and call.func.value.id=="re"
                and call.func.attr=="compile"):continue
        targets=n.targets if isinstance(n,ast.Assign) else [n.target]
        names.update(t.id for t in targets if isinstance(t,ast.Name))
    return names

def enumerate_candidates(source):
    tree=ast.parse(source)
    compiled=compile_names(tree)
    lines=source.splitlines(keepends=True)
    found=[]
    seen=set()
    def propose(node,new_segment,kind):
        start=pos(lines,node.lineno,node.col_offset)
        end=pos(lines,node.end_lineno,node.end_col_offset)
        old=source[start:end]
        edited=source[:start]+new_segment+source[end:]
        if edited==source or edited in seen:return
        try:
            ast.parse(edited)
            compile(edited,"<regex-generator-candidate>","exec")
        except (SyntaxError,ValueError):return
        seen.add(edited)
        found.append({"kind":kind,"line":node.lineno,
                      "candidate_sha256":sha(edited.encode()),
                      "bytes_added":len(edited.encode())-len(source.encode()),
                      "old_expr":old,"new_expr":new_segment,"_edited":edited})
    for call in ast.walk(tree):
        if not isinstance(call,ast.Call):continue
        func=call.func
        is_direct=(isinstance(func,ast.Attribute)
                   and isinstance(func.value,ast.Name)
                   and func.value.id=="re" and func.attr in {"compile","match","search"})
        is_compiled=(isinstance(func,ast.Attribute)
                     and isinstance(func.value,ast.Name) and func.value.id in compiled)
        if is_direct and call.args:
            v=call.args[0]
            if isinstance(v,ast.Constant) and isinstance(v.value,str):
                literal=ast.get_source_segment(source,v)
                pattern=v.value
                # Raw, simple quoted literals only; terminal $ not escaped.
                if (literal and len(literal)>=4 and literal[0] in "rR"
                    and literal[1] in ("'",'"') and literal[-1]==literal[1]
                    and literal[-2]=="$" and not literal.startswith(literal[:2]*3)):
                    backslashes=len(pattern[:-1])-len(pattern[:-1].rstrip("\\"))
                    if backslashes%2==0:
                        propose(v,literal[:-2]+r"\Z"+literal[-1],"strict_terminal_anchor")
        if isinstance(func,ast.Attribute) and func.attr=="match":
            if ((isinstance(func.value,ast.Name) and func.value.id in compiled)
                or (isinstance(func.value,ast.Name) and func.value.id=="re")):
                fragment=ast.get_source_segment(source,func)
                if fragment and fragment.endswith(".match"):
                    propose(func,fragment[:-6]+".fullmatch","whole_input_match")
    found.sort(key=lambda x:(abs(x["bytes_added"]),x["line"],x["kind"]))
    return found[:MAX_CANDIDATES]

def source_identified():
    p=U+"G2_REGEX_BOUNDARY_SOURCE_DISTINCT_V1_FROZEN_PROTOCOL.md"
    assert (ROOT/p).read_bytes()==subprocess.check_output(
        ["git","-C",str(ROOT),"show",PROTOCOL+":"+p],timeout=25)
    return {"repo":"pypa/packaging","pr":1446,"base":PACKAGE_BASE,
            "head":PACKAGE_HEAD,"production":"src/packaging/pylock.py",
            "author_test":"tests/test_pylock.py"}

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    result={"schema":"G2_REGEX_BOUNDARY_TRAIN_PACKAGING_V1",
            "status":"UNKNOWN_TRAINING_ENVIRONMENT","G2":"UNKNOWN",
            "future":"ALL_THREE_SOURCE_UNOPENED","protocol_sha":PROTOCOL,
            "candidate_trials":[]}
    start=time.monotonic()
    try:
        task=source_identified()
        rec=pool.one(task,0,out/"original-admission")
        result["original_training"]={k:v for k,v in rec.items() if k!="provisioning"}
        if rec["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            result["status"]="UNKNOWN_ORIGINAL_TRAIN_NOT_ADMITTED"
            return
        assert rec["source_sha256"]==SOURCE_SHA
        count=rec["native"]["counts"]["tests"]
        assert count==5 and rec["native"]["counts"]["failures"]==1
        assert rec["native"]["counts"]["errors"]==rec["native"]["counts"]["skipped"]==0
        work=Path(rec["work_dir"]);py=Path(rec["interpreter"])
        prod=work/task["production"];original=prod.read_bytes()
        assert sha(original)==SOURCE_SHA
        source=original.decode("utf-8")
        items=enumerate_candidates(source)
        result["candidates"]=[{k:v for k,v in n.items() if k!="_edited"} for n in items]
        result["candidate_count"]=len(items)
        result["status"]="REJECTED_NO_QUALIFIED_REGEX_BOUNDARY_OPERATOR"
        for rank,item in enumerate(items):
            if time.monotonic()-start>750:
                result["status"]="UNKNOWN_TRAINING_BUDGET"
                break
            edited=item["_edited"].encode()
            prod.write_bytes(edited)
            assert pool.git(work,"diff","--name-only").splitlines()==sorted([task["production"],task["author_test"]])
            row={"rank":rank,"kind":item["kind"],"source_sha256":sha(edited)}
            result["candidate_trials"].append(row)
            row["protected"]=native_gate.native(py,work,rec["protected_nodes"],"candidate-%02d-protected"%rank,out,150)
            if not native_gate.exact_pass(row["protected"],count):
                prod.write_bytes(original)
                continue
            row["full"]=native_gate.native(py,work,[task["author_test"]],"candidate-%02d-full"%rank,out,240)
            f=row["full"]["counts"]
            if (row["full"]["exit"]!=0 or f["tests"]<=count or
                f["failures"]!=0 or f["errors"]!=0):
                prod.write_bytes(original)
                continue
            prod.write_bytes(original)
            row["withdrawal"]=native_gate.native(py,work,rec["protected_nodes"],"candidate-%02d-withdrawal"%rank,out,150)
            if not (native_gate.exact_original(row["withdrawal"],count)
                    and row["withdrawal"]["counts"]["failures"]==1):
                raise RuntimeError("CAUSAL_WITHDRAWAL_NOT_RESTORED")
            prod.write_bytes(edited)
            row["restoration"]=native_gate.native(py,work,rec["protected_nodes"],"candidate-%02d-restoration"%rank,out,150)
            if not native_gate.exact_pass(row["restoration"],count):
                raise RuntimeError("CAUSAL_RESTORATION_NOT_PASSED")
            patch="".join(difflib.unified_diff(source.splitlines(keepends=True),
                item["_edited"].splitlines(keepends=True),
                fromfile="original/"+task["production"],
                tofile="generated/"+task["production"]))
            (out/"ACQUIRED_REGEX_OPERATOR.patch").write_text(patch)
            operator={"name":item["kind"],"source_mutator_callable":"enumerate_candidates",
                "source_file_sha256":sha(Path(__file__).read_bytes()),
                "selected_rank":rank,"selected_candidate_sha256":sha(edited),
                "original_source_sha256":SOURCE_SHA,
                "operator_family":"source-neutral terminal regex validation",
                "future_source_opened":False}
            (out/"ACQUIRED_REGEX_OPERATOR.json").write_text(json.dumps(operator,indent=2,sort_keys=True)+"\n")
            result["status"]="CANDIDATE_REGEX_TRAIN_NATIVE_GREEN_AWAITING_AUDIT"
            break
        prod.write_bytes(original)
        assert sha(prod.read_bytes())==SOURCE_SHA
    except Exception as exc:
        result["status"]="UNKNOWN_TRAINING_APPARATUS"
        result["error"]=type(exc).__name__+": "+str(exc)
    finally:
        result["wall_seconds"]=round(time.monotonic()-start,3)
        result["G2"]="UNKNOWN"
        (out/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps({k:result.get(k) for k in ("status","G2","candidate_count","future")}),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: g2_regex_terminal_genesis_v1.py FRESH_OUTPUT")
    main(Path(sys.argv[1]).resolve())
