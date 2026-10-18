#!/usr/bin/env python3
"""Source-neutral bounded guard-fallback candidate search on exposed training only.

This script NEVER reads the separately frozen Packaging future. A successful
train result remains G2 UNKNOWN until a new prospective future qualification.
"""
from __future__ import annotations
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as pool

ROOT = Path(__file__).resolve().parents[2]
U = "research/unified_consequence_runtime/"
PROTOCOL = "de234c7e180467bbb0b957cac2016263bf80920b"
ROLE = "57c400ea49881e440f7895acaeebeee5854363e3"
EXPECTED_SOURCE_SHA = "02c0bbdf7c9254021b10ce296e8e9545cd60779b94053c4cf595790b868a47fd"
MAX_CANDIDATES = 16
MAX_SEARCH_SECONDS = 750
METHOD_ID = "context_disabled_guard_fallback_v1"

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def frozen_ref(commit: str, relpath: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "show", commit + ":" + relpath], timeout=35
    )

def freeze_check() -> dict:
    rel = U + "G2_CROSS_SOURCE_CONSEQUENCE_LAW_V1_FROZEN_PROTOCOL.md"
    assert (ROOT / rel).read_bytes() == frozen_ref(PROTOCOL, rel), "PROTOCOL_MODIFIED"
    rel = U + "G2_NATIVE_FIRST_FAIL_POOL_V2_ROLE_FREEZE.json"
    assert (ROOT / rel).read_bytes() == frozen_ref(ROLE, rel), "ROLES_MODIFIED"
    spec = json.loads(frozen_ref(ROLE, rel))
    train = spec["training_candidates"][0]
    assert train["repo"] == "pallets/werkzeug" and train["pr"] == 3215
    assert spec["sealed_futures"][0]["role"] == "SEALED_FUTURE"
    assert train["production"] == "src/werkzeug/routing/map.py"
    return train

def offset(lines: list[str], row: int, col: int) -> int:
    return sum(len(s) for s in lines[:row - 1]) + col

def enumerate_candidates(source: str) -> list[dict]:
    """Enumerate AST-shape mutations; no target identifier or failure literal."""
    syntax = ast.parse(source)
    lines = source.splitlines(keepends=True)
    out: list[dict] = []
    for node in ast.walk(syntax):
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.BoolOp):
            continue
        if not isinstance(node.test.op, ast.And):
            continue
        terms = node.test.values
        if len(terms) < 3 or not any(isinstance(n, ast.Return) for n in node.body):
            continue
        # An adjacent context-disjunction guard and outcome guard:
        # A and (B_or_C) and D -> A and (not (B_or_C) or D)
        # This adds the missing disabled-context fallback without naming B/C/D.
        for i in range(1, len(terms) - 1):
            guard = terms[i]
            following = terms[i + 1]
            if not (isinstance(guard, ast.BoolOp) and isinstance(guard.op, ast.Or)):
                continue
            new = ast.BoolOp(op=ast.And(), values=[
                *terms[:i],
                ast.BoolOp(op=ast.Or(), values=[
                    ast.UnaryOp(op=ast.Not(), operand=guard),
                    following
                ]),
                *terms[i + 2:]
            ])
            ast.fix_missing_locations(new)
            old_expr = ast.get_source_segment(source, node.test)
            replacement = ast.unparse(new)
            start = offset(lines, node.test.lineno, node.test.col_offset)
            end = offset(lines, node.test.end_lineno, node.test.end_col_offset)
            if not old_expr or source[start:end] != old_expr:
                continue
            edited = source[:start] + replacement + source[end:]
            if edited == source:
                continue
            try:
                ast.parse(edited)
                compile(edited, "<source-neutral-candidate>", "exec")
            except (SyntaxError, ValueError):
                continue
            out.append({
                "tag": METHOD_ID, "if_line": node.lineno, "guard_term_index": i,
                "old_predicate": old_expr, "new_predicate": replacement,
                "bytes_added": len(edited.encode()) - len(source.encode()),
                "candidate_source_sha256": digest(edited.encode()),
                "_edited": edited
            })
    out.sort(key=lambda v: (abs(v["bytes_added"]), v["if_line"], v["guard_term_index"]))
    return out[:MAX_CANDIDATES]

