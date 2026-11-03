"""Independent, fail-closed native RED/GREEN extraction on a pinned Go PR.

Scientific receipt is not the GitHub Actions job conclusion. A patch or PR title
is NEVER sent to the learner. Uses original source/native suite and test bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any

SHA = re.compile(r"[0-9a-f]{40}\Z")
TEST_FILE = re.compile(r"(?:[a-zA-Z0-9_.-]+/)*[a-zA-Z0-9_.-]+_test\.go\Z")
MAX_SECONDS = 360


def cmd(args: list[str], cwd: Path, *, timeout: int = MAX_SECONDS) -> dict[str, Any]:
    t = time.monotonic()
    try:
        p = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=timeout, check=False,
                           env={**os.environ, "GOTOOLCHAIN": "local"})
        return {"exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
                "elapsed_seconds": round(time.monotonic() - t, 3)}
    except subprocess.TimeoutExpired:
        return {"exit": 124, "stdout": "", "stderr": "UNKNOWN_TIMEOUT",
                "elapsed_seconds": round(time.monotonic()-t, 3)}
    except OSError as e:
        return {"exit": 125, "stdout": "", "stderr": f"UNKNOWN_OS_ERROR:{type(e).__name__}",
                "elapsed_seconds": round(time.monotonic()-t, 3)}


def decode_go_events(raw: str, code: int) -> dict[str, Any]:
    events = []
    malformed = 0
    for line in raw.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            malformed += 1
            continue
        if not isinstance(item, dict):
            malformed += 1
            continue
        events.append(item)
    passed = {x["Test"] for x in events if x.get("Action")=="pass" and isinstance(x.get("Test"),str)}
    failed = {x["Test"] for x in events if x.get("Action")=="fail" and isinstance(x.get("Test"),str)}
    ran = {x["Test"] for x in events if x.get("Action")=="run" and isinstance(x.get("Test"),str)}
    if code == 124:
        status = "UNKNOWN_TIMEOUT"
    elif malformed:
        status = "UNKNOWN_MALFORMED_TEST_STREAM"
    elif not ran or not (passed or failed):
        status = "UNKNOWN_ZERO_RECOGNIZED_TESTS"
    elif code == 0 and failed:
        status = "UNKNOWN_INCONSISTENT_GO_TEST_RUN"
    elif code == 0:
        status = "PASS_NONEMPTY"
    elif failed:
        status = "FAIL_NATIVE_ASSERTIONS"
    else:
        status = "UNKNOWN_SETUP_COMPILATION_OR_INFRASTRUCTURE"
    return {"status":status,"ran_count":len(ran),"passed_count":len(passed),
            "failed_count":len(failed),"failed_names":sorted(failed),
            "passed_names":sorted(passed),"malformed_lines":malformed}


def identity(repo: Path, sha: str) -> bool:
    if not SHA.fullmatch(sha):
        return False
    result = cmd(["git","rev-parse","HEAD"],repo,timeout=20)
    if result["exit"] or result["stdout"].strip()!=sha:
        return False
    return cmd(["git","status","--porcelain"],repo,timeout=20)["stdout"].strip()==""


def run_suite(path: Path, outdir: Path, name: str) -> dict[str, Any]:
    output = cmd(["go","test","-json","./..."], path)
    (outdir/(name+"-go-events.jsonl")).write_text(output["stdout"])
    (outdir/(name+"-go-stderr.txt")).write_text(output["stderr"])
    receipt = decode_go_events(output["stdout"],output["exit"])
    receipt.update({"exit":output["exit"],"elapsed_seconds":output["elapsed_seconds"]})
    return receipt


def qualify(repo: Path, base: str, head: str, test_file: str, outdir: Path) -> dict[str, Any]:
    repo=repo.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any]={"schema":"mathgraph.g2.author-native-redgreen.v1",
      "base_sha":base,"head_sha":head,"test_file":test_file,
      "status":"UNKNOWN_PRECONDITION","scientific_g2":"UNKNOWN","scientific_g3":"UNKNOWN"}
    if not SHA.fullmatch(base) or not SHA.fullmatch(head) or not TEST_FILE.fullmatch(test_file):
        receipt["status"]="UNKNOWN_INVALID_MANIFEST"
        return receipt
    if not (repo/".git").exists():
        receipt["status"]="UNKNOWN_SOURCE_GIT_IDENTITY"
        return receipt
    # Verify the immutable Git objects exist; no HEAD/test-file substitution.
    for sha in (base,head):
        c=cmd(["git","cat-file","-e",sha+"^{commit}"],repo,timeout=15)
        if c["exit"]:
            receipt["status"]="UNKNOWN_SOURCE_OBJECT_MISSING"
            return receipt
    with tempfile.TemporaryDirectory(prefix="udm-g2-native-") as temp:
        root=Path(temp)
        source=root/"base"
        fixed=root/"head"
        for where,sha in ((source,base),(fixed,head)):
            r=cmd(["git","-c","advice.detachedHead=false","worktree","add","--detach",str(where),sha],repo,timeout=60)
            if r["exit"]:
                receipt["status"]="UNKNOWN_WORKTREE_CHECKOUT"
                return receipt
        if not identity(source,base) or not identity(fixed,head):
            receipt["status"]="UNKNOWN_SOURCE_SHA_MISMATCH"
            return receipt
        a,b=source/test_file,fixed/test_file
        if not b.is_file():
            receipt["status"]="UNKNOWN_CONTRIBUTOR_TEST_FILE_MISSING"
            return receipt
        if a.exists() and not a.is_file():
            receipt["status"]="UNKNOWN_BASE_TEST_NOT_REGULAR"
            return receipt
        base_test_exists=a.is_file()
        original=a.read_bytes() if base_test_exists else b""
        contributed=b.read_bytes()
        receipt["base_test_existed"]=base_test_exists
        receipt["base_test_sha256"]=hashlib.sha256(original).hexdigest()
        receipt["head_test_sha256"]=hashlib.sha256(contributed).hexdigest()
        if original == contributed:
            receipt["status"]="UNKNOWN_NO_AUTHOR_TEST_CHANGE"
            return receipt
        # No head test body shown to the future proposer.
        receipt["original_base"]=run_suite(source,outdir,"pristine-base")
        receipt["head_contributor"]=run_suite(fixed,outdir,"contributor-head")
        if receipt["original_base"]["status"]!="PASS_NONEMPTY" or receipt["head_contributor"]["status"]!="PASS_NONEMPTY":
            receipt["status"]="UNKNOWN_ORIGINAL_SOURCE_SUITE"
            return receipt
        # Only author test-file replacement, including a newly added test file.
        # Never modify implementation or install a target-specific adapter.
        a.parent.mkdir(parents=True, exist_ok=True)
        a.write_bytes(contributed)
        receipt["base_transplant"]=run_suite(source,outdir,"author-test-on-base")
        if receipt["base_transplant"]["status"]!="FAIL_NATIVE_ASSERTIONS":
            receipt["status"]="UNKNOWN_NO_NATIVE_FAILING_ASSERTION"
            return receipt
        witness=set(receipt["base_transplant"]["failed_names"]) & set(receipt["head_contributor"]["passed_names"])
        if not witness:
            receipt["status"]="UNKNOWN_NO_SAME_TEST_HEAD_PASS"
            return receipt
        receipt["matched_failed_tests"]=sorted(witness)
        # Bounded learner input: only actual native assertion output, base source,
        # test title/source is NOT included; the author test file is hidden.
        lines=[]
        for line in (outdir/"author-test-on-base-go-events.jsonl").read_text().splitlines():
            try: item=json.loads(line)
            except ValueError: continue
            if (item.get("Action")=="output" and isinstance(item.get("Test"),str)
                    and item["Test"] in witness):
                lines.append(item.get("Output", ""))
        learner={"schema":"mathgraph.g2.native-residual-to-observer.v1",
                 "source_sha":base,"head_sha_hidden_from_learner":True,
                 "failing_tests":sorted(witness),
                 "native_assertion_output":"".join(lines)[-6000:],
                 "native_contract":"Author regression test fails against pinned pre-fix Go source and passes on pinned contributor source. Independent source observer must be generated separately without seeing author test body or fix."}
        (outdir/"learner-residual.json").write_text(json.dumps(learner,indent=2)+"\n")
        receipt["status"]="WARRANTED_BOUNDED_AUTHENTIC_AUTHOR_NATIVE_RED_GREEN"
        receipt["scientific_g2"]="UNKNOWN_OBSERVER_NOT_YET_CREATED"
        return receipt


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    ap.add_argument("--base",required=True)
    ap.add_argument("--head",required=True)
    ap.add_argument("--test-file",required=True)
    ap.add_argument("--output",required=True)
    ns=ap.parse_args()
    out=Path(ns.output).resolve()
    try:
        result=qualify(Path(ns.repo),ns.base,ns.head,ns.test_file,out)
    except Exception as e:
        result={"schema":"mathgraph.g2.author-native-redgreen.v1",
                "status":"UNKNOWN_UNHANDLED_APPARATUS_EXCEPTION",
                "type":type(e).__name__,"scientific_g2":"UNKNOWN"}
    out.mkdir(parents=True, exist_ok=True)
    (out/"qualification.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("NATIVE_ADMISSION",result["status"])
    print("AUTHOR_ASSERTION_WITNESS_COUNT",len(result.get("matched_failed_tests",[])))
    print("SCIENTIFIC_G2",result.get("scientific_g2","UNKNOWN"))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
