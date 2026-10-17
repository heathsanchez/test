#!/usr/bin/env python3
"""Original V104/MSI native training over a source-blind, precommitted catalog.

No new constructor/operator/method grammar is introduced. Original base + exact
head-authored regression test only. Held-out future must remain unopened.
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

from research.unified_consequence_runtime import (
    qualify_source_bound_g2_v9 as original,
    typed_v104_msi_bridge_v7 as bridge,
)

ROOT = Path(__file__).resolve().parents[2]
U = "research/unified_consequence_runtime/"
LOCK = U + "G2_TRAINING_NATIVE_CATALOG_LOCK_V1.json"
PROTOCOL = U + "G2_TRAINING_METHOD_V104_PROTOCOL_V1.json"
POOL = U + "G2_SOURCE_DISTINCT_POOL_V1.json"
LOCK_COMMIT = "fc5cbaf37fe55ab36b06de35e53bc08844791182"
POOL_COMMIT = "b90328c2315bd07d30bf7ddf05711e7431589aaf"


def git(repo, *args, raw=False):
    result = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(repo), *args],
        capture_output=True, timeout=50, check=True,
    )
    return result.stdout if raw else result.stdout.decode().strip()


def fail(actual, expected, reason):
    if actual != expected:
        raise ValueError(reason + " (expected=" + str(expected) + ", actual=" + str(actual) + ")")


def authority(path, commit):
    live = (ROOT / path).read_bytes()
    frozen = git(ROOT, "show", commit + ":" + path, raw=True)
    fail(live, frozen, "FROZEN_RESEARCH_SOURCE_CHANGED")
    return json.loads(frozen)


def immutable_inputs(repo, triskelion, msi):
    lock = authority(LOCK, LOCK_COMMIT)
    protocol = authority(PROTOCOL, "36f3f82ebe840eaeac049020844fb3ba54639a4a")
    pool = authority(POOL, POOL_COMMIT)
    task = pool["case_pool"][0]
    fail(lock["training"], task["repo"] + "@" + task["base"],
         "FROZEN_TRAINING_SUBJECT_CHANGED")
    fail(protocol["training"]["production_paths"], [
        x["path"] for x in task["production"]], "PRODUCTION_SCOPE_CHANGED")
    fail(protocol["training"]["protected"], [
        "tests/test_pytest_plugin.py::test_hypothesis_multiple_backends",
        "tests/test_pytest_plugin.py::test_hypothesis_multiple_backends_in_class",
    ], "PROTECTED_TEST_LIST_CHANGED")
    fail(git(repo, "rev-parse", "HEAD"), task["base"], "TRAINING_BASE_COMMIT_CHANGED")
    fail(git(repo, "rev-parse", "HEAD^{tree}"), task["base_tree"],
         "TRAINING_BASE_TREE_CHANGED")
    fail(git(repo, "status", "--porcelain"), "", "DIRTY_TRAINING_BASE_SOURCE")
    fail(git(triskelion, "rev-parse", "HEAD"),
         "426c54f7c774560e0fabe7213c5ef333b1327c71", "V104_SOURCE_CHANGED")
    fail(git(msi, "rev-parse", "HEAD"),
         "56cfd7b523e3592cae4eafa5468f437ccb94dbe9", "MSI_SOURCE_CHANGED")
    fail(pool["case_pool"][1]["repo"], "alexmojaki/executing",
         "HELDOUT_SOURCE_ROLE_CHANGED")
    return lock, protocol, task


def prepare_author(repo, task):
    # Git has the exact author-head commit object solely to permit reading this
    # ONE head test blob. Never request author-repaired production or heldout.
    rows = []
    for item in task["head_author_tests"]:
        path, oid = item["path"], item["head_blob"]
        fail(git(repo, "rev-parse", task["head"] + ":" + path), oid,
             "AUTHOR_TEST_OID_CHANGED")
        raw = git(repo, "show", task["head"] + ":" + path, raw=True)
        fail(hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw
        ).hexdigest(), oid, "AUTHOR_TEST_CONTENT_NOT_GIT_BLOB")
        rows.append({
            "path": path, "git_oid": oid, "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": raw.hex(),
        })
    return rows


def run(repo, triskelion, msi, output):
    t0 = time.monotonic()
    output.mkdir(parents=True, exist_ok=False)
    result = {
        "schema": "UDM_FROZEN_ORIGINAL_V104_MSI_TRAINING_NATIVE_V1",
        "status": "UNKNOWN_NOT_EXECUTED",
        "training": "agronholm/anyio#1354",
        "heldout_source": "UNOPENED",
        "original_method_source": "ORIGINAL_PINNED_V104_AND_MSI_V10",
        "native_calls_conservatively_charged": 0,
        "G2": "UNKNOWN", "G3": "UNKNOWN", "G4": "UNKNOWN",
        "G5": "UNKNOWN", "G6": "UNKNOWN",
        "future_native": "NOT_EXECUTED",
        "agent_comparator": "NOT_EXECUTED",
        "ledger_comparator": "NOT_EXECUTED",
        "permission": "NONE",
    }
    try:
        lock, protocol, task = immutable_inputs(repo, triskelion, msi)
        authors = prepare_author(repo, task)
        cat = bridge.catalog_v104_typed(
            repo, task["base"], [row["path"] for row in task["production"]],
            triskelion, msi, cap=64, observation={},
        )
        raw = original.canonical(cat).encode()
        fail(hashlib.sha256(raw).hexdigest(), lock["catalog_canonical_sha256"],
             "SOURCE_ONLY_V104_CATALOG_DIGEST_DIFFERS")
        fail(cat["original_typed_source_sha256"],
             lock["catalog_source_manifest_sha256"], "BASE_TYPED_MANIFEST_DIFFERS")
        fail(cat["source"]["v104_language"], "ORIGINAL_PINNED_V104",
             "ORIGINAL_V104_NOT_USED")
        fail(cat["source"]["msi_policy"], "ORIGINAL_PINNED_MSI_V10",
             "ORIGINAL_MSI_NOT_USED")
        fail(len(cat["rows"]), lock["complete_catalog_candidate_count"],
             "ORIGINAL_CANDIDATE_COUNT_DIFFERS")
        fail(len(cat["orders"]), lock["original_policy_count"],
             "ORIGINAL_POLICY_COUNT_DIFFERS")
        horizon = lock["horizon_per_policy"]
        scheduled = original.schedule(cat["orders"], horizon)
        fail(len(scheduled), lock["unique_scheduled_candidate_count"],
             "PRENATIVE_SCHEDULE_SIZE_DIFFERS")
        fail(original.sha(scheduled), lock["scheduled_candidate_ids_digest_sha256"],
             "PRENATIVE_SCHEDULE_CHANGED")
        fail(len(set(scheduled)), len(scheduled), "DUPLICATE_SCHEDULED_ID")
        (output / "SOURCE_ONLY_LOCKED_CATALOG.json").write_bytes(raw + b"\n")
        (output / "PRENATIVE_SCHEDULE.json").write_text(
            json.dumps({"candidates": scheduled, "candidate_count": len(cat["rows"]),
                        "policy_orders": cat["orders"],
                        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
                        "source_manifest_sha256": cat["original_typed_source_sha256"],
                        "G2": "UNKNOWN", "native_calls": 0},
                       sort_keys=True, indent=2) + "\n")
        result.update(
            status="FROZEN_CATALOG_AWAITING_NATIVE",
            catalog_sha256=hashlib.sha256(raw).hexdigest(),
            schedule_sha256=original.sha(scheduled),
            candidate_count=len(cat["rows"]), scheduled=len(scheduled),
            policy_count=len(cat["orders"]))
        # Refusal controls operate only on local evidence, before native subprocesses.
        bad_author = [dict(authors[0], git_oid="0" * 40)]
        try:
            bridge.changed_author_assertions(repo, task["base"], bad_author)
            raise AssertionError("FORGED_AUTHOR_TEST_OID_WAS_ACCEPTED")
        except ValueError:
            result["wrong_author_test_control"] = "REFUSED"
        invalid_candidate = {"replacements": [{
            "path": task["production"][0]["path"],
            "original_sha256": "0" * 64,
            "replacement": "pass\n"}]}
        try:
            bridge._candidate(invalid_candidate, bridge._blobs(repo, task["base"])[1])
            raise AssertionError("FORGED_SOURCE_REPLACEMENT_WAS_ACCEPTED")
        except ValueError:
            result["wrong_source_replacement_control"] = "REFUSED"

        source_task = {
            "author_tests": [row["path"] for row in task["head_author_tests"]],
            "production": [row["path"] for row in task["production"]],
        }
        native_ceiling = protocol["native_gate"]["training_native_calls_max"]
        cost_ceiling = protocol["native_gate"]["training_wall_seconds"]
        timeout = protocol["native_gate"]["timeout_per_native_call_seconds"]
        base = original._observation(
            repo, task["base"], authors[0], {"replacements": []},
            output / "native-baseline", source_task, timeout,
        )
        result["baseline"] = {
            k: value for k, value in base.items()
            if k not in ("native_first", "native_second")
        }
        (output / "BASELINE_DOUBLE_NATIVE.json").write_text(
            json.dumps(base, indent=2, sort_keys=True) + "\n")
        result["native_calls_conservatively_charged"] += base["native_calls"]
        if base["status"] != original.BAD:
            result["status"] = "UNKNOWN_BASELINE_NATIVE_PROTECTED_FAILURE_NOT_REPRODUCED"
            return result
        result["status"] = "AUTHENTIC_FAIL_REVERIFIED_NATIVE_METHOD_TRIALS"
        evaluations = []
        states = {}
        evidence = {}
        index = {row["id"]: row for row in cat["rows"]}
        for number, key in enumerate(scheduled):
            if (result["native_calls_conservatively_charged"] + 2 >
                    native_ceiling + 2 or
                    time.monotonic() - t0 >= cost_ceiling):
                result["status"] = "UNKNOWN_INCOMPLETE_NATIVE_BUDGET"
                break
            row = index[key]
            observed = original._observation(
                repo, task["base"], authors[0], row["candidate"],
                output / ("candidate-" + str(number).zfill(3)),
                source_task, timeout,
            )
            status = observed["status"]
            result["native_calls_conservatively_charged"] += observed["native_calls"]
            states[key] = status
            evidence[key] = observed.get("evidence_sha256")
            small = {
                "index": number, "id": key, "status": status,
                "native_calls_conservatively_charged": observed["native_calls"],
                "reason": observed.get("reason"),
                "builder": row["builder"], "selector": row["selector"],
                "changed_lines": row["changed_lines"],
                "elapsed_seconds": observed.get("elapsed_seconds"),
                "evidence_sha256": observed.get("evidence_sha256"),
                "measured_statuses": observed.get("measured_statuses"),
            }
            evaluations.append(small)
            (output / ("CANDIDATE_" + str(number).zfill(3) + ".json")).write_text(
                json.dumps(observed, sort_keys=True, indent=2) + "\n")
            # Outcomes never change the precommitted candidate IDs or order.
            result["evaluations_completed"] = len(evaluations)
            result["outcome_counts"] = {
                state: list(states.values()).count(state)
                for state in sorted(set(states.values()))
            }
            (output / "PROGRESS.json").write_text(
                json.dumps({**result, "evaluations": evaluations},
                           indent=2, sort_keys=True) + "\n")
        result["candidate_evaluations"] = evaluations
        if len(states) != len(scheduled):
            result["status"] = "UNKNOWN_INCOMPLETE_ORIGINAL_NATIVE_SCHEDULE"
            return result
        result["status"] = "COMPLETE_NATIVE_EVIDENCE_NO_PROMOTION"
        choice = original._select(
            cat, states, evidence,
            hashlib.sha256((ROOT / PROTOCOL).read_bytes()).hexdigest(),
        )
        result["original_msi_choice"] = choice
        result["selected_training_policy"] = None
        if not original.authorize_future(choice.get("choice"), original.COLD):
            result["status"] = "UNKNOWN_NO_UNIQUE_ORIGINAL_MSI_NONCOLD_POLICY"
            return result
        selected = choice["choice"]["selected"]
        if (choice["profiles"][original.COLD]["TRAINING"] != [1, 16] or
                choice["profiles"][selected]["TRAINING"][0] != 0):
            result["status"] = "UNKNOWN_NO_TRAINING_COLD_RESIDUAL"
            return result
        result["selected_training_policy"] = selected
        result["status"] = "WARRANTED_BOUNDED_ORIGINAL_MSI_TRAINING_CHOICE_FUTURE_SEALED"
        # Even qualified training cannot promote G2 or read held-out source here.
        return result
    except BaseException as error:
        result["status"] = "UNKNOWN_ORIGINAL_TRAINING_APPARATUS"
        result["reason"] = type(error).__name__ + ": " + str(error)
        result["traceback"] = traceback.format_exc(limit=12)[-3300:]
        return result
    finally:
        result["wall_seconds"] = time.monotonic() - t0
        (output / "RESULT.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: g2_original_v104_training_native_v1.py SOURCE V104 MSI FRESH_OUT")
    output = run(*(Path(value).absolute() for value in sys.argv[1:]))
    print(json.dumps({
        name: output.get(name) for name in
        ("status", "native_calls_conservatively_charged",
         "evaluations_completed", "outcome_counts", "selected_training_policy",
         "G2", "heldout_source", "reason")
    }, sort_keys=True))
    raise SystemExit(0 if output["status"] in (
        "WARRANTED_BOUNDED_ORIGINAL_MSI_TRAINING_CHOICE_FUTURE_SEALED",
        "UNKNOWN_NO_UNIQUE_ORIGINAL_MSI_NONCOLD_POLICY",
    ) else 2)
