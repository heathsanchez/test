#!/usr/bin/env python3
"""Fail-closed admission of a separately qualified native semantic witness.

The original defect-finding method belongs to the evidence producer, not this
adapter. The host must supply an independently pinned digest of its evidence
manifest; PR-controlled files/metadata cannot select the trust anchor.
"""
import hashlib
import json
from pathlib import Path
import re

HEX64 = re.compile(r"^[0-9a-f]{64}$")
TEST_RUN = re.compile(r"(?m)^=== RUN   ([A-Za-z0-9_]+)")
FAIL = re.compile(r"(?m)^--- FAIL: ")
PASS = re.compile(r"(?m)^--- PASS: ")
LOGS = ("original", "candidate_patch", "removed_patch")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def admit(repo, pr, base, head, changed, changed_lines, root, manifest_digest):
    """Return (findings, typed status); no incoming PR can grant authority."""
    if not root:
        return [], {"status": "NOT_CONFIGURED"}
    if not isinstance(manifest_digest, str) or not HEX64.fullmatch(manifest_digest):
        return [], {"status": "UNKNOWN_MISSING_HOST_TRUST_ANCHOR"}
    try:
        root = Path(root)
        manifest_bytes = (root / "manifest.json").read_bytes()
        if sha(manifest_bytes) != manifest_digest:
            return [], {"status": "UNKNOWN_UNTRUSTED_MANIFEST_DIGEST"}
        m = json.loads(manifest_bytes)
        if m.get("schema") != "mgcheck-trusted-native-witness-v1":
            return [], {"status": "UNKNOWN_EVIDENCE_SCHEMA"}
        nwo = pr.get("nwo") or str(pr.get("repo", "")).removeprefix("https://github.com/")
        expected = {"repo": nwo, "pr_number": int(pr["pr_number"]),
                    "base": base, "head": head}
        if m.get("subject") != expected:
            return [], {"status": "UNKNOWN_OTHER_SOURCE_SUBJECT"}
        detail = m["finding"]
        path = detail["file"]
        if (not isinstance(path, str) or path not in changed or
                path.startswith("/") or ".." in Path(path).parts):
            return [], {"status": "UNKNOWN_UNCHANGED_FILE"}
        line = detail["line"]
        if type(line) is not int or line < 1:
            return [], {"status": "UNKNOWN_INVALID_LINE"}
        source_bytes = (repo / path).read_bytes()
        if line > len(source_bytes.splitlines()):
            return [], {"status": "UNKNOWN_LINE_OUTSIDE_SOURCE"}
        if line not in changed_lines(repo, base, head, path):
            return [], {"status": "UNKNOWN_NOT_IN_CHANGED_HUNK"}
        e = m["evidence"]
        if sha(source_bytes) != e.get("original_source_sha256"):
            return [], {"status": "UNKNOWN_SOURCE_BYTES_CHANGED"}
        native = (root / "receipt.json").read_bytes()
        if sha(native) != e.get("native_receipt_sha256"):
            return [], {"status": "UNKNOWN_NATIVE_REPORT_CHANGED"}
        receipt = json.loads(native)
        if (receipt.get("source_head") != head or
                receipt.get("original_sha256") != sha(source_bytes) or
                receipt.get("test_sha256") != e.get("native_test_sha256") or
                receipt.get("golden_reference_used") is not False or
                receipt.get("final_source_restored") is not True or
                receipt.get("fixture_removed") is not True):
            return [], {"status": "UNKNOWN_NATIVE_REPORT_SCOPE"}
        arms = receipt.get("arm")
        if (not isinstance(arms, list) or len(arms) != 3 or
                [x.get("name") for x in arms] != list(LOGS)):
            return [], {"status": "UNKNOWN_NATIVE_ARMS"}
        test_name = e.get("native_test_name")
        if not isinstance(test_name, str) or not re.fullmatch(r"Test[A-Za-z0-9_]+", test_name):
            return [], {"status": "UNKNOWN_NATIVE_TEST"}
        for item, label in zip(arms, LOGS):
            needed = "PASS" if label == "candidate_patch" else "FAIL"
            if item.get("actual") != needed or item.get("expected") != needed:
                return [], {"status": "UNKNOWN_NATIVE_OUTCOME_CONFLICT"}
            if bool(item.get("exit") == 0) != (needed == "PASS"):
                return [], {"status": "UNKNOWN_NATIVE_EXIT_CONFLICT"}
            payload = (root / (label + ".log")).read_bytes()
            if sha(payload) != e.get("log_sha256", {}).get(label):
                return [], {"status": "UNKNOWN_NATIVE_LOG_DIGEST"}
            content = payload.decode("utf-8", "replace")
            if test_name not in TEST_RUN.findall(content):
                return [], {"status": "UNKNOWN_TEST_NOT_EXECUTED"}
            if needed == "PASS" and not PASS.search(content):
                return [], {"status": "UNKNOWN_NATIVE_NO_PASS"}
            if needed == "FAIL" and not FAIL.search(content):
                return [], {"status": "UNKNOWN_NATIVE_NO_FAIL"}
        message = detail.get("message")
        if not isinstance(message, str) or not message.strip():
            return [], {"status": "UNKNOWN_NO_ACTIONABLE_CLAIM"}
        return [{
            "file": path, "start_line": line, "end_line": line,
            "message": message.strip()[:1500], "producer": "mathgraph-native-receipt"
        }], {
            "status": "WARRANTED_BOUNDED_SUBJECT_BOUND_NATIVE_WITNESS",
            "native_receipt_sha256": e["native_receipt_sha256"],
            "source_head": head, "authority": "HOST_PINNED_RECEIPT",
            "limits": "human-authored witness/patch; targeted native tests only"
        }
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError):
        return [], {"status": "UNKNOWN_INVALID_NATIVE_EVIDENCE"}
