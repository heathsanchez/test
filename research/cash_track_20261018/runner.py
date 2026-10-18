#!/usr/bin/env python3
"""Reproducible bounded evidence-admissibility controls for developer agents.

This is a construction test over externally qualified historical authorities,
NOT an independent re-execution of original upstream Go, Lean or Python tests.
The self-generated negative controls do not establish held-out generalization.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHORITIES = HERE / "authorities.json"
CONTROL_NAMES = (
    "stale_subject",
    "wrong_ci_run",
    "wrong_matrix_job",
    "missing_required_phase",
    "forged_extra_phase",
    "revoked_source",
    "unsupported_broader_claim",
)


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def load_authorities():
    data = json.loads(AUTHORITIES.read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) == len({x["id"] for x in cases}), "duplicate case ID"
    assert len(cases) == 7, "unpreregistered case count"
    for c in cases:
        for field in ("id", "repo", "subject", "run_id", "job", "claim", "required_phases", "unknown_claim", "citation"):
            assert field in c and c[field], f"{c.get('id')} missing {field}"
        assert c["claim"] != c["unknown_claim"]
        assert len(c["required_phases"]) == len(set(c["required_phases"]))
    assert cases[1]["run_id"] == cases[2]["run_id"]
    assert cases[1]["job"] != cases[2]["job"], "Go matrix-job guard absent"
    return data


def original_packet(c):
    return {
        "case_id": c["id"],
        "repo": c["repo"],
        "subject": c["subject"],
        "ci_run_id": c["run_id"],
        "ci_job": c["job"],
        "ci_conclusion": "success",
        "claim": c["claim"],
        "observed_phases": list(c["required_phases"]),
        "source_active": True,
        "evidence_url": c["citation"],
    }


def mutation(packet, c, name):
    q = copy.deepcopy(packet)
    if name == "stale_subject":
        q["subject"] += "-stale"
    elif name == "wrong_ci_run":
        q["ci_run_id"] = c["run_id"] + 1
    elif name == "wrong_matrix_job":
        # If another authentic job shares the run this must still fail.
        q["ci_job"] = "Exact original native application / transfer" if c["id"] == "ozzo-e164" else "unrelated-successful-job"
    elif name == "missing_required_phase":
        q["observed_phases"].pop()
    elif name == "forged_extra_phase":
        q["observed_phases"].append("agent_claims_verified_without_execution")
    elif name == "revoked_source":
        q["source_active"] = False
    elif name == "unsupported_broader_claim":
        q["claim"] = c["unknown_claim"]
    else:
        raise ValueError("Unfrozen mutation: " + name)
    return q


def admit(packet, authorities):
    """Only checks packet identity/scope consistency against pinned local data.

    Does NOT authenticate a GitHub run, verify its ZIP, execute a Lean kernel,
    or establish that an AI agent autonomously discovered a method.
    """
    if not isinstance(packet, dict):
        return False
    c = authorities.get(packet.get("case_id"))
    if c is None:
        return False
    return (
        packet.get("repo") == c["repo"]
        and packet.get("subject") == c["subject"]
        and packet.get("ci_run_id") == c["run_id"]
        and packet.get("ci_job") == c["job"]
        and packet.get("ci_conclusion") == "success"
        and packet.get("claim") == c["claim"]
        and packet.get("observed_phases") == c["required_phases"]
        and packet.get("source_active") is True
        and packet.get("evidence_url") == c["citation"]
    )


def baseline_always(_packet, _cases):
    return True


def baseline_green(packet, _cases):
    return packet.get("ci_conclusion") == "success"


def baseline_subject(packet, cases):
    c = cases.get(packet.get("case_id"))
    return bool(c and packet.get("ci_conclusion") == "success"
                and packet.get("repo") == c["repo"]
                and packet.get("subject") == c["subject"])


def baseline_run_subject(packet, cases):
    c = cases.get(packet.get("case_id"))
    return bool(c and baseline_subject(packet, cases)
                and packet.get("ci_run_id") == c["run_id"])


METHODS = {
    "accept_all": baseline_always,
    "green_ci_only": baseline_green,
    "subject_green": baseline_subject,
    "subject_run_green": baseline_run_subject,
    "typed_scoped_packet": admit,
}


def build_examples(data):
    examples = []
    cases = {c["id"]: c for c in data["cases"]}
    for key in sorted(cases):
        c = cases[key]
        good = original_packet(c)
        examples.append({
            "id": key + "::original_scoped",
            "source_case": key,
            "control": "original_scoped",
            "admissible": True,
            "packet": good,
        })
        for name in CONTROL_NAMES:
            examples.append({
                "id": key + "::" + name,
                "source_case": key,
                "control": name,
                "admissible": False,
                "packet": mutation(good, c, name),
            })
    return examples


def evaluate(examples, cases):
    results = {}
    for name, method in METHODS.items():
        tp = fp = tn = fn = 0
        for x in examples:
            predicted = bool(method(x["packet"], cases))
            if predicted and x["admissible"]:
                tp += 1
            elif predicted and not x["admissible"]:
                fp += 1
            elif not predicted and x["admissible"]:
                fn += 1
            else:
                tn += 1
        results[name] = {
            "true_admissions": tp, "false_admissions": fp,
            "correct_refusals": tn, "wrong_refusals": fn,
            "precision": round(tp / (tp + fp), 6) if tp + fp else None,
            "recall": round(tp / (tp + fn), 6) if tp + fn else None,
        }
    return results


def run(out_dir=None):
    data = load_authorities()
    cases = {c["id"]: c for c in data["cases"]}
    examples = build_examples(data)
    assert len(examples) == 7 * (1 + len(CONTROL_NAMES))
    assert len([x for x in examples if x["admissible"]]) == 7
    assert all(admit(x["packet"], cases) is x["admissible"] for x in examples)
    assert len({x["id"] for x in examples}) == len(examples)
    results = evaluate(examples, cases)
    authority_blob = AUTHORITIES.read_bytes()
    jsonl = b"".join(canonical(row) + b"\n" for row in examples)
    report = {
        "experiment": data["version"],
        "status": "WARRANTED_BOUNDED_PACKET_CONSISTENCY_IF_SOURCE_CI_GREEN",
        "scope": "Self-generated adversarial controls over manually transcribed, externally source-linked historical CI observations",
        "actual_source_native_rerun": False,
        "actual_ai_model_run": False,
        "competition_submission": False,
        "frozen_protocol_commit": data["frozen_protocol_sha"],
        "authority_file_sha256": sha256(authority_blob),
        "dataset_sha256": sha256(jsonl),
        "original_positive_cases": 7,
        "negative_controls": 7 * len(CONTROL_NAMES),
        "methods": results,
        "constraints": data["limitations"],
        "next_decisive_test": "Independent unseen coding-agent outputs; actual native oracle; matched strong agent; source/rights audit and measured full lifecycle cost",
    }
    output = canonical(report) + b"\n"
    if out_dir:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "evidence_cases.jsonl").write_bytes(jsonl)
        (out / "metrics.json").write_bytes(output)
        (out / "README.txt").write_text(
            "Scope: original evidence case IDs, CI-success observations and source claims were frozen before this code. "
            "Labels are control constructions, not sampled unknown-world ground truth. "
            "A result of 0 false admissions is a specification sanity check, not an estimated real-world false-positive rate.\n",
            encoding="utf-8",
        )
    return report, jsonl, output


def self_test():
    report, jsonl, metrics = run()
    data = load_authorities()
    cases = {c["id"]: c for c in data["cases"]}
    positives = build_examples(data)
    for x in positives:
        assert isinstance(admit(x["packet"], cases), bool)
        if x["control"] == "wrong_matrix_job":
            assert not admit(x["packet"], cases)
    assert report["methods"]["typed_scoped_packet"]["false_admissions"] == 0
    assert report["methods"]["typed_scoped_packet"]["true_admissions"] == 7
    assert report["methods"]["green_ci_only"]["false_admissions"] == 49
    assert run()[1:] == (jsonl, metrics), "not deterministic"
    print("SELF_TEST_PASS: 7 genuine bounded packets; 49 constructed falsifiers; exact deterministic replay")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--out", default="out")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    report, _, _ = run(args.out)
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
