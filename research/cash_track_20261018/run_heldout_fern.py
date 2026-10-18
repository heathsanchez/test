#!/usr/bin/env python3
"""Source-pinned retrospective Go oracle test on a new, external repository.

Protocol freeze: bb? (see HELDOUT_FERN_PROTOCOL.md at source ancestor 3ec172aa).
This script is human-written after inspecting the published production patch.
It does not execute a model, discover a new upstream defect or prove repair quality.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEST = ROOT / "heldout_fern_outage_test.go"
UPSTREAM = "https://github.com/OllyInsurance/fern-platform.git"
BASE = "ee843f4babd4c05e819aa86701e409b58e328c66"
HEAD = "ddff2c82b9a0124ccec83d079cf9877f4479e914"
TEST_NAME = "TestCashtrackHeldoutOutageEvidence"
CASES = {
    "step_declared_only": True,
    "step_without_declared_outage": False,
    "declared_step_plus_unexcused_product_check": False,
    "ordinary_declared_check": True,
    "declared_step_with_an_unbound_check": False,
    "unbound_step_plus_informational_outage_notice": False,
    "declared_check_plus_unexcused_check": False,
}
INPUTS = {
    "step_declared_only": "STEP FAIL consent dispatch interrupted DURING DECLARED OUTAGE consent_cut\n",
    "step_without_declared_outage": "STEP FAIL consent dispatch interrupted (product API response mismatch)\n",
    "declared_step_plus_unexcused_product_check": "STEP FAIL consent dispatch interrupted DURING DECLARED OUTAGE consent_cut\nCHECK FAIL Equal want=200 got=201\n",
    "ordinary_declared_check": "CHECK FAIL Equal want=200 got=503 DURING DECLARED OUTAGE consent_cut\n",
    "declared_step_with_an_unbound_check": "STEP FAIL snapshot blocked DURING DECLARED OUTAGE other_cut\nCHECK FAIL unexpected business-state result\n",
    "unbound_step_plus_informational_outage_notice": "STEP FAIL snapshots mismatched\nNOTICE DURING DECLARED OUTAGE known_cut\n",
    "declared_check_plus_unexcused_check": "CHECK FAIL retry DURING DECLARED OUTAGE known_cut\nCHECK FAIL wrong invoice amount\n",
}
GO_COMMAND = ["go", "test", "-v", "-count=1", "./internal/api", "-run", "^TestCashtrackHeldoutOutageEvidence$"]


def shell(argv, *, cwd=None, seconds=180):
    env = dict(os.environ)
    env.update({"GIT_TERMINAL_PROMPT": "0", "GOTOOLCHAIN": "local", "GIT_CONFIG_NOSYSTEM": "1"})
    try:
        p = subprocess.run(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, timeout=seconds, check=False)
        return p.returncode, p.stdout
    except subprocess.TimeoutExpired as ex:
        so = ex.stdout or b""
        if isinstance(so, bytes):
            so = so.decode("utf-8", "replace")
        return 124, so + "\nTIMED_OUT"
    except OSError as ex:
        return 127, f"LAUNCH_ERROR {ex}"


def digest(b):
    return hashlib.sha256(b).hexdigest()


def verify_source(path, expected):
    # Source identifier is the *actual* exact source revision, not a claimed
    # branch label or a commit guessed from a PR summary.
    rc, out = shell(["git", "rev-parse", "HEAD"], cwd=path, seconds=10)
    return rc == 0 and out.strip() == expected


def verify_authorized_tree(root: Path, expected_sha: str, fixture_present: bool, fixture_digest: str):
    """Exact source-head plus clean tracked tree and single exact test overlay.

    A valid HEAD alone does NOT prove that native Go executed clean source.
    """
    if not verify_source(root, expected_sha):
        return False
    rc, status = shell(["git", "status", "--porcelain=v1", "--untracked-files=all"],
                       cwd=root, seconds=15)
    if rc:
        return False
    observed = sorted(x for x in status.splitlines() if x)
    overlay_name = "internal/api/cashtrack_outage_test.go"
    authorized = ["?? " + overlay_name] if fixture_present else []
    if observed != authorized:
        return False
    fixture_path = root / overlay_name
    if fixture_present:
        return fixture_path.is_file() and digest(fixture_path.read_bytes()) == fixture_digest
    return not fixture_path.exists()


def clone_sha(parent: Path, tag: str, expected: str):
    root = parent / tag
    root.mkdir(parents=True)
    for cmd in (
        ["git", "init", "-q"],
        ["git", "remote", "add", "origin", UPSTREAM],
        ["git", "-c", "protocol.version=2", "fetch", "--no-tags", "--depth=1", "origin", expected],
        ["git", "checkout", "-q", "--detach", "FETCH_HEAD"],
    ):
        rc, log = shell(cmd, cwd=root, seconds=180)
        if rc:
            raise RuntimeError(f"Git {tag}: {cmd} returned {rc}; {log[-1600:]}")
    if not verify_source(root, expected):
        raise RuntimeError(f"Source SHA fail closed: {tag} expected {expected}")
    return root


def run_go(root: Path, name: str, out: Path):
    rc, log = shell(GO_COMMAND, cwd=root, seconds=540)
    (out / f"{name}.log").write_text(log, encoding="utf-8")
    # Presence of each actual native subtest is required: "go test" exit=0
    # without matching tests is NOT a positive observation.
    seen = {}
    executed = set()
    for line in log.splitlines():
        match_start = re.search(r"^\s*=== RUN\s+" + TEST_NAME + r"/([A-Za-z0-9_]+)\s*$", line)
        if match_start:
            executed.add(match_start.group(1))
        match_end = re.search(r"^\s*--- (PASS|FAIL): " + TEST_NAME + r"/([A-Za-z0-9_]+)\s+\(", line)
        if match_end:
            if match_end.group(2) in seen:
                raise RuntimeError(f"Duplicate native test verdict: {match_end.group(2)}")
            seen[match_end.group(2)] = match_end.group(1)
    exact = set(CASES) == set(seen) == executed
    return {"returncode": rc, "named_all_executed": exact, "verdicts": seen,
            "log_sha256": digest(log.encode("utf-8")), "named_executed_count": len(executed)}


def policy_baselines():
    # These are runnable non-model baselines. They are *not* strong equal-info
    # coding agents. This table only tests the frozen scope distinction.
    checks_only = re.compile(r"CHECK FAIL\b[^\n]* DURING DECLARED OUTAGE \S+")
    scores = {}
    for name, rule in (
        ("literal_any_outage_mention", lambda x: "DURING DECLARED OUTAGE" in x),
        ("literal_check_only", lambda x: bool(checks_only.search(x))),
    ):
        pred = {key: rule(inp) for key, inp in INPUTS.items()}
        scores[name] = {"correct": sum(pred[k] == y for k, y in CASES.items()),
                        "total": len(CASES),
                        "false_outage": sorted(k for k, y in CASES.items() if not y and pred[k]),
                        "missed_outage": sorted(k for k, y in CASES.items() if y and not pred[k])}
    return scores


def main():
    output = ROOT / "out_heldout_fern"
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "protocol_freeze_commit": "3ec172aa162787d9acc0d7dad3aceeb994dfa6b5",
        "source_repository": "OllyInsurance/fern-platform",
        "source_pr": "https://github.com/OllyInsurance/fern-platform/pull/16",
        "base_sha": BASE,
        "head_sha": HEAD,
        "independent_test_sha256": digest(TEST.read_bytes()),
        "native_source_test": True,
        "strong_model_baseline_executed": False,
        "public_competition_submission": False,
        "frozen_named_cases": len(CASES),
        "baseline": policy_baselines(),
    }
    report["status"] = "UNKNOWN_SOURCE_OR_NATIVE"
    try:
        with tempfile.TemporaryDirectory(prefix="cashtrack_fern_") as temp:
            work = Path(temp)
            actual = {}
            for label, sha in (("base", BASE), ("head", HEAD)):
                root = clone_sha(work, label, sha)
                test_path = root / "internal" / "api" / "cashtrack_outage_test.go"
                if test_path.exists():
                    raise RuntimeError("External repo has preexisting named cashtrack test, refusing overwrite")
                shutil.copyfile(TEST, test_path)
                if digest(test_path.read_bytes()) != report["independent_test_sha256"]:
                    raise RuntimeError("Original fixture not byte-identical in both source revisions")
                tree_pre = verify_authorized_tree(
                    root, sha, True, report["independent_test_sha256"])
                if not tree_pre:
                    raise RuntimeError(f"Native {label} source tree unclean before execution")
                actual[label] = run_go(root, label, output)
                if not actual[label]["named_all_executed"]:
                    raise RuntimeError(f"Native {label} named 7/7 test execution missing")
                tree_post = verify_authorized_tree(
                    root, sha, True, report["independent_test_sha256"])
                actual[label]["source_tree_clean_before"] = tree_pre
                actual[label]["source_tree_clean_after"] = tree_post
                if not tree_post:
                    raise RuntimeError(f"Native {label} source tree dirty after execution")
                if label == "head":
                    code_path = root / "internal" / "api" / "coverage_verdict.go"
                    original_source_bytes = code_path.read_bytes()
                    code_path.write_bytes(original_source_bytes + b"\n// cashtrack-only source tamper control\n")
                    tracked_refused = (
                        verify_source(root, HEAD) and
                        not verify_authorized_tree(
                            root, HEAD, True, report["independent_test_sha256"]))
                    code_path.write_bytes(original_source_bytes)
                    restored_tracked = verify_authorized_tree(
                        root, HEAD, True, report["independent_test_sha256"])

                    original_fixture_bytes = test_path.read_bytes()
                    test_path.write_bytes(original_fixture_bytes + b"\n// cashtrack-only altered test control\n")
                    fixture_refused = (
                        verify_source(root, HEAD) and
                        not verify_authorized_tree(
                            root, HEAD, True, report["independent_test_sha256"]))
                    test_path.write_bytes(original_fixture_bytes)
                    restored_fixture = verify_authorized_tree(
                        root, HEAD, True, report["independent_test_sha256"])

                    alien = root / "internal" / "api" / "cashtrack_untrusted_overlay.go"
                    if alien.exists():
                        raise RuntimeError("Unexpected second overlay already present")
                    alien.write_text("package api\n", encoding="utf-8")
                    second_overlay_refused = (
                        verify_source(root, HEAD) and
                        not verify_authorized_tree(
                            root, HEAD, True, report["independent_test_sha256"]))
                    alien.unlink()
                    restored_single_overlay = verify_authorized_tree(
                        root, HEAD, True, report["independent_test_sha256"])
                    report["source_tree_controls"] = {
                        "dirty_tracked_source_same_head_refused": tracked_refused,
                        "tracked_source_restored": restored_tracked,
                        "mutated_frozen_test_same_head_refused": fixture_refused,
                        "test_bytes_restored": restored_fixture,
                        "extra_untracked_go_source_refused": second_overlay_refused,
                        "single_exact_overlay_restored": restored_single_overlay,
                    }
                    if not all(report["source_tree_controls"].values()):
                        raise RuntimeError("Dirty-source or test-byte falsification gate failed")
                    # Physically remove injected test. Go may exit 0 but this
                    # must be classified as no evidence, not a test pass.
                    test_path.unlink()
                    if not verify_authorized_tree(root, HEAD, False, report["independent_test_sha256"]):
                        raise RuntimeError("Post-removal source state is not clean")
                    removed = run_go(root, "head_removed_test", output)
                    if removed["named_executed_count"] != 0:
                        raise RuntimeError("Unexpected named test after physical deletion")
                    report["removed_test_control"] = {
                        "native_command_returncode": removed["returncode"],
                        "named_executed_count": removed["named_executed_count"],
                        "admission": "REFUSED_NO_EXECUTED_NAMED_TEST",
                    }
                    # source identity guards are physically exercised with both
                    # an actual checkout and a missing source reference.
                    report["source_identity_controls"] = {
                        "correct_source_admitted": verify_source(root, HEAD),
                        "wrong_sha_refused": not verify_source(root, BASE),
                        "missing_reference_refused": not verify_source(root / "source_reference_removed", HEAD),
                    }
            report["native"] = actual
            expected_pre = {k: ("FAIL" if k == "step_declared_only" else "PASS") for k in CASES}
            expected_post = {k: "PASS" for k in CASES}
            if actual["base"]["verdicts"] != expected_pre or actual["base"]["returncode"] == 0:
                raise RuntimeError("Base did not show exactly one frozen real regression failure")
            if actual["head"]["verdicts"] != expected_post or actual["head"]["returncode"] != 0:
                raise RuntimeError("Head did not satisfy all seven independent controls")
            if not all(report["source_identity_controls"].values()):
                raise RuntimeError("Original source-identity protected controls failed")
            if not all(report["source_tree_controls"].values()):
                raise RuntimeError("Strict exact-source authority was not qualified")
            report["status"] = "WARRANTED_BOUNDED_NATIVE_GO_DIFF_EXACT_TREE_V2"
            report["limitations"] = [
                "Test input grammar authored after reading the production-only patch, using frozen natural-language acceptance obligations",
                "Not a blind source-native method or new human-intent discovery: original contributor disclosed the issue",
                "No matched live LLM, Gemma, or coding agent inference; no benchmark-heldout model task",
                "Go source native envFault method tested: not complete UI/server/database integration",
                "CI platform, git fetch and Go toolchain remain trusted, not cryptographic external attestation",
            ]
    except Exception as ex:
        report["native_error"] = str(ex)
    (output / "heldout_metrics.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "WARRANTED_BOUNDED_NATIVE_GO_DIFF_EXACT_TREE_V2":
        sys.exit(3)


if __name__ == "__main__":
    main()
