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
    ap.add_argument("--catalogue-replay", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--previous-flash", type=Path)
    ap.add_argument("--previous-ledger", type=Path)
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
    source_index = read(args.catalogue_replay)
    published = read(args.components / "mathgraph" / "website" / "public"
                     / "catalogues" / "mathlib" / "v4.34.1" / "manifest.json")
    assert source_index == {
        "source_status": "SOURCE_INDEXED",
        "independent_verification": "NOT_CHECKED",
        "current_applicability": "NOT_CHECKED",
        "freshness": "PINNED_HISTORICAL_SOURCE",
        "authorization": "NONE",
        "authority": "NONE"}, "source-index authority changed"
    assert published["counts"]["objects"] == 2345
    assert published["counts"]["relations"] == 3571
    assert published["counts"]["modules"] == 13
    assert published["authority"] == published["authorization"] == "NONE"


    # The frozen native FLASH loader verifies each actual event's evidence bytes.
    bundles = sorted(p.parent for p in args.source_bundles.rglob("event.json"))
    assert len(bundles) >= 4, "no genuine source-bound events"
    preceding_flash = (args.previous_flash.read_text(encoding="utf-8")
                      if args.previous_flash and args.previous_flash.is_file() else None)
    flash = update_live_state(preceding_flash, bundles)
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
    assert len(source_events) <= summary["external_events"]
    assert len({item["id"] for item in source_events}) == len(source_events)
    retained_ids = set(flash["retained_past_event_ids"])
    previous_ids = set()
    if preceding_flash is not None:
        old = read(args.previous_flash)
        previous_ids = {item["event_id"] for item in old["events"]}
        assert previous_ids <= set(summary["event_ids"])
        assert retained_ids <= previous_ids
    assert (set(flash["new_event_ids"]) | set(flash["unchanged_event_ids"])
            ) == {item["id"] for item in source_events}
    assert not (set(flash["new_event_ids"]) & set(flash["unchanged_event_ids"]))

    # New source-qualified native proof is OPTIONAL until its separate Lean
    # verification succeeds. Its capability affects only its matching scope.
    native_done = "CSLIB_NATIVE_PASS" in runs and "native" in manifest["emitters"]
    native_causal = "NOT_CHECKED"
    native_id = "cslib:cycle:native-source-checked-simulation:v1"
    if native_done:
        if native_id not in summary["active_capability_ids"]:
            raise AssertionError("QUALIFIED_NATIVE_PROOF_NOT_IN_ACTIVE_FLASH")
        without = [p for p in bundles if p.relative_to(args.source_bundles).parts[0] != "native"]
        ablated = update_live_state(None, without)["summary"]
        if native_id in ablated["active_capability_ids"]:
            raise AssertionError("NATIVE_PROOF_ABLATION_DID_NOT_REMOVE_CAPABILITY")
        old_active = set(ablated["active_capability_ids"])
        current_active = set(summary["active_capability_ids"])
        if current_active != old_active | {native_id}:
            raise AssertionError("UNRELATED_CAPABILITY_CHANGED_WITH_NATIVE_EVENT")
        if set(ablated["obstruction_ids"]) != set(summary["obstruction_ids"]):
            raise AssertionError("UNRELATED_RESEARCH_OBSTRUCTION_CHANGED")
        native_causal = "PASS_SCOPED_ADMISSION_ABLATION"

    preceding_log = (args.previous_ledger.read_text(encoding="utf-8")
                     if args.previous_ledger and args.previous_ledger.is_file() else None)
    log = mt.loads(preceding_log) if preceding_log is not None else ()
    old_log_ids = set(mt.ids(log))
    assert set(mt.live_ids(log)) == independent_live(log)
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
    source_catalogue = mt.Node("independently_checked_source_index",
        {"scope": "13 pinned Mathlib modules",
         "objects": published["counts"]["objects"],
         "structural_relations": published["counts"]["relations"],
         "source_status": source_index["source_status"],
         "independent_verification": source_index["independent_verification"],
         "current_applicability": source_index["current_applicability"],
         "authority": source_index["authority"],
         "action_authorization": source_index["authorization"]},
        (roots[("components", "mathgraph")].id,))
    log = mt.append(log, source_catalogue)
    flash_event = mt.Node(
        "native_flash_event_reclosure",
        {"event_ids": summary["event_ids"],
         "source_commits": summary["source_commits"],
         "source_events": source_events,
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
    native_node = None
    if native_done:
        success = runs["CSLIB_NATIVE_PASS"]
        assert success["conclusion"] == "success"
        native_node = mt.Node("scoped_native_lean_proof_product", {
            "native_run": success["url"],
            "head": success["commit"],
            "prior_failed_run": bad["url"],
            "verified_scope": "pinned finite CSLib LTS simulation certificate",
            "new_general_generator": "UNKNOWN",
            "current_action_authorization": "NONE",
            "verified_source_capability_id": native_id},
            (anchors["CSLIB_NATIVE_PASS"].id,
             roots[("emitters", "native")].id,
             flash_event.id))
        log = mt.append(log, native_node)
    future_dependencies = (qualification.id, source_catalogue.id, flash_event.id, residual.id)
    if native_done:
        future_dependencies += (native_node.id,)
    future_name = (
        "source_distinct_native_generator_invention_still_open"
        if native_done else "diagnose_native_failure_and_test_new_semantic_repair")
    future_payload = {
        "candidate": future_name,
        "protected_target": bad["url"],
        "native_certificate_backend": "PASS_SCOPED" if native_done else "UNKNOWN",
        "action_authorization": "NONE",
        "system_e2e": manifest["protected_claims"]["system_e2e"],
        "recursive_native_development": manifest["protected_claims"]["recursive_native_development"]}
    frontier = mt.Node("advisory_future", future_payload, future_dependencies)
    if frontier.id not in set(mt.live_ids(log)):
        for old_id, old_node in mt.live(log, "advisory_future"):
            if old_id != frontier.id:
                log = mt.append(log, mt.Node("revoke", {
                    "target": old_id,
                    "reason": "new source-qualified evidence superseded advisory focus"
                }))
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
        "mathgraph_source_catalogue": {
            "counts": published["counts"],
            "source_status": source_index["source_status"],
            "independent_verification": source_index["independent_verification"],
            "action_authorization": source_index["authorization"],
            "current_applicability": source_index["current_applicability"]},
        "flash": {
            "events": summary["external_events"],
            "new_event_ids": flash["new_event_ids"],
            "unchanged_event_ids": flash["unchanged_event_ids"],
            "retained_past_event_ids": flash["retained_past_event_ids"],
            "past_restored": preceding_flash is not None,
            "repositories": summary["repositories"],
            "source_events": source_events,
            "active_capabilities": summary["active_capability_ids"],
            "open_obligations": summary["open_obligation_ids"],
            "obstructions": summary["obstruction_ids"],
            "restart": "PASS"},
        "metatron": {
            "nodes": len(log), "live": len(mt.live_ids(log)),
            "past_restored": preceding_log is not None,
            "prior_node_ids_retained": len(old_log_ids),
            "restart": "PASS", "dependency_oracle": "PASS",
            "source_revocation": "PASS", "unrelated_lineage": "PRESERVED"},
        "frontier": frontier.payload,
        "native_scoped_proof": {
            "verdict": "PASS_SCOPED" if native_done else "UNKNOWN",
            "run": runs["CSLIB_NATIVE_PASS"]["url"] if native_done else None,
            "capability_id": native_id if native_done else None,
            "source_deletion_ablation": native_causal,
            "scientific_genesis": "UNKNOWN"},
        "scientific_closure": "UNKNOWN",
        "scientific_claim_boundary": "INTEGRATED_OPERATIONAL_STATE_NOT_NEW_AUTONOMOUS_CAPABILITY",
        "gates": {
            "source_pins": "PASS",
            "provider_runs": "PASS",
            "independent_mathgraph_replay": "PASS",
            "independent_mathgraph_source_index_replay": "PASS",
            "flash_source_reclosure": "PASS",
            "flash_cold_restart": "PASS",
            "metatron_live_restart": "PASS",
            "metatron_ablation": "PASS",
            "source_bound_native_scoped_certificate": "PASS" if native_done else "UNKNOWN",
            "native_semantic_event_ablation": native_causal,
            "prior_research_history_retained": "PASS" if preceding_flash is not None and preceding_log is not None else "COLD_BOOTSTRAP",
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
