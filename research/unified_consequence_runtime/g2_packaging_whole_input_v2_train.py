#!/usr/bin/env python3
"""Packaging exposed-training residual: generate source-neutral whole-string
boundary observations. Never reads unopened Click source or outcomes.
"""
from __future__ import annotations
import ast, hashlib, json, pathlib, subprocess, sys, traceback
from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as native
from research.unified_consequence_runtime import g2_cross_source_train_v1 as oracle
from research.unified_consequence_runtime import g2_whole_input_regex_syntax_v2 as v2

ROOT=pathlib.Path(__file__).resolve().parents[2]
U=pathlib.Path("research/unified_consequence_runtime")
PRECOMMIT="d659a652607b82fe79adf77f4582408602c5d951"
SOURCE_SHA="a10d2871bb4015855a6e894790949189afff40ae7364fe0210efa91e299fa32e"
FUTURE_ROLE={"repo":"dbader/schedule","pr":666}
MAX_OPTIONS=24

def sha(b): return hashlib.sha256(b).hexdigest()
def span(raw,node): return oracle.byte_span(raw,node)
def splice(raw,node,replacement):
    lo,hi=span(raw,node)
    out=raw[:lo]+replacement+raw[hi:]
    ast.parse(out)
    return out
def option(old,new,node,family):
    return {"family":family,"line":node.lineno,
            "source_sha256":sha(new),"delta_bytes":abs(len(new)-len(old)),
            "source":new}
def enumerate_candidates(source):
    raw=source.encode() if isinstance(source,str) else source
    root=ast.parse(raw.decode("utf-8"))
    options=[]
    anchored={}
    for node in ast.walk(root):
        if (isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
            and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute)
            and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=="re"
            and node.value.func.attr=="compile" and node.value.args
            and isinstance(node.value.args[0],ast.Constant) and isinstance(node.value.args[0].value,str)):
            pattern=node.value.args[0].value
            if pattern.startswith("^") and pattern.endswith("$") and not node.value.keywords:
                anchored[node.targets[0].id]=node.value.args[0]
                literal=node.value.args[0]
                lo,hi=span(raw,literal)
                original=raw[lo:hi]
                if original.endswith((b'$"',b"$'")):
                    after=original[:-2]+b'\\Z'+original[-1:]
                else:
                    after=repr(pattern[:-1]+"\\Z").encode("utf-8")
                candidate=splice(raw,literal,after)
                options.append(option(raw,candidate,literal,"strict_terminal_regex_anchor"))
    for node in ast.walk(root):
        if not (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
                and node.func.attr=="match"):
            continue
        v=node.func.value
        if not (isinstance(v,ast.Name) and v.id in anchored):
            continue
        target=node.func
        lo,hi=span(raw,target)
        old=raw[lo:hi]
        if not old.endswith(b".match"):
            continue
        candidate=raw[:lo]+old[:-5]+b"fullmatch"+raw[hi:]
        ast.parse(candidate)
        options.append(option(raw,candidate,target,"compiled_pattern_fullmatch"))
    # Conservative source-neutral primitive suffix rejection, only for a
    # Boolean validator already using an anchored regex on a simple property.
    for fn in ast.walk(root):
        if not isinstance(fn,ast.FunctionDef) or len(fn.args.args)!=1:
            continue
        arg=fn.args.args[0].arg
        if not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                   and n.func.attr=="match"
                   and isinstance(n.func.value,ast.Name) and n.func.value.id in anchored
                   and any(isinstance(q,ast.Attribute) and isinstance(q.value,ast.Name)
                           and q.value.id==arg for q in ast.walk(n))
                   for n in ast.walk(fn)):
            continue
        # Insert before first executable statement, after docstring.
        body=fn.body
        loc=1 if body and isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str) else 0
        if len(body)<=loc: continue
        lead=body[loc]
        lines=raw.splitlines(keepends=True)
        offset=sum(len(x) for x in lines[:lead.lineno-1])
        indent=b" " * lead.col_offset
        guard=(indent+b"if getattr("+arg.encode()+b", 'name', '').endswith(('\\n', '\\r')):\n"
               +indent+b"    return False\n")
        candidate=raw[:offset]+guard+raw[offset:]
        ast.parse(candidate)
        options.append(option(raw,candidate,lead,"primitive_terminal_control_suffix"))
    unique={}
    for c in options:
        unique[c["source_sha256"]]=c
    ordered=sorted(unique.values(),key=lambda o:(o["delta_bytes"],o["line"],o["family"]))
    return ordered[:MAX_OPTIONS]

def protected_pass(rec):
    c=rec["counts"]
    # One changed parameterized author-test node expands to five real testcases.
    names=[x["name"] for x in rec.get("cases",[])]
    return (rec["returncode"]==0 and c["tests"]==5 and c["failures"]==0
            and c["errors"]==0 and c["skipped"]==0 and len(names)==5
            and all(x.startswith("test_pylock_file_name[") for x in names))

def controls():
    sample='''import re
_P = re.compile(r"^sample\\.([^.]+)\\.txt$")
def ok(x):
    return bool(_P.match(x))
'''
    ops=enumerate_candidates(sample)
    assert ops, "NO_SYNTHETIC_BOUNDARY_OPERATORS"
    applicable=[]
    for c in ops:
        ns={}
        exec(c["source"],ns)
        if ns["ok"]("sample.a.txt") and not ns["ok"]("sample.a.txt\n"):
            applicable.append(c["family"])
    assert applicable and "strict_terminal_regex_anchor" in applicable
    assert not enumerate_candidates(b"def f(x): return x == 3\n")
    return applicable