def native(py: Path, work: Path, nodes: list[str], name: str, out: Path,
           timeout: int = 150) -> dict:
    junit = out / (name + ".xml")
    argv = [str(py), "-m", "pytest", "-q", "--junitxml=" + str(junit), *nodes]
    start = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=work, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True, timeout=timeout,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        state = {"exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except subprocess.TimeoutExpired as e:
        state = {"exit": 124, "stdout": (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout,bytes) else (e.stdout or ""),
                 "stderr": "TIMEOUT"}
    log = out / (name + ".log")
    log.write_text(json.dumps({"argv": argv, **state}, indent=2) + "\n")
    c = pool.junit(junit)
    return {"exit": state["exit"], "counts": c, "seconds": round(time.monotonic()-start, 3),
            "log_sha256": digest(log.read_bytes()), "junit_sha256": digest(junit.read_bytes()) if junit.exists() else None}

def exact_pass(x: dict, n: int) -> bool:
    c = x["counts"]
    return x["exit"] == 0 and c == {"tests": n, "failures": 0, "errors": 0, "skipped": 0}

def exact_original(x: dict, n: int) -> bool:
    c = x["counts"]
    return x["exit"] == 1 and c["tests"] == n and c["failures"] >= 1 and c["errors"] == c["skipped"] == 0

def main(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema": "SOURCE_DISTINCT_G2_TRAIN_WERKZEUG_V1",
              "status": "UNKNOWN_ENVIRONMENT", "G2": "UNKNOWN",
              "future": "SEALED_UNOPENED", "method": METHOD_ID,
              "protocol_commit": PROTOCOL, "method_frozen_before_future": False,
              "candidate_trials": [], "source_distinct_future_results": None}
    start = time.monotonic()
    try:
        task = freeze_check()
        admitted = pool.one(task, 0, output / "original-admission")
        report["original_admission"] = {k:v for k,v in admitted.items() if k not in ("provisioning",)}
        if admitted["status"] != "ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            report["status"] = "UNKNOWN_ORIGINAL_NOT_ADMITTED"
            return
        assert admitted["source_sha256"] == EXPECTED_SOURCE_SHA, "ORIGINAL_SOURCE_HASH_CHANGED"
        work,py = Path(admitted["work_dir"]),Path(admitted["interpreter"])
        protected = admitted["protected_nodes"]
        assert len(protected) == 2 and admitted["native"]["counts"] == {
            "tests":2, "failures":1, "errors":0, "skipped":0
        }, "BASELINE_NOT_REPRODUCED"
        prod = work/task["production"]
        original = prod.read_bytes()
        assert digest(original) == EXPECTED_SOURCE_SHA
        source = original.decode("utf-8")
        items = enumerate_candidates(source)
        report["candidate_count"] = len(items)
        report["candidate_metadata"] = [
            {k:v for k,v in x.items() if k != "_edited"} for x in items
        ]
        if not items:
            report["status"] = "UNKNOWN_TRAINING_GRAMMAR_INAPPLICABLE"
            return
        report["status"] = "REJECTED_NO_QUALIFIED_TRAINING_CANDIDATE"
        for idx,item in enumerate(items):
            if time.monotonic()-start > MAX_SEARCH_SECONDS:
                report["status"] = "UNKNOWN_TRAINING_BUDGET"
                break
            edited = item["_edited"].encode()
            prod.write_bytes(edited)
            if pool.git(work,"diff","--name-only").splitlines() != sorted([task["production"],task["author_test"]]):
                raise RuntimeError("UNAUTHORIZED_CHANGE")
            if digest(prod.read_bytes()) != digest(edited):
                raise RuntimeError("MUTATION_IDENTITY_FAILED")
            trial = {"rank":idx,"source_sha256":digest(edited),"line":item["if_line"]}
            report["candidate_trials"].append(trial)
            trial["protected"] = native(py,work,protected,"candidate-%02d-protected"%idx,output,150)
            if not exact_pass(trial["protected"],len(protected)):
                prod.write_bytes(original)
                continue
            trial["routing_full"] = native(py,work,[task["author_test"]],"candidate-%02d-full"%idx,output,240)
            if not (trial["routing_full"]["exit"]==0 and trial["routing_full"]["counts"]["tests"]>len(protected)
                    and trial["routing_full"]["counts"]["errors"]==0
                    and trial["routing_full"]["counts"]["skipped"]==0
                    and trial["routing_full"]["counts"]["failures"]==0):
                prod.write_bytes(original)
                continue
            # Exact physical withdrawal, observation of original FAIL, restoration.
            prod.write_bytes(original)
            trial["withdrawal"] = native(py,work,protected,"candidate-%02d-withdrawal"%idx,output,150)
            if not exact_original(trial["withdrawal"],len(protected)):
                raise RuntimeError("CAUSAL_WITHDRAWAL_FAILURE")
            prod.write_bytes(edited)
            trial["restoration"] = native(py,work,protected,"candidate-%02d-restored"%idx,output,150)
            if not exact_pass(trial["restoration"],len(protected)):
                raise RuntimeError("CAUSAL_RESTORATION_FAILURE")
            patch = "".join(difflib.unified_diff(source.splitlines(keepends=True),
                     item["_edited"].splitlines(keepends=True),
                     fromfile="original/"+task["production"], tofile="generated/"+task["production"]))
            (output/"TRAINING_GENERATED_PATCH.diff").write_text(patch)
            (output/"ACQUIRED_OPERATOR.json").write_text(json.dumps({
                "name":METHOD_ID,"selected_rank":idx,"selector":"minimum_abs_AST_changed_bytes",
                "candidate_transform":"AND adjacent OR-context and consequence -> OR(not context, consequence)",
                "operator_source_sha256":digest(Path(__file__).read_bytes()),
                "training_source_sha256":digest(original),
                "training_patched_source_sha256":digest(edited),
                "training_protected_nodes":protected,
                "future":"SEALED_UNOPENED", "future_candidate_not_evaluated":True
            },indent=2,sort_keys=True)+"\n")
            report["status"] = "WARRANTED_BOUNDED_TRAINING_OPERATOR_ONLY"
            report["training_source_changed"] = True
            break
        # Restore entire external checkout; all artifacts refer to source snapshot.
        prod.write_bytes(original)
        if digest(prod.read_bytes()) != EXPECTED_SOURCE_SHA:
            raise RuntimeError("ORIGINAL_SOURCE_RESTORE_FAILED")
    except Exception as e:
        report["status"] = "UNKNOWN_TRAINING_APPARATUS"
        report["error"] = "%s: %s" % (type(e).__name__,str(e))
    finally:
        report["elapsed_seconds"] = round(time.monotonic()-start,3)
        report["future"] = "SEALED_UNOPENED"
        report["G2"] = "UNKNOWN"
        (output/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"status":report["status"],"G2":report["G2"],
              "future":report["future"],"candidate_count":report.get("candidate_count"),
              "attempts":len(report["candidate_trials"])},sort_keys=True),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: g2_werkzeug_guard_genesis_v1.py FRESH_OUTPUT")
    main(Path(sys.argv[1]).resolve())
