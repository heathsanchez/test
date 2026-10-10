#!/usr/bin/env python3
"""Matched WebArena task-family F acquisition economics.

Source authority: ServiceNow/webarena-verified@6473f72db5dcefc97b5725b59e734504edc28a21.
Retained representation: certified E artifact 11467591099, from run 37587112851.
F train: 288; F heldout: 292, neither used in earlier A-E acquisition.

All arms receive the same observed order rows, candidate-scoring budget, pinned
official evaluator, and deterministic search order. Only admissible grouping
hypotheses differ. A naive broad search is a WEAK baseline; schema-aware
stateless inference is the meaningful alternative. This cannot measure total
amortized economics or establish recursive acceleration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path

F_TRAIN = (288,)
F_HOLDOUT = (292,)
SOURCE = "6473f72db5dcefc97b5725b59e734504edc28a21"
E_FREEZE = "66930dc2ea50b944564c46e12d531b6daca8d609cb2495b21152078a3c87267d"
STATUS_CHOICES = ("any", "complete", "cancelled")


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_retained(archive):
    root = Path(archive)
    result = read(root / "result.json")
    frozen = read(root / "frozen.json")
    rep = read(root / "representation.json")
    assert frozen["freeze_sha256"] == E_FREEZE, "E frozen checksum mismatch"
    assert hashlib.sha256(json.dumps({k: v for k, v in frozen.items() if k != "freeze_sha256"}, sort_keys=True).encode()).hexdigest() == E_FREEZE, "corrupt E frozen bytes"
    assert result["epistemic_state"] == "WARRANTED_BOUNDED"
    assert result["freeze_sha256"] == E_FREEZE
    assert result["representation"] == rep == frozen["representation"]
    assert (rep["representation_type"], rep["group_key"], rep["measure"], rep["source_row_semantics"]) == (
        "grouped_row_count", "customer email", "row_count", "one row per order")
    assert result["selected"]["success_count"] == 3
    assert result["grouping_ablation"]["success_count"] == 0
    return rep, {
        "prior_run": 37587112851,
        "prior_artifact": 11467591099,
        "freeze_sha256": E_FREEZE,
        "representation_file_sha256": sha(root / "representation.json"),
    }


def validate_input(tasks, observation):
    assert all("eval" not in t and "reference_url" not in t for t in tasks), "oracle exposed to candidates"
    ti = {int(t["task_id"]): t for t in tasks}
    assert all(t in ti and ti[t]["intent_template_id"] == 234 for t in F_TRAIN + F_HOLDOUT)
    assert "most cancellations" in ti[288]["intent"].lower()
    assert observation["row_semantics"] == "one row per order"
    rows = observation["rows"]
    assert rows and {"id", "customer email", "status_class"}.issubset(rows[0])
    assert len({r["id"] for r in rows}) == len(rows), "duplicate order identifiers"
    assert any(r["status_class"] == "cancelled" for r in rows), "fixture contains no cancelled orders"
    return ti


def infer_schema_key(intent, observation):
    # Generic schema-based inference WITHOUT E memory.
    target = "customer email" if re.search(r"\bemail\b.*\bcustomer\b|\bcustomer\b.*\bemail\b", intent, re.I) else None
    assert target is not None and target in observation["rows"][0]
    return target


def candidate_keys(observation):
    # Deliberately broad control, NOT the strongest available stateless inference.
    return [k for k in ("id", "status_class", "customer email") if k in observation["rows"][0]]


def response_for(task_id, observation, key, status_filter):
    assert status_filter in STATUS_CHOICES
    rows = observation["rows"] if status_filter == "any" else [
        r for r in observation["rows"] if r["status_class"] == status_filter
    ]
    counts = Counter(r[key] for r in rows)
    if not counts:
        return {"task_type": "RETRIEVE", "status": "NOT_FOUND_ERROR",
                "retrieved_data": None, "error_details": None}
    top = max(counts.values())
    winners = sorted(k for k, n in counts.items() if n == top)
    if task_id == 288:
        data = winners
    elif task_id == 292:
        data = [top]
    else:
        raise ValueError("out of scope F task")
    return {"task_type": "RETRIEVE", "status": "SUCCESS",
            "retrieved_data": data, "error_details": None}


def score(wa, empty_trace, root, arm, phase, task_id, observation, key, status):
    from time import perf_counter
    # Unique path for every candidate: never silently overwrite a losing witness.
    path = root / arm / phase / f"{task_id}_{key}_{status}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(response_for(task_id, observation, key, status), indent=2) + "\n")
    before = perf_counter()
    r = wa.evaluate_task(task_id=task_id, agent_response=path, network_trace=empty_trace)
    return {
        "task_id": task_id, "score": float(r.score), "status": r.status.value,
        "verifier_seconds": perf_counter() - before, "output_path": str(path),
    }


def passes(r):
    return r["score"] == 1.0 and r["status"] == "success"


def run(args):
    from webarena_verified.api import WebArenaVerified
    from webarena_verified.types.config import WebArenaVerifiedConfig
    from webarena_verified.types.tracing import NetworkTrace

    root = Path(args.root)
    rep, receipt = verify_retained(args.archive)
    observation = read(args.observation)
    tasks = validate_input(read(args.tasks), observation)
    assert rep["group_key"] in observation["rows"][0]
    wa = WebArenaVerified(config=WebArenaVerifiedConfig.from_file(Path(args.config)))
    empty = NetworkTrace.model_construct(is_playwright=False, src_file=Path("<none>"), events=())

    hypotheses = {
        "retained_e": [rep["group_key"]],
        "stateless_schema": [infer_schema_key(tasks[288]["intent"], observation)],
        "stateless_broad": candidate_keys(observation),
    }
    result = {
        "experiment": "WebArena F grouped cancellation acquisition: E memory vs stateless alternatives",
        "authority_commit": SOURCE, "train": list(F_TRAIN), "heldout": list(F_HOLDOUT),
        "equal_budget_candidate_task_evaluations": args.budget,
        "prior_e": receipt, "fresh_observation_sha256": sha(args.observation),
        "observed_order_rows": len(observation["rows"]),
        "arms": {}, "claims": {},
    }
    # Freeze ALL acquisition decisions before inspecting ANY heldout score.
    for arm, keys in hypotheses.items():
        history = []
        chosen = None
        start = time.perf_counter()
        for key in keys:
            for status in STATUS_CHOICES:
                if len(history) >= args.budget:
                    break
                training = [score(wa, empty, root, arm, "train", tid, observation, key, status) for tid in F_TRAIN]
                row = {"key": key, "filter": status, "results": training,
                       "passed": all(passes(s) for s in training)}
                history.append(row)
                if row["passed"]:
                    chosen = {"group_key": key, "status_filter": status}
                    break
            if chosen is not None or len(history) >= args.budget:
                break
        freeze = {
            "arm": arm, "chosen": chosen, "training": list(F_TRAIN),
            "search_log": [{"key": h["key"], "filter": h["filter"], "passed": h["passed"]} for h in history],
        }
        (root / f"{arm}_freeze.json").write_text(json.dumps(freeze, indent=2) + "\n")
        result["arms"][arm] = {
            "chosen": chosen, "training_results": history,
            "freeze_sha256": digest(freeze), "candidate_task_evaluations": sum(len(h["results"]) for h in history),
            "train_verifier_seconds": sum(s["verifier_seconds"] for h in history for s in h["results"]),
            "search_wall_seconds": time.perf_counter() - start,
            "state": "FROZEN_BEFORE_HELDOUT",
        }

    assert "most cancellations" in tasks[292]["intent"].lower()
    for arm, arm_result in result["arms"].items():
        chosen = arm_result["chosen"]
        held = [] if chosen is None else [
            score(wa, empty, root, arm, "heldout", tid, observation,
                  chosen["group_key"], chosen["status_filter"]) for tid in F_HOLDOUT
        ]
        ok = chosen is not None and all(passes(v) for v in held)
        arm_result["heldout_results"] = held
        arm_result["state"] = "WARRANTED_BOUNDED_F" if ok else "REJECTED_OR_UNKNOWN_F"
        arm_result["heldout_verifier_seconds"] = sum(v["verifier_seconds"] for v in held)

    a = result["arms"]
    success = all(v["state"] == "WARRANTED_BOUNDED_F" for v in a.values())
    c = lambda k: a[k]["candidate_task_evaluations"]
    result["claims"] = {
        "reusable_E_to_F_cancellation_grouping": "WARRANTED_BOUNDED" if success else "UNKNOWN",
        "cost_saving_vs_broad_stateless": "WARRANTED_BOUNDED" if success and c("retained_e") < c("stateless_broad") else "UNKNOWN",
        "cost_saving_vs_schema_aware_stateless": "WARRANTED_BOUNDED" if success and c("retained_e") < c("stateless_schema") else ("REJECTED_ON_THIS_CASE" if success else "UNKNOWN"),
        "full_amortized_recursive_acceleration": "UNKNOWN",
    }
    (root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "prior_e": receipt, "claims": result["claims"],
        "arms": {k: {"candidate_task_evaluations": v["candidate_task_evaluations"],
                     "state": v["state"], "chosen": v["chosen"],
                     "heldout_results": v["heldout_results"]} for k, v in a.items()},
    }, indent=2))
    # A negative economics finding is a valid experiment outcome; integrity controls must hold.
    assert len(a) == 3
    assert all(v["candidate_task_evaluations"] <= args.budget for v in a.values())


def selftest():
    ob = {"row_semantics": "one row per order",
          "rows": [{"id": "1", "customer email": "alice", "status_class": "cancelled"},
                   {"id": "2", "customer email": "alice", "status_class": "cancelled"},
                   {"id": "3", "customer email": "bob", "status_class": "complete"}]}
    assert response_for(288, ob, "customer email", "cancelled")["retrieved_data"] == ["alice"]
    assert response_for(292, ob, "customer email", "cancelled")["retrieved_data"] == [2]
    assert response_for(288, ob, "id", "cancelled")["retrieved_data"] != ["alice"]
    assert infer_schema_key("Get the email of the customer who has the most cancellations", ob) == "customer email"
    assert candidate_keys(ob) == ["id", "status_class", "customer email"]
    assert not passes({"score": 0.0, "status": "failure"})
    print("SELFTEST_OK")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--root", default="artifacts/matched_compounding_v1")
    p.add_argument("--archive", default="artifacts/matched_compounding_v1/e_archive")
    p.add_argument("--observation", default="artifacts/matched_compounding_v1/f_observation.json")
    p.add_argument("--tasks", default="artifacts/matched_compounding_v1/full_no_eval.json")
    p.add_argument("--config", default="artifacts/matched_compounding_v1/config.json")
    p.add_argument("--budget", type=int, default=12)
    args = p.parse_args()
    if args.self_test:
        selftest()
    else:
        run(args)
