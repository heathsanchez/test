#!/usr/bin/env python3
"""Independent offline MathGraph Check receipt/preview requalification.

Uses the original GitHub Actions ZIP artifacts; never posts to GitHub or
requires network. Bounds: exact historical source-native tests on files inside
original artifacts, not author independence or current source freshness.
"""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
NATIVE = HERE / "mathgraph_native_11862929149.zip"
PREVIEW = HERE / "mathgraph_native_11864308701.zip"
EXPECTED = {
    NATIVE.name: "dfa66e486f8d669115f33deef9b3fd79c784e39161791bc1dcad7f349a4a20b5",
    PREVIEW.name: "8f1266d7f99231faafee879c767148fc903982978f58adf5897ead1a5f1212e5",
}
RECEIPT_DIGEST = "e5f970c699588a01bf1e773c48e3882a1d91ce3dfff4db98bb9a576d9b381562"
PINNED_BASE = "2a10e721ff645865c45c344333b1934f34c45b41"
PINNED_HEADS = {
    158: "7fab327e61518fa607753cd022d87ef9d243bbf4",
    155: "a70ba812e1b6e40a6ce4652fb830589030e461d0",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(test: bool, code: str):
    if not test:
        raise ValueError(code)


def verify_receipt(rec: dict, prev: dict) -> None:
    require(rec.get("schema") == "metalogic.real-external-pr-native-evidence.v1", "SCHEMA")
    require(rec.get("action_authorization") == "NONE", "FALSE_AUTHORIZATION")
    require(rec.get("code_repair_generated") == "NO", "FALSE_REPAIR")
    require(rec.get("method_generator_software_authorship") == "HUMAN_WRITTEN", "FALSE_AUTONOMY")
    require(rec.get("scientific_L7") == "UNKNOWN", "FALSE_L7")
    require(rec.get("original_external_repo") == "teorth/IEANTN", "REPO")
    require(rec.get("qualified_count") == 2 and len(rec.get("cases", [])) == 2, "CASE_COUNT")
    require(prev.get("schema") == "metalogic.mathgraph-check.external-pr-native-preview.v1", "PREVIEW_SCHEMA")
    require(prev.get("actual_check_runs_posted") == 0, "FALSE_PUBLICATION")
    require(prev.get("github_app_installation") == "NOT_TESTED", "FALSE_INSTALLATION")
    require(prev.get("advisory_scope") == "EXACT_PINNED_NATIVE_PR_REGRESSIONS_ONLY", "PREVIEW_SCOPE")
    require(len(prev.get("results", [])) == 2, "PREVIEW_CASE_COUNT")
    for n in PINNED_HEADS:
        candidates = [r for r in rec["cases"] if r.get("pr") == n]
        prs = [r for r in prev["results"] if r.get("pr") == n]
        require(len(candidates) == len(prs) == 1, "JOIN_AMBIGUOUS")
        c, v = candidates[0], prs[0]
        require(c.get("base_sha") == PINNED_BASE, "WRONG_BASE")
        require(c.get("head_sha") == PINNED_HEADS[n], "WRONG_HEAD")
        require(v.get("protected_revision") == PINNED_HEADS[n], "WRONG_PROTECTED_HEAD")
        require(v.get("source", {}).get("sha") == PINNED_HEADS[n], "WRONG_SOURCE_SHA")
        require(v.get("source", {}).get("repository") == "teorth/IEANTN", "WRONG_SOURCE_REPO")
        require(v.get("receipt_id") == RECEIPT_DIGEST, "WRONG_RECEIPT_DIGEST")
        require(v.get("actually_posted") is False and v.get("app_installed") is False, "FALSE_LIVE_APP")
        require(v.get("action_authorization") == "NONE", "FALSE_PR_AUTHORIZATION")
        require(v.get("external_contributor_supplied_fix") is True, "FALSE_FIX_ORIGIN")
        require(v.get("auto_repair_generated") is False and v.get("scientific_L7") == "UNKNOWN", "FALSE_AUTONOMY_PR")
        require(v.get("finding") == "BEHAVIORAL_SCOPE_UNKNOWN", "GENERIC_SCOPE_LAUNDERED")
        require(v.get("native_evidence_verdict", "WARRANTED_BOUNDED_REAL_PR_NATIVE_REGRESSION") ==
                "WARRANTED_BOUNDED_REAL_PR_NATIVE_REGRESSION", "NATIVE_SCOPE_LAUNDERED")
        p = v.get("github_check_run_preview", {})
        require(p.get("conclusion") == "neutral" and p.get("status") == "completed", "ESCALATED_CONCLUSION")
        require(p.get("head_sha") == PINNED_HEADS[n], "WRONG_CHECK_HEAD")
        require(p.get("external_id") == f"teorth/IEANTN#{n}@{PINNED_HEADS[n]}", "WRONG_EXTERNAL_ID")
        require(c.get("result") == "WARRANTED_BOUNDED_REAL_PR_NATIVE_REGRESSION", "UNQUALIFIED_RECEIPT")
        require(c.get("source_behavioral_proof") == "RED_BASE_GREEN_HEAD_NATIVE_TESTS", "NON_COUNTERFACTUAL_RECEIPT")
        require(c["before_source_with_head_tests"].get("exit_code") != 0, "ORIGINAL_BASE_NOT_RED")
        require(c["after_source_with_head_tests"].get("exit_code") == 0, "AUTHOR_HEAD_NOT_GREEN")
        require(c["old_full_suite_on_base"].get("exit_code") == 0, "ORIGINAL_FULL_SUITE_NOT_GREEN")
        require(c["full_suite_on_head"].get("exit_code") == 0, "AUTHOR_FULL_SUITE_NOT_GREEN")
        methods = c.get("AST_derived_new_test_methods", [])
        require(len(methods) == 2 if n == 158 else len(methods) == 1, "WRONG_METHOD_COUNT")
        require(all(re.fullmatch(r"Test[A-Za-z0-9_]+\.test_[A-Za-z0-9_]+", m) for m in methods), "METHOD_FORMAT")
        require(len(methods) == c["before_source_with_head_tests"]["test_count"] == c["after_source_with_head_tests"]["test_count"], "COUNTERFACTUAL_METHOD_MISMATCH")
        require(f"Evidence receipt SHA256:** {RECEIPT_DIGEST}" in p["output"]["summary"], "DIGEST_NOT_LINKED_IN_PREVIEW")


def replay(z: zipfile.ZipFile, c: dict, arm: str) -> dict:
    n = c["pr"]
    prefix = f"overlays/{n}/{arm}/"
    with tempfile.TemporaryDirectory(prefix=f"mg-{n}-{arm}-") as tmp:
        for member in (prefix + "scripts/ieantn.py", prefix + "tests/test_ieantn.py"):
            out = Path(tmp) / member[len(prefix):]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(z.read(member))
        methods = [m.split(".", 1)[1] for m in c["AST_derived_new_test_methods"]]
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_ieantn.py"]
        for m in methods:
            cmd.extend(["-k", m])
        cmd.append("-v")
        run = subprocess.run(cmd, cwd=tmp, env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"},
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, timeout=40, check=False)
        output = run.stdout + run.stderr
        found = re.search(r"Ran (\d+) test", output)
        require(found is not None, "NATIVE_TESTS_NOT_RUN")
        num = int(found.group(1))
        require(num == len(methods), "NATIVE_SELECTOR_INCOMPLETE")
        require(not any(e in output for e in ["ImportError:", "ModuleNotFoundError:", "Ran 0 tests"]), "NATIVE_SETUP_FAILURE")
        want = c["before_source_with_head_tests"] if arm == "base" else c["after_source_with_head_tests"]
        require((run.returncode == 0) == (want["exit_code"] == 0), "NATIVE_COUNTERFACTUAL_DISAGREES")
        return {"case": n, "arm": arm, "native_method_count": num,
                "exit_code": run.returncode, "expected_exit_code": want["exit_code"],
                "observed": "PASS" if run.returncode == 0 else "BEHAVIORAL_REGRESSION",
                "matched_historical_pass_fail": True, "tail": output[-620:]}


def main():
    for p in (NATIVE, PREVIEW):
        require(p.is_file() and sha(p.read_bytes()) == EXPECTED[p.name], "ARCHIVE_IDENTITY_MISMATCH")
    with zipfile.ZipFile(NATIVE) as original, zipfile.ZipFile(PREVIEW) as preview:
        embedded = preview.read("native-pr-proof/pr-native.zip")
        require(sha(embedded) == EXPECTED[NATIVE.name], "EMBEDDED_ARCHIVE_MISMATCH")
        receipt_bytes = original.read("receipt.json")
        require(sha(receipt_bytes) == RECEIPT_DIGEST, "RECEIPT_BYTE_IDENTITY_MISMATCH")
        rec = json.loads(receipt_bytes)
        prev = json.loads(preview.read("mathgraph-check/external-pr-neutral-previews.json"))
        verify_receipt(rec, prev)
        runs = [replay(original, next(r for r in rec["cases"] if r["pr"] == n), a)
                for n in PINNED_HEADS for a in ("base", "head")]
        controls = {
            "wrong_pr_source_sha": ("preview", lambda v: v["results"][0]["source"].update(sha="0"*40)),
            "wrong_check_head": ("preview", lambda v: v["results"][0]["github_check_run_preview"].update(head_sha="0"*40)),
            "forged_authorization": ("receipt", lambda v: v.update(action_authorization="MERGE")),
            "forged_l7": ("receipt", lambda v: v.update(scientific_L7="WARRANTED")),
            "fake_base_green": ("receipt", lambda v: v["cases"][0]["before_source_with_head_tests"].update(exit_code=0)),
            "fake_head_green_absent": ("receipt", lambda v: v["cases"][0]["after_source_with_head_tests"].update(exit_code=1)),
            "wrong_receipt_link": ("preview", lambda v: v["results"][0].update(receipt_id="0"*64)),
            "false_check_posting": ("preview", lambda v: v.update(actual_check_runs_posted=2)),
            "escalated_github_conclusion": ("preview", lambda v: v["results"][0]["github_check_run_preview"].update(conclusion="success")),
            "false_fix_origin": ("preview", lambda v: v["results"][0].update(external_contributor_supplied_fix=False)),
        }
        negatives = []
        for name, (which, mutate) in controls.items():
            r, p = copy.deepcopy(rec), copy.deepcopy(prev)
            mutate(r if which == "receipt" else p)
            try:
                verify_receipt(r, p)
            except ValueError as e:
                negatives.append({"control": name, "rejected": True, "code": str(e)})
            else:
                raise ValueError("MUTATION_UNDETECTED:" + name)
        result = {
          "schema": "metalogic.external-native-archive-consumer.v1",
          "run_mode": "OFFLINE_READ_ONLY_ORIGINAL_ARCHIVES",
          "archive_sha256": EXPECTED,
          "original_native_receipt_sha256": RECEIPT_DIGEST,
          "original_native_run": "https://github.com/heathsanchez/test/actions/runs/38495636825",
          "original_preview_run": "https://github.com/heathsanchez/test/actions/runs/38498825980",
          "independent_consumer_status": "WARRANTED_BOUNDED_OFFLINE_HISTORICAL_COUNTERFACTUAL",
          "source_revision_current_freshness": "NOT_CHECKED",
          "real_github_app_check_publication_from_this_consumer": False,
          "same_test_sources_used": True,
          "separate_original_test_implementations": False,
          "source_to_natural_language_fidelity": "UNKNOWN",
          "customer_adoption": "UNKNOWN",
          "auto_repair_or_L7": "UNKNOWN",
          "native_replays": runs,
          "adversarial_rejections": negatives,
          "baseline_comparison": {
             "generic_existing_app": "BEHAVIORAL_SCOPE_UNKNOWN for both PRs",
             "original_old_ci_only": "241/241 GREEN for both original branches",
             "enhanced_receipt_consumer": "original regression RED and original contributor head GREEN for both PRs",
             "strong_full_information_reviewer": "also has all the original tests and can reach the same conclusions",
             "measured_relative_time_or_cost_advantage": "NOT_MEASURED",
             "novel_decision_improvement_over_full_information_baseline": "NOT_ESTABLISHED"
          },
          "action_authorization": "NONE"
        }
        dest = HERE / "mathgraph_check_native_bridge_replay_result.json"
        dest.write_text(json.dumps(result, indent=2)+"\n")
        print(json.dumps({"replays": [{k:x[k] for k in ("case","arm","observed","native_method_count")} for x in runs],
                          "negative_controls": len(negatives),
                          "archive_verified":True,
                          "verdict":result["independent_consumer_status"],
                          "result_path":str(dest)}, indent=2))


if __name__ == "__main__":
    main()