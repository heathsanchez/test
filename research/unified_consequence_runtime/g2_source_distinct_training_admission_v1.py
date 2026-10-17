#!/usr/bin/env python3
"""Admission of an authentic, author-protected external native failure.

No method search, G2 promotion, future source read or side-effect authority.
The PR/pins and source selection were committed before target source access.
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

from research.unified_consequence_runtime import typed_native_authority_v6 as native

HERE = Path(__file__).resolve().parent
POOL = HERE / "G2_SOURCE_DISTINCT_POOL_V1.json"
FREEZE = "8b6e60a22c659d81533e61facc6d9a008054d407"
EXPECTED_POOL_COMMIT = "b90328c2315bd07d30bf7ddf05711e7431589aaf"
EXPECTED_ROLE = "agronholm/anyio"
REQUIRED = (
    "tests/test_pytest_plugin.py::test_hypothesis_multiple_backends",
    "tests/test_pytest_plugin.py::test_hypothesis_multiple_backends_in_class",
)


def git(repo, *args, input=None):
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], input=input, stderr=subprocess.PIPE
    )


def h(raw):
    return hashlib.sha256(raw).hexdigest()


def check_equal(actual, expected, label):
    if actual != expected:
        raise ValueError(label + ": expected " + str(expected) + ", got " + str(actual))


def load_pool(research):
    # Read the immutable Git object, not an uncommitted override.
    raw = git(research, "show", EXPECTED_POOL_COMMIT + ":" + str(
        POOL.relative_to(research)))
    check_equal(raw, POOL.read_bytes(), "FROZEN_POOL_CURRENT_BYTES_DIFFER")
    plan = json.loads(raw)
    check_equal(plan["prequery_source_commit"], FREEZE, "PREQUERY_PARENT_CHANGED")
    check_equal(plan["case_pool"][0]["repo"], EXPECTED_ROLE, "ROLE_CHANGED")
    check_equal(len(plan["case_pool"]), 2, "POOL_COUNT_CHANGED")
    old = "research/unified_consequence_runtime/G2_SOURCE_DISTINCT_PREQUERY_V1.json"
    check_equal(git(research, "show", FREEZE + ":" + old),
                git(research, "show", "HEAD:" + old), "FROZEN_PREQUERY_CHANGED")
    return plan


def run(repo, output):
    started = time.monotonic()
    result = {
        "schema": "UDM_SOURCE_DISTINCT_TRAINING_NATIVE_ADMISSION_V1",
        "status": "UNKNOWN_NOT_EXECUTED",
        "source_subject": EXPECTED_ROLE,
        "source_qualification": "FROZEN_EXTERNAL_AUTHOR_TEST_ONLY",
        "native_calls": 0,
        "G2": "UNKNOWN", "G3": "UNKNOWN", "G4": "UNKNOWN",
        "G5": "UNKNOWN", "G6": "UNKNOWN",
        "heldout_source": "UNOPENED",
        "method_acquisition": "NOT_EXECUTED",
        "agent_comparator": "NOT_EXECUTED",
        "informed_ledger_comparator": "NOT_EXECUTED",
        "external_permission": "NONE",
    }
    output.mkdir(parents=True, exist_ok=False)
    research = HERE.parents[1].resolve()
    repo = Path(repo).resolve()
    try:
        assert repo.is_dir() and repo != research and not repo.is_relative_to(research)
        plan = load_pool(research)
        task = plan["case_pool"][0]
        base, head = task["base"], task["head"]
        check_equal(git(repo, "rev-parse", "HEAD").decode().strip(),
                    base, "BASE_COMMIT_MISMATCH")
        check_equal(git(repo, "rev-parse", "HEAD^{tree}").decode().strip(),
                    task["base_tree"], "BASE_TREE_MISMATCH")
        check_equal(git(repo, "status", "--porcelain").strip(), b"", "DIRTY_BASE_SOURCE")
        # Read only the precommitted author test objects, never head production.
        paths = []
        for row in task["head_author_tests"]:
            path = row["path"]
            assert path.startswith("tests/") and path.endswith(".py")
            blob = git(repo, "show", head + ":" + path)
            check_equal(git(repo, "hash-object", "--stdin", input=blob).decode().strip(),
                        row["head_blob"], "WRONG_AUTHOR_TEST_BLOB")
            original = row["base_blob"]
            if original is not None:
                check_equal(git(repo, "rev-parse", base + ":" + path).decode().strip(),
                            original, "BASE_AUTHOR_TEST_BLOB_CHANGED")
            dest = repo / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.is_symlink():
                raise ValueError("TEST_SOURCE_SYMLINK_FORBIDDEN")
            dest.write_bytes(blob)
            paths.append(path)
        # No author head production source was requested.
        for row in task["production"]:
            check_equal(git(repo, "rev-parse", base + ":" + row["path"]).decode().strip(),
                        row["base_blob"], "BASE_PRODUCTION_BLOB_CHANGED")
        git(repo, "add", "--", *paths)
        git(repo, "-c", "user.name=UDM Local Test Overlay",
            "-c", "user.email=local-test-only@invalid.example",
            "commit", "-m", "Detached original source plus frozen author tests only")
        augmented = git(repo, "rev-parse", "HEAD").decode().strip()
        check_equal(git(repo, "rev-parse", "HEAD^").decode().strip(),
                    base, "OVERLAY_PARENT_CHANGED")
        modified = git(repo, "diff", "--name-only", base, augmented).decode().splitlines()
        check_equal(sorted(modified), sorted(paths), "OVERLAY_CHANGED_PRODUCTION")
        check_equal(git(repo, "status", "--porcelain").strip(), b"", "DIRTY_OVERLAY")
        for row in task["head_author_tests"]:
            check_equal(git(repo, "rev-parse", augmented + ":" + row["path"]).decode().strip(),
                        row["head_blob"], "OVERLAY_TEST_OBJECT_CHANGED")
        for row in task["production"]:
            check_equal(git(repo, "rev-parse", augmented + ":" + row["path"]).decode().strip(),
                        row["base_blob"], "OVERLAY_PRODUCTION_OBJECT_CHANGED")
        result["source"] = {
            "original_base_commit": base, "author_head_commit_metadata_only": head,
            "author_test_paths": paths, "local_test_only_overlay": augmented,
            "production_files_unchanged": True,
            "original_base_tree": task["base_tree"],
            "frozen_author_test_git_oids": {
                row["path"]: row["head_blob"] for row in task["head_author_tests"]
            }
        }
        source = native.stage(repo, augmented, output / "stage")
        result["stage"] = source
        trials = []
        for i in range(2):
            t0 = time.monotonic()
            receipt = native.run_protected(
                repo, augmented, output / "stage", required=REQUIRED,
                interpreter=sys.executable, timeout=120,
                paths=["tests/test_pytest_plugin.py"]
            )
            trials.append(receipt)
            result["native_calls"] += receipt.get("native_calls", 0)
            (output / ("native-" + str(i + 1) + ".json")).write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            result["native_" + str(i + 1) + "_wall_seconds"] = time.monotonic() - t0
            if receipt["status"] != "FAIL_NATIVE_PROTECTED":
                result["status"] = "UNKNOWN_NATIVE_PROTECTED_FAILURE_NOT_REPLAYED"
                break
        if len(trials) == 2 and all(x["status"] == "FAIL_NATIVE_PROTECTED" for x in trials):
            first, second = trials
            checks = ("required", "selected", "executed", "deselected",
                      "imported_project_files", "typed_manifest_sha256")
            if not all(first.get(key) == second.get(key) for key in checks):
                result["status"] = "UNKNOWN_NATIVE_REPLAY_DISAGREEMENT"
            elif any(any(node == prefix or node.startswith(prefix + "[")
                         for node in x.get("executed", [])) is False
                     for x in trials for prefix in REQUIRED):
                result["status"] = "UNKNOWN_PROTECTED_NOT_EXECUTED"
            elif any(x.get("deselected") or x.get("junit", {}).get("skipped")
                     or x.get("junit", {}).get("errors") for x in trials):
                result["status"] = "UNKNOWN_PARTIAL_TEST_AUTHORITY"
            else:
                result["status"] = "WARRANTED_BOUNDED_AUTHENTIC_NATIVE_PROTECTED_FAILURE"
        post = native.verify_stage(repo, augmented, output / "stage")
        result["stage_after_replay"] = post
        if post.get("status") != "PASS_TYPED_STAGE_IDENTITY":
            result["status"] = "UNKNOWN_STAGED_SOURCE_INTEGRITY"
        # Source-withdrawal negative: any byte change must fail independent stage authentication.
        protected = output / "stage/tests/test_pytest_plugin.py"
        pristine = protected.read_bytes()
        try:
            protected.write_bytes(pristine + b"\n# invalid forged test source\n")
            try:
                native.verify_stage(repo, augmented, output / "stage")
            except ValueError:
                result["mutated_test_source_control"] = "REJECTED"
            else:
                result["mutated_test_source_control"] = "WRONGLY_ACCEPTED"
                result["status"] = "UNKNOWN_MUTATION_CONTROL_FAILURE"
        finally:
            protected.write_bytes(pristine)
        result["restored_stage"] = native.verify_stage(repo, augmented, output / "stage")
        if result["mutated_test_source_control"] != "REJECTED":
            result["status"] = "UNKNOWN_MUTATION_CONTROL_FAILURE"
        return result
    except Exception as error:
        result["status"] = "UNKNOWN_ADMISSION_APPARATUS"
        result["obstruction"] = type(error).__name__ + ": " + str(error)
        result["traceback"] = traceback.format_exc(limit=8)[-2500:]
        return result
    finally:
        result["wall_seconds"] = time.monotonic() - started
        (output / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: admission.py ORIGINAL_GIT_REPOSITORY FRESH_OUTPUT")
    report = run(sys.argv[1], Path(sys.argv[2]).absolute())
    print(json.dumps({"status": report["status"], "native_calls": report["native_calls"],
                      "G2": report["G2"], "heldout_source": report["heldout_source"]},
                     sort_keys=True))
    raise SystemExit(0 if report["status"] ==
                     "WARRANTED_BOUNDED_AUTHENTIC_NATIVE_PROTECTED_FAILURE" else 2)
