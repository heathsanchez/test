#!/usr/bin/env python3
"""Train exactly one bounded source-neutral operation on the exposed first failure.

No code path fetches, reads, tests or inspects the protected future. A repaired
training source is not cross-source G2, even if all controls pass.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as native
from research.unified_consequence_runtime import g2_context_fallback_operator_v1 as method

HERE = Path(__file__).resolve().parents[2]
U = "research/unified_consequence_runtime/"
PROTOCOL_COMMIT = "de234c7e180467bbb0b957cac2016263bf80920b"
METHOD_COMMIT = "6fbfa0a633439f0eb5c8e9c55726f2b053e1bdd1"
SOURCE_SHA = "02c0bbdf7c9254021b10ce296e8e9545cd60779b94053c4cf595790b868a47fd"
ROLE_COMMIT = "57c400ea49881e440f7895acaeebeee5854363e3"
MAX_NATIVE = 12

def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def git_show(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(HERE), "show",
                                    f"{commit}:{path}"], timeout=45)

def manifest():
    path = U + "G2_NATIVE_FIRST_FAIL_POOL_V2_ROLE_FREEZE.json"
    frozen = git_show(ROLE_COMMIT, path)
    if (HERE / path).read_bytes() != frozen:
        raise RuntimeError("ROLE_FREEZE_CHANGED")
    frozen_protocol = git_show(PROTOCOL_COMMIT, U + "G2_CROSS_SOURCE_CONSEQUENCE_LAW_V1_FROZEN_PROTOCOL.md")
    if (HERE / U / "G2_CROSS_SOURCE_CONSEQUENCE_LAW_V1_FROZEN_PROTOCOL.md").read_bytes() != frozen_protocol:
        raise RuntimeError("PROTOCOL_CHANGED")
    frozen_method = git_show(METHOD_COMMIT, U + "g2_context_fallback_operator_v1.py")
    if (HERE / U / "g2_context_fallback_operator_v1.py").read_bytes() != frozen_method:
        raise RuntimeError("METHOD_CHANGED")
    roles = json.loads(frozen)
    assert len(roles["sealed_futures"]) == 1
    return roles, sha(frozen_method)

def junit(path):
    if not path.exists():
        return {"tests": 0, "failures": 0, "errors": 1, "skipped": 0}
    cases = list(ET.parse(path).getroot().iter("testcase"))
    return {"tests": len(cases), "failures": sum(any(x.tag == "failure" for x in case) for case in cases),
            "errors": sum(any(x.tag == "error" for x in case) for case in cases),
            "skipped": sum(any(x.tag == "skipped" for x in case) for case in cases)}

def run(py: Path, world: Path, nodes: list[str], dest: Path, timeout=120):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise RuntimeError("DUPLICATE_NATIVE_INVOCATION")
    dest.mkdir()
    xml = dest / "native.xml"
    argv = [str(py), "-m", "pytest", "-q", "--junitxml=" + str(xml), *nodes]
    start = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=world, capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        stdout, stderr, rc, reason = p.stdout, p.stderr, p.returncode, "EXECUTED"
    except subprocess.TimeoutExpired as ex:
        stdout = (ex.stdout or b"").decode(errors="replace") if isinstance(ex.stdout, bytes) else (ex.stdout or "")
        stderr = (ex.stderr or b"").decode(errors="replace") if isinstance(ex.stderr, bytes) else (ex.stderr or "")
        rc, reason = 124, "TIMEOUT"
    (dest / "stdout.log").write_text(stdout)
    (dest / "stderr.log").write_text(stderr)
    rec = {"status":reason,"returncode":rc,"counts":junit(xml),
           "seconds":round(time.monotonic()-start,3),"args":nodes,
           "stdout_sha256":sha(stdout.encode()),"stderr_sha256":sha(stderr.encode())}
    (dest / "RESULT.json").write_text(json.dumps(rec, indent=2, sort_keys=True)+"\n")
    return rec

def exactly(r, pass_count, fail_count, zero_skips=True):
    c = r["counts"]
    return (r["status"] == "EXECUTED" and r["returncode"] == (0 if fail_count==0 else 1)
            and c["tests"] == pass_count + fail_count and c["failures"] == fail_count
            and c["errors"] == 0 and (not zero_skips or c["skipped"] == 0))

def working_diff(world, production, test, patched=False):
    p = subprocess.run(["git","-C",str(world),"diff","--name-only"],
                       capture_output=True,text=True,timeout=30,check=True)
    expected = [test, production] if patched else [test]
    return sorted(p.stdout.splitlines()) == sorted(expected)

def main(out: Path):
    out.mkdir(parents=True, exist_ok=False)
    report = {"schema":"G2_EXPOSED_WERKZEUG_TRAINING_V1","scientific_scope":"TRAINING_ONLY",
              "future":"SEALED_UNOPENED","future_repo_access":"NOT_PERFORMED",
              "G2":"UNKNOWN","status":"UNKNOWN_ENVIRONMENT", "candidates_tested":0}
    started = time.monotonic()
    try:
        roles, method_sha = manifest()
        report["method_source_sha256"] = method_sha
        report["method_freeze_commit"] = METHOD_COMMIT
        report["protocol_freeze_commit"] = PROTOCOL_COMMIT
        method.self_test()
        task = roles["training_candidates"][0]
        assert task["repo"] == "pallets/werkzeug" and task["pr"] == 3215
        orig = native.one(task, 0, out / "admission")
        report["native_admission"] = orig
        if orig["status"] != "ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE":
            report["status"] = "UNKNOWN_NO_REPRODUCED_NATIVE_TRAINING_FAILURE"
            return report
        world = Path(orig["work_dir"])
        py = Path(orig["interpreter"])
        production = task["production"]
        original = (world / production).read_bytes()
        if sha(original) != SOURCE_SHA or orig["source_sha256"] != SOURCE_SHA:
            raise RuntimeError("SOURCE_SHA_MISMATCH")
        nodes = orig["protected_nodes"]
        report["protected_nodes"] = nodes
        if len(nodes) != 2 or orig["native"]["counts"] != {"tests":2,"failures":1,"errors":0,"skipped":0}:
            report["status"] = "UNKNOWN_BASELINE_PROTECTED_COUNTS"
            return report
        if not working_diff(world, production, task["author_test"]):
            raise RuntimeError("DIRTY_BASE_BEYOND_AUTHOR_TEST")
        report["native_observation"] = method.observation(
            (orig["native"].get("stdout_tail") or "") + (orig["native"].get("stderr_tail") or ""))
        candidates = method.generate(original)
        report["candidate_count"] = len(candidates)
        report["candidate_catalogue"] = [
            {key:c[key] for key in ("method","line","context","prefix","original_sha256","patched_sha256")}
            for c in candidates]
        if not candidates:
            report["status"] = "REJECTED_NO_LICENSED_CONTEXT_FALLBACK_CANDIDATES"
            return report
        report["status"] = "REJECTED_NO_QUALIFIED_TRAINING_REPAIR"
        results = []
        for i,c in enumerate(candidates[:MAX_NATIVE]):
            rec = {key:c[key] for key in ("method","line","context","prefix","patched_sha256")}
            try:
                (world / production).write_bytes(c["source"])
                assert sha((world / production).read_bytes())==c["patched_sha256"]
                if not working_diff(world, production, task["author_test"], patched=True):
                    raise RuntimeError("CANDIDATE_CHANGED_OTHER_TRACKED_SOURCE")
                first = run(py, world, nodes, out / f"candidate-{i:02d}" / "protected-a")
                rec["protected_a"]=first
                rec["status"]="REJECTED_CANDIDATE_NATIVE"
                if not exactly(first,2,0):
                    results.append(rec)
                    continue
                second = run(py, world, nodes, out / f"candidate-{i:02d}" / "protected-b")
                rec["protected_b"]=second
                if not exactly(second,2,0):
                    results.append(rec)
                    continue
                full = run(py, world, [task["author_test"]], out / f"candidate-{i:02d}" / "full-original-author-file")
                rec["full_author_file"]=full
                if (full["returncode"] != 0 or full["counts"]["failures"] or
                    full["counts"]["errors"] or full["counts"]["tests"] <= 2):
                    results.append(rec)
                    continue
                (world / production).write_bytes(original)
                withdrawn = run(py, world, nodes, out / f"candidate-{i:02d}" / "physical-withdrawal")
                rec["withdrawal"]=withdrawn
                if not exactly(withdrawn,1,1):
                    rec["status"]="UNKNOWN_WITHDRAWAL_FAILED"
                    results.append(rec)
                    continue
                (world / production).write_bytes(c["source"])
                restored = run(py, world, nodes, out / f"candidate-{i:02d}" / "byte-restoration")
                rec["restoration"]=restored
                if not exactly(restored,2,0) or sha((world / production).read_bytes()) != c["patched_sha256"]:
                    rec["status"]="UNKNOWN_RESTORATION_FAILED"
                    results.append(rec)
                    continue
                rec["status"]="WARRANTED_BOUNDED_TRAINING_REPAIR"
                report["selected_operator"]=rec
                report["status"]="WARRANTED_BOUNDED_TRAINING_REPAIR_FUTURE_SEALED"
                results.append(rec)
                break
            finally:
                (world / production).write_bytes(original)
                if sha((world / production).read_bytes())!=SOURCE_SHA:
                    raise RuntimeError("TRAINING_WORKTREE_NOT_RESTORED")
                if not working_diff(world, production, task["author_test"]):
                    raise RuntimeError("TRAINING_WORKTREE_CLEANUP_FAILURE")
        report["candidates_tested"]=len(results)
        report["candidate_results"]=results
        return report
    except Exception as ex:
        report["status"]="UNKNOWN_ENVIRONMENT"
        report["error"]=type(ex).__name__+": "+str(ex)[:500]
        report["traceback"]=traceback.format_exc(limit=8)[-2400:]
        return report
    finally:
        report["wall_seconds"]=round(time.monotonic()-started,3)
        (out/"RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
        print("TRAINING_STATUS",report["status"],"FUTURE",report["future"],"G2",report["G2"],flush=True)
        print("SUMMARY",json.dumps({k:report.get(k) for k in ("status","candidate_count","candidates_tested","future","G2","error")},sort_keys=True),flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: g2_werkzeug_train_v1.py EMPTY_OUTPUT_DIRECTORY")
    main(Path(sys.argv[1]).resolve())