def train(out):
    out.mkdir(parents=True,exist_ok=False)
    report={"schema":"G2_PACKAGING_WHOLE_INPUT_V2_TRAIN",
            "status":"UNKNOWN_TRAINING_APPARATUS",
            "future":"SCHEDULE_SEALED_UNOPENED","G2":"UNKNOWN",
            "future_source_visited":False}
    try:
        assert subprocess.call(["git","-C",str(ROOT),"merge-base","--is-ancestor",PRECOMMIT,"HEAD"])==0
        manifest=json.loads((ROOT/"research/unified_consequence_runtime/G2_NATIVE_FIRST_FAIL_POOL_V2_ROLE_FREEZE.json").read_text())
        task=manifest["sealed_futures"][0]
        future=FUTURE_ROLE
        assert task["repo"]=="pypa/packaging" and task["pr"]==1446
        assert future["repo"]==FUTURE_ROLE["repo"] and future["pr"]==FUTURE_ROLE["pr"]
        assert report["future_source_visited"] is False
        report["grammar_controls"]=v2.controls()
        admitted=native.one(task,0,out/"native-admission")
        report["original_admission"]=admitted
        if admitted["status"]!="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            report["status"]="UNKNOWN_TRAINING_NATIVE_NOT_ADMITTED"
            return
        assert admitted["source_sha256"]==SOURCE_SHA
        assert admitted["native"]["counts"]=={"tests":5,"failures":1,"errors":0,"skipped":0}
        world=pathlib.Path(admitted["work_dir"])
        source=world/task["production"]
        orig=source.read_bytes()
        protected=admitted["protected_nodes"]
        py=pathlib.Path(admitted["interpreter"])
        assert sha(orig)==SOURCE_SHA and len(protected)==1
        assert oracle.run_git(world,"diff","--name-only").splitlines()==[task["author_test"]]
        baseline=oracle.run_test(py,world,protected,out/"native-repeat-original")
        report["baseline"]=baseline
        if not oracle.original_fail(baseline,5):
            report["status"]="UNKNOWN_TRAINING_ORIGINAL_NOT_REPRODUCED"
            return
        candidates=v2.enumerate_candidates(orig)
        report["candidates"]=[{k:v for k,v in c.items() if k!="source"} for c in candidates]
        if not candidates:
            report["status"]="UNKNOWN_NO_BOUNDARY_OPERATOR"
            return
        for i,op in enumerate(candidates):
            dest=out/("candidate-"+str(i).zfill(2))
            try:
                source.write_bytes(op["source"])
                assert sorted(oracle.run_git(world,"diff","--name-only").splitlines())==sorted([task["author_test"],task["production"]])
                a=oracle.run_test(py,world,protected,dest/"protected-a")
                trial={"index":i,"family":op["family"],"source_sha256":op["source_sha256"],
                       "first":a,"status":"REJECTED_PROTECTED"}
                report.setdefault("trials",[]).append(trial)
                if not protected_pass(a):
                    continue
                full=oracle.run_test(py,world,[task["author_test"]],dest/"full-author",timeout=180)
                trial["full_author"]=full
                if not oracle.native_pass(full):
                    trial["status"]="REJECTED_REGRESSION"
                    continue
                b=oracle.run_test(py,world,protected,dest/"protected-b")
                trial["second"]=b
                if not protected_pass(b):
                    trial["status"]="REJECTED_REPEAT"
                    continue
                source.write_bytes(orig)
                withdrawal=oracle.run_test(py,world,protected,dest/"withdrawal")
                trial["withdrawal"]=withdrawal
                if not oracle.original_fail(withdrawal,5):
                    trial["status"]="UNKNOWN_NO_CAUSAL_WITHDRAWAL"
                    continue
                source.write_bytes(op["source"])
                restored=oracle.run_test(py,world,protected,dest/"restoration")
                trial["restoration"]=restored
                if not protected_pass(restored) or sha(source.read_bytes())!=op["source_sha256"]:
                    trial["status"]="UNKNOWN_NO_CAUSAL_RESTORATION"
                    continue
                trial["status"]="WARRANTED_BOUNDED_TRAINING_ONLY"
                report["status"]="WARRANTED_BOUNDED_PACKAGING_NEW_OBSERVATION_TRAINING"
                report["acquired_operator"]={k:v for k,v in op.items() if k!="source"}
                (dest/"candidate_source.py").write_bytes(op["source"])
                break
            finally:
                source.write_bytes(orig)
                assert sha(source.read_bytes())==SOURCE_SHA
                assert oracle.run_git(world,"diff","--name-only").splitlines()==[task["author_test"]]
        else:
            report["status"]="REJECTED_NO_NATIVE_BOUNDARY_REPAIR"
    except Exception as exc:
        report["status"]="UNKNOWN_TRAINING_APPARATUS"
        report["error"]=type(exc).__name__+": "+str(exc)[:1000]
        report["traceback_tail"]=traceback.format_exc(limit=8)[-1700:]
    finally:
        report["future"]="SCHEDULE_SEALED_UNOPENED"
        report["future_source_visited"]=False
        report["G2"]="UNKNOWN"
        (out/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
        print("NEW_OBSERVATION_TRAIN",report["status"],"FUTURE",report["future"],flush=True)
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("usage: g2_packaging_boundary_genesis_v1.py OUTPUT")
    train(pathlib.Path(sys.argv[1]).resolve())
