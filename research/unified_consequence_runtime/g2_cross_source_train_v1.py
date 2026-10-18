#!/usr/bin/env python3
"""Prospective G2 V1 training: one source-neutral path/context fallback operator.
No future source, future fixture, or upstream patch is accessed.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as native

ROOT = pathlib.Path(__file__).resolve().parents[2]
U = pathlib.Path("research/unified_consequence_runtime")
FREEZE = "de234c7e180467bbb0b957cac2016263bf80920b"
ROLE = "57c400ea49881e440f7895acaeebeee5854363e3"
SOURCE_SHA = "02c0bbdf7c9254021b10ce296e8e9545cd60779b94053c4cf595790b868a47fd"
OPERATOR = "pure-ast-mode-disabled-fallback-v1"
MAX_CANDIDATES = 16

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def run_git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True, timeout=40).strip()

def pure(node):
    return all(isinstance(n, (ast.BoolOp, ast.UnaryOp, ast.Name, ast.Attribute,
                               ast.Compare, ast.Eq, ast.NotEq, ast.Is, ast.IsNot,
                               ast.And, ast.Or, ast.Not, ast.Constant, ast.Load))
               for n in ast.walk(node))

def fragments(node):
    if not isinstance(node, ast.JoinedStr):
        return ""
    return "".join(x.value for x in node.values
                   if isinstance(x, ast.Constant) and isinstance(x.value, str))

def fresh_pred(test):
    # Precommitted grammar: A and B and C -> A and ((not B) or C).
    # This is an environment-mode-absence fallback, NOT an author patch lookup.
    vals = test.values
    return ast.BoolOp(op=ast.And(), values=[
        vals[0],
        ast.BoolOp(op=ast.Or(), values=[
            ast.UnaryOp(op=ast.Not(), operand=vals[1]), vals[2]])])

def byte_span(raw, node):
    lines = raw.splitlines(keepends=True)
    assert node.lineno <= node.end_lineno <= len(lines)
    lo = sum(len(x) for x in lines[:node.lineno-1]) + node.col_offset
    hi = sum(len(x) for x in lines[:node.end_lineno-1]) + node.end_col_offset
    return lo, hi

def enumerate_candidates(original):
    source = original.decode("utf-8")
    tree = ast.parse(source)
    candidates = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for idx, block in enumerate(fn.body):
            if not (isinstance(block, ast.If) and len(block.body) == 1
                    and isinstance(block.body[0], ast.Return)):
                continue
            condition = block.test
            if not (isinstance(condition, ast.BoolOp)
                    and isinstance(condition.op, ast.And)
                    and len(condition.values) == 3
                    and isinstance(condition.values[0], ast.UnaryOp)
                    and isinstance(condition.values[0].op, ast.Not)
                    and pure(condition)):
                continue
            # Source-neutral output-kind observation: path-only return vs
            # same function's following scheme/host-style URL return.
            relative = fragments(block.body[0].value)
            later = [n for n in fn.body[idx+1:] if isinstance(n, ast.Return)]
            if "/" not in relative or "//" in relative:
                continue
            if not any("//" in fragments(n.value) for n in later):
                continue
            rewritten = fresh_pred(condition)
            ast.fix_missing_locations(rewritten)
            lo, hi = byte_span(original, condition)
            new = original[:lo] + ast.unparse(rewritten).encode() + original[hi:]
            ast.parse(new)
            if new == original:
                continue
            candidates.append({"function": fn.name, "line": block.lineno,
                               "original_guard": ast.unparse(condition),
                               "candidate_guard": ast.unparse(rewritten),
                               "source": new, "source_sha256": digest(new),
                               "operator": OPERATOR, "edit_bytes": len(new)-len(original)})
    return candidates[:MAX_CANDIDATES]

def control_grammar():
    # Purely constructed, non-project synthetic truth-table checks.
    src = '''def f(external, mode_one, mode_two, same_one, same_two):
    if (
        not external
        and (mode_one or mode_two)
        and ((mode_one and same_one) or (mode_two and same_two))
    ):
        return f"/{1}"
    return f"http://{2}"
'''
    cand = enumerate_candidates(src.encode())
    assert len(cand) == 1, ("GRAMMAR_ENUMERATION", len(cand))
    namespace = {}
    exec(compile(cand[0]["source"], "<constructed>", "exec"), namespace)
    f = namespace["f"]
    assert f(False, False, False, False, False) == "/1"
    assert f(False, True, False, True, False) == "/1"
    assert f(False, True, False, False, False) == "http://2"
    assert f(True, False, False, False, False) == "http://2"
    # Rejection control: no host-shaped fallback / no three-way condition.
    assert not enumerate_candidates(b'def f(x):\n    if x:\n        return "/"\n    return "absolute"\n')
    return len(cand)

def run_test(py, world, nodes, dest, timeout=150):
    dest.mkdir(parents=True, exist_ok=False)
    xml = dest / "native.xml"
    start = time.monotonic()
    argv = [str(py), "-m", "pytest", "-q", "--junitxml="+str(xml), *nodes]
    try:
        p = subprocess.run(argv, cwd=world, capture_output=True, text=True,
                           timeout=timeout, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        (dest/"stdout.txt").write_text(p.stdout)
        (dest/"stderr.txt").write_text(p.stderr)
        counts = native.junit(xml)
        cases = []
        if xml.is_file():
            for el in ET.parse(xml).getroot().iter("testcase"):
                cases.append({"name":el.attrib.get("name",""), "class":el.attrib.get("classname",""),
                              "fail":bool(list(el.iter("failure"))),
                              "skip":bool(list(el.iter("skipped")))})
        return {"returncode":p.returncode, "counts":counts, "cases":cases,
                "elapsed_seconds":round(time.monotonic()-start,4)}
    except subprocess.TimeoutExpired:
        return {"returncode":124, "counts":{"tests":0,"failures":0,"errors":1,"skipped":0},
                "cases":[], "status":"UNKNOWN_NATIVE_TIMEOUT"}

def native_pass(rec, exact=None):
    counts = rec["counts"]
    return (rec["returncode"] == 0 and counts["tests"] >= 1
            and counts["failures"] == 0 and counts["errors"] == 0
            and counts["skipped"] == 0 if exact is not None else
            rec["returncode"] == 0 and counts["tests"] >= 1
            and counts["failures"] == 0 and counts["errors"] == 0) and (
                exact is None or
                (counts["tests"] == len(exact) and
                 sorted(x["name"] for x in rec["cases"]) == sorted(x.split("::")[-1] for x in exact)))

def original_fail(rec, n):
    c = rec["counts"]
    return (rec["returncode"] == 1 and c["tests"] == n
            and c["failures"] >= 1 and c["errors"] == c["skipped"] == 0)

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    rec={"schema":"G2_CROSS_SOURCE_TRAINING_V1", "status":"UNKNOWN_APPARATUS",
         "G2":"UNKNOWN", "future":"SEALED_UNOPENED", "operator":OPERATOR,
         "prospective_future_visited":False}
    try:
        # Pretest/protocol identity is material: ensure previously frozen rules.
        subprocess.check_call(["git","-C",str(ROOT),"cat-file","-e",FREEZE+"^{commit}"])
        subprocess.check_call(["git","-C",str(ROOT),"merge-base","--is-ancestor",FREEZE,"HEAD"])
        rolepath = "research/unified_consequence_runtime/G2_NATIVE_FIRST_FAIL_POOL_V2_ROLE_FREEZE.json"
        assert (ROOT/rolepath).read_bytes() == subprocess.check_output(
            ["git","-C",str(ROOT),"show",ROLE+":"+rolepath])
        manifest = json.loads((ROOT/rolepath).read_text())
        assert len(manifest["sealed_futures"]) == 1
        assert manifest["sealed_futures"][0]["repo"] == "pypa/packaging"
        task = manifest["training_candidates"][0]
        assert task["repo"] == "pallets/werkzeug" and task["pr"] == 3215
        rec["grammar_controls"] = control_grammar()
        admission = native.one(task, 0, out/"admission")
        rec["admission"] = admission
        if admission["status"] != "ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            rec["status"]="UNKNOWN_NO_NATIVE_TRAINING_OBLIGATION"
            return
        assert admission["source_sha256"] == SOURCE_SHA
        world=pathlib.Path(admission["work_dir"])
        py=pathlib.Path(admission["interpreter"])
        source=world/task["production"]
        orig=source.read_bytes()
        protected=admission["protected_nodes"]
        assert len(protected)==2 and len(orig)>0
        assert run_git(world,"rev-parse","HEAD")==task["base"]
        assert digest((world/task["author_test"]).read_bytes()) == admission["head_test_sha256"]
        assert run_git(world,"diff","--name-only").splitlines()==[task["author_test"]]
        baseline=run_test(py,world,protected,out/"baseline",timeout=150)
        rec["baseline"]=baseline
        if not original_fail(baseline,len(protected)):
            rec["status"]="UNKNOWN_BASELINE_NOT_REPRODUCED"
            return
        candidates=enumerate_candidates(orig)
        rec["enumeration"]=[{k:v for k,v in c.items() if k!="source"} for c in candidates]
        if not candidates:
            rec["status"]="UNKNOWN_NO_LICENSED_OPERATOR"
            return
        for idx,c in enumerate(candidates):
            dest=out/("candidate-"+str(idx).zfill(2))
            try:
                source.write_bytes(c["source"])
                assert digest(source.read_bytes())==c["source_sha256"]
                assert sorted(run_git(world,"diff","--name-only").splitlines()) == sorted(
                    [task["author_test"],task["production"]])
                a=run_test(py,world,protected,dest/"protected-a")
                outcome={"source_sha256":c["source_sha256"],"protected_a":a}
                if not native_pass(a,protected):
                    rec.setdefault("attempts",[]).append({"index":idx,**outcome,"status":"REJECTED_PROTECTED"})
                    continue
                full=run_test(py,world,[task["author_test"]],dest/"full-author",timeout=180)
                outcome["full_author"]=full
                if not native_pass(full):
                    rec.setdefault("attempts",[]).append({"index":idx,**outcome,"status":"REJECTED_REGRESSION"})
                    continue
                b=run_test(py,world,protected,dest/"protected-b")
                outcome["protected_b"]=b
                if not native_pass(b,protected):
                    rec.setdefault("attempts",[]).append({"index":idx,**outcome,"status":"REJECTED_REPEAT"})
                    continue
                source.write_bytes(orig)
                withdrawal=run_test(py,world,protected,dest/"withdrawal")
                outcome["withdrawal"]=withdrawal
                if not original_fail(withdrawal,len(protected)):
                    rec.setdefault("attempts",[]).append({"index":idx,**outcome,"status":"UNKNOWN_NO_CAUSAL_WITHDRAWAL"})
                    continue
                source.write_bytes(c["source"])
                restoration=run_test(py,world,protected,dest/"restoration")
                outcome["restoration"]=restoration
                if not native_pass(restoration,protected) or digest(source.read_bytes())!=c["source_sha256"]:
                    rec.setdefault("attempts",[]).append({"index":idx,**outcome,"status":"UNKNOWN_NO_CAUSAL_RESTORATION"})
                    continue
                rec["admitted_operator"]={k:v for k,v in c.items() if k!="source"}
                (dest/"candidate_source.py").write_bytes(c["source"])
                rec.setdefault("attempts",[]).append({"index":idx,**outcome,"status":"WARRANTED_BOUNDED_TRAINING_ONLY"})
                rec["status"]="WARRANTED_BOUNDED_TRAINING_REPAIR_FUTURE_SEALED"
                break
            finally:
                source.write_bytes(orig)
                assert digest(source.read_bytes())==SOURCE_SHA
                assert run_git(world,"diff","--name-only").splitlines()==[task["author_test"]]
        else:
            rec["status"]="REJECTED_NO_QUALIFIED_TRAINING_REPAIR"
    except Exception as exc:
        rec["status"]="UNKNOWN_APPARATUS"
        rec["error"]=type(exc).__name__+": "+str(exc)[:1000]
        rec["traceback_tail"]=traceback.format_exc(limit=8)[-1600:]
    finally:
        rec["future"]="SEALED_UNOPENED"
        rec["G2"]="UNKNOWN"
        (out/"RESULT.json").write_text(json.dumps(rec,indent=2,sort_keys=True,default=str)+"\n")
        print("TRAINING_RESULT",rec["status"],"FUTURE",rec["future"],"G2",rec["G2"],flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: g2_cross_source_train_v1.py FRESH_OUTPUT")
    main(pathlib.Path(sys.argv[1]).resolve())
