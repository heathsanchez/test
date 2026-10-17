#!/usr/bin/env python3
"""Fail-closed admission only. Does not run developmental science or promote G2."""
import hashlib
import json
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

source = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
pin = json.loads((out / "pin.json").read_text())
def call(cmd, cwd=source):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=300)

identity = call(["git", "rev-parse", "HEAD"])
assert identity.returncode == 0 and identity.stdout.strip() == pin["sha"], "SOURCE_IDENTITY_MISMATCH"
assert call(["git", "status", "--porcelain"]).stdout.strip() == "", "DIRTY_SOURCE"
testdir = source / "tests"
assert testdir.is_dir(), "MISSING_NATIVE_TEST_DIRECTORY"
cmd = [sys.executable, "-m", "pytest", "-q", "--junitxml=" + str(out / "native.xml"), str(testdir)]
try:
    result = call(cmd)
except subprocess.TimeoutExpired as exc:
    (out / "admission.json").write_text(json.dumps({"status":"UNKNOWN_APPARATUS_TIMEOUT","command":cmd}, indent=2))
    raise SystemExit("UNKNOWN_APPARATUS_TIMEOUT") from exc
(out / "native.stdout").write_text(result.stdout)
(out / "native.stderr").write_text(result.stderr)
summary = {"status":"UNKNOWN_APPARATUS", "source_sha":pin["sha"], "command":cmd,
           "returncode":result.returncode, "tests":0, "failures":0, "errors":0, "skipped":0}
try:
    root = ET.parse(out / "native.xml").getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    # Use testcase nodes to avoid counting aggregate suite twice.
    cases = list(root.iter("testcase"))
    summary["tests"] = len(cases)
    summary["failures"] = sum(bool(list(c.iter("failure"))) for c in cases)
    summary["errors"] = sum(bool(list(c.iter("error"))) for c in cases)
    summary["skipped"] = sum(bool(list(c.iter("skipped"))) for c in cases)
except (ET.ParseError, OSError):
    summary["status"] = "UNKNOWN_APPARATUS_NO_JUNIT"
else:
    executed = summary["tests"] - summary["skipped"]
    if result.returncode == 0 and executed > 0 and summary["failures"] == summary["errors"] == 0:
        summary["status"] = "ADMITTED_NATIVE_TESTS_ONLY"
    else:
        summary["status"] = "UNKNOWN_APPARATUS_OR_NATIVE_FAILURE"
summary["source_manifest_sha256"] = hashlib.sha256((out / "pin.json").read_bytes()).hexdigest()
(out / "admission.json").write_text(json.dumps(summary, sort_keys=True, indent=2))
print(json.dumps(summary, sort_keys=True))
if summary["status"] != "ADMITTED_NATIVE_TESTS_ONLY":
    raise SystemExit(1)
