#!/usr/bin/env python3
"""Unify real pinned producer events and independent source checks without authority inflation."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_head(directory, expected):
    actual = subprocess.check_output(
        ["git", "-C", str(directory), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != expected:
        raise ValueError(f"source changed: {directory} {actual} != {expected}")


def check_provider_run(row, event):
    key, repository, run_id, commit, conclusion = row
    assert event["id"] == run_id, key
    assert event["repository"]["full_name"] == repository, key
    assert event["head_sha"] == commit, key
    assert event["status"] == "completed", key
    assert event["conclusion"] == conclusion, key
    return {"key": key, "repository": repository, "commit": commit,
            "run_id": run_id, "conclusion": conclusion,
            "url": event["html_url"], "authority": "HISTORICAL_POINTER_ONLY"}


def check_mathgraph_replay(result, source_dir, policy_hash):
    source_dir = Path(source_dir) / "conformance" / "capability_v1"
    previous = read(source_dir / "evaluation.json")
    receipt = read(source_dir / "receipt.json")
    assert result["evaluation"] == previous, "independent replay disagrees with source"
    assert result["receipt"] == receipt, "independent receipt mismatch"
    assert receipt["trust_policy"]["sha256"] == policy_hash
    assert previous["qualification"] == "QUALIFIED_BOUNDED"
    assert previous["current_applicability"] == "UNKNOWN"
    assert previous["action_authorization"] == "NONE"
    assert previous["revocation"] == previous["freshness"] == "NOT_CHECKED"
    return {"qualification": previous["qualification"],
            "scope": previous["contract"],
            "current_applicability": previous["current_applicability"],
            "action_authorization": previous["action_authorization"],
            "freshness": previous["freshness"], "revocation": previous["revocation"]}


def independent_live(log):
    rows = [node.record() | {"id": node.id} for node in log]
    withdrawn = {x["payload"]["target"] for x in rows if x["kind"] == "revoke"}
    present = set()
    for row in rows:
        if row["kind"] != "revoke" and row["id"] not in withdrawn:
            if set(row["premises"]).issubset(present):
                present.add(row["id"])
    return present


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--components", type=Path, required=True)
    ap.add_argument("--run-data", type=Path, required=True)
    ap.add_argument("--source-bundles", type=Path, required=True)
    ap.add_argument("--mathgraph-replay", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    manifest = read(args.manifest)
    assert manifest["schema"] == "metalogic.unified-consequence-manifest.v1"
    for family in ("components", "emitters"):
        for key, (_, commit) in manifest[family].items():
            base = key if family == "components" else "producers/" + key
            verify_head(args.components / base, commit)

    sys.path.insert(0, str(args.components / "metatron" / "runtime"))
    sys.path.insert(0, str(args.components / "flash"))
    from metatron import nucleus as mt
    from qckn_flash_live_router import update_live_state
    from qckn_flash_cross_repo_ingest import restore_state_bundle

    runs = {}
    for row in manifest["runs"]:
        runs[row[0]] = check_provider_run(row, read(args.run_data / (row[0] + ".json")))

    mg = check_mathgraph_replay(
        read(args.mathgraph_replay), args.components / "mathgraph",
        manifest["mathgraph_policy_sha256"])

    # The frozen native FLASH loader verifies each actual event's evidence bytes.
    bundles = sorted(p.parent for p in args.source_bundles.rglob("event.json"))
    assert len(bundles) >= 4, "no genuine source-bound events"
    flash = update_live_state(None, bundles)
    summary = flash["summary"]
    cold, _ = restore_state_bundle(flash["state_bundle_text"])
    for key in ("external_events", "event_ids", "active_capability_ids",
                "open_obligation_ids", "discharged_obligation_ids", "repositories"):
        assert summary[key] == cold[key], "Flash restart mismatch: " + key
    # A producer can retain multiple historical source commitments.
    # Repo-level source_commits is a lossy presentation, NOT event provenance.
    source_events = []
    for bundle in bundles:
        source_family = bundle.relative_to(args.source_bundles).parts[0]
        repository, emitter_head = manifest["emitters"][source_family]
        event = read(bundle / "event.json")
        allowed = manifest.get("event_origin_allowlist", {}).get(
            source_family, [emitter_head])
        assert event["repository"] == repository, "source repository changed"
        assert event["commit"] in allowed, "unapproved historical event origin"
        source_events.append({
            "id": event["event_id"], "emitter": source_family,
            "repository": repository, "event_origin_commit": event["commit"],
            "emitter_source_commit": emitter_head,
            "source_evidence_sha256": event["source_evidence_sha256"]
        })
    assert len(source_events) == summary["external_events"]
    assert len({item["id"] for item in source_events}) == len(source_events)

    log = ()
    roots = {}
    for family in ("components", "emitters"):
        for key, (repo, commit) in sorted(manifest[family].items()):
            source = mt.Node("source_commit", {"family": family,
                                               "key": key, "repo": repo, "sha": commit})
            log = mt.append(log, source)
            roots[(family, key)] = source
    anchors = {}
    for key, data in sorted(runs.items()):
        event = mt.Node("historical_provider_result", data)
        log = mt.append(log, event)
        anchors[key] = event

    qualification = mt.Node("bounded_profile_replay", mg,
                            (roots[("components", "mathgraph")].id,))
    log = mt.append(log, qualification)
    flash_event = mt.Node(
        "native_flash_event_reclosure",
        {"event_ids": summary["event_ids"],
         "source_commits": summary["source_commits"],
         "active": summary["active_capability_ids"],
         "open": summary["open_obligation_ids"],
         "artifact_sha256": sha(flash["state_bundle_text"].encode("utf-8")),
         "new_theorem": False},
        tuple(roots[("emitters", key)].id for key in sorted(manifest["emitters"])))
    log = mt.append(log, flash_event)
    bad = runs[manifest["protected_claims"]["open_native_target"]]
    assert bad["conclusion"] == "failure"
    residual = mt.Node("unresolved_native_proof", {
        "run": bad["url"], "status": "UNKNOWN",
        "impossibility_certificate": "NOT_PROVIDED",
        "cause": "actual_generated_Lean_certificate_rejected"},
        (anchors[bad["key"]].id,))
    log = mt.append(log, residual)
    frontier = mt.Node("advisory_future", {
        "candidate": "diagnose_native_failure_and_test_new_semantic_repair",
        "protected_target": bad["url"],
        "action_authorization": "NONE",
        "system_e2e": manifest["protected_claims"]["system_e2e"],
        "recursive_native_development": manifest["protected_claims"]["recursive_native_development"]},
        (qualification.id, flash_event.id, residual.id))
    log = mt.append(log, frontier)

    serialized = mt.dumps(log)
    assert mt.loads(serialized) == log
    assert set(mt.live_ids(log)) == independent_live(log)
    assert frontier.id in independent_live(log)
    revoked = mt.append(log, mt.Node("revoke", {
        "target": qualification.id, "reason": "isolated lineage attack only"
    }))
    assert set(mt.live_ids(revoked)) == independent_live(revoked)
    assert frontier.id not in independent_live(revoked)
    assert qualification.id not in independent_live(revoked)
    assert residual.id in independent_live(revoked)
    assert flash_event.id in independent_live(revoked)
    assert mt.loads(serialized) == log, "archived past must not change"

    out = {
        "schema": "metalogic.unified-consequential-closure.v1",
        "manifest_sha256": sha(args.manifest.read_bytes()),
        "sources": manifest["components"],
        "runs": runs,
        "mathgraph": mg,
        "flash": {
            "events": summary["external_events"],
            "repositories": summary["repositories"],
            "source_events": source_events,
            "active_capabilities": summary["active_capability_ids"],
            "open_obligations": summary["open_obligation_ids"],
            "obstructions": summary["obstruction_ids"],
            "restart": "PASS"},
        "metatron": {
            "nodes": len(log), "live": len(mt.live_ids(log)),
            "restart": "PASS", "dependency_oracle": "PASS",
            "source_revocation": "PASS", "unrelated_lineage": "PRESERVED"},
        "frontier": frontier.payload,
        "scientific_closure": "UNKNOWN",
        "scientific_claim_boundary": "INTEGRATED_OPERATIONAL_STATE_NOT_NEW_AUTONOMOUS_CAPABILITY",
        "gates": {
            "source_pins": "PASS",
            "provider_runs": "PASS",
            "independent_mathgraph_replay": "PASS",
            "flash_source_reclosure": "PASS",
            "flash_cold_restart": "PASS",
            "metatron_live_restart": "PASS",
            "metatron_ablation": "PASS",
            "previously_failing_native_goal_solved": "UNKNOWN",
            "new_generator_native_transfer": "UNKNOWN",
            "full_lifecycle_advantage": "NOT_MEASURED"}
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "closure.json").write_text(
        json.dumps(out, sort_keys=True, indent=2) + "\n")
    (args.out / "metatron-ledger.jsonl").write_text(serialized)
    (args.out / "flash-state-bundle.json").write_text(
        flash["state_bundle_text"])
    print("PASS_REAL_CROSS_REPOSITORY_OPERATIONAL_INTEGRATION")
    print("NATIVE_SELF_DEVELOPMENT_STILL_UNKNOWN")


if __name__ == "__main__":
    main()
