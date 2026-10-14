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
    native_revocation = "NOT_CHECKED"
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

        # Deliberately simulated proof withdrawal: generated after current
        # qualification, kept OUTSIDE the real persistent event history.
        # This is a causal control of FLASH's existing revocation logic,
        # not a claim that the actual CSLib proof has been withdrawn.
        from tempfile import TemporaryDirectory
        from realitygraph.flash import ExternalEventEnvelope
        proof_event_path = next(
            p for p in bundles if p.relative_to(args.source_bundles).parts[0] == "native"
        )
        proof_event = read(proof_event_path / "event.json")
        if "external:" + native_id not in summary["discharged_obligation_ids"]:
            raise AssertionError("NEW_NATIVE_OBLIGATION_NOT_ACTUALLY_DISCHARGED")
        simulated_evidence = (
            b'{"kind":"SIMULATED_NATIVE_SUPPORT_WITHDRAWAL","real_revocation":false}'
        )
        attack = ExternalEventEnvelope.capability_revocation(
            event_id="cslib:cycle:controlled-native-revocation:attack-only",
            repository=proof_event["repository"],
            commit=proof_event["commit"],
            authority_snapshot=proof_event["authority_snapshot"],
            verifier_id=proof_event["verifier_id"],
            source_evidence=simulated_evidence,
            capability_id=native_id,
            reason="controlled support withdrawal, NOT an actual proof revocation",
        )
        with TemporaryDirectory(prefix="unified-native-revocation-") as td:
            revocation_dir = Path(td)
            (revocation_dir / "event.json").write_text(attack.to_text())
            (revocation_dir / "evidence.json").write_bytes(simulated_evidence)
            after_revoke = update_live_state(
                None, list(bundles) + [revocation_dir]
            )["summary"]
        if native_id in after_revoke["active_capability_ids"]:
            raise AssertionError("REVOKED_NATIVE_PROOF_REMAINS_EXECUTABLE")
        if set(after_revoke["active_capability_ids"]) != old_active:
            raise AssertionError("REVOKED_PROOF_CHANGED_UNRELATED_ACTIVE_CAPABILITIES")
        if set(after_revoke["obstruction_ids"]) != set(summary["obstruction_ids"]):
            raise AssertionError("REVOKED_PROOF_CHANGED_UNRELATED_OBSTRUCTIONS")
        if "external:" + native_id not in after_revoke["open_obligation_ids"]:
            raise AssertionError("REVOKED_PROOF_DID_NOT_REOPEN_NATIVE_OBLIGATION")
        native_revocation = "PASS_SIMULATED_TYPED_REVOCATION"

    # Real independent source-to-native transfer qualified in the pinned
    # upstream CSLib checker. It is a two-source guarded proof capability,
    # NOT general autonomous generator revision.
    method_done = "CSLIB_SOURCE_METHOD_PASS" in runs and "source_bisim" in manifest["emitters"]
    method_id = "cslib:two-original-inductives:native-source-derived-bisimulation:v1"
    method_ablation = "NOT_CHECKED"
    method_revocation = "NOT_CHECKED"
    if method_done:
        active = set(summary["active_capability_ids"])
        if method_id not in active or "external:" + method_id not in summary["discharged_obligation_ids"]:
            raise AssertionError("SOURCE_NATIVE_METHOD_NOT_ACTUALLY_ADMITTED")
        without_method = [
            p for p in bundles
            if p.relative_to(args.source_bundles).parts[0] != "source_bisim"
        ]
        other = update_live_state(None, without_method)["summary"]
        if set(other["active_capability_ids"]) | {method_id} != active:
            raise AssertionError("SOURCE_METHOD_ABLATION_CHANGED_OTHER_CAPABILITIES")
        if set(other["obstruction_ids"]) != set(summary["obstruction_ids"]):
            raise AssertionError("SOURCE_METHOD_ABLATION_CHANGED_OTHER_OBSTRUCTIONS")
        if method_id in other["active_capability_ids"]:
            raise AssertionError("SOURCE_METHOD_SURVIVED_ANCESTOR_DELETION")
        method_ablation = "PASS_NATIVE_SOURCE_CAPABILITY_DELETION"

        # Additional cross-method revocation uses the existing FLASH typed
        # event language and is NOT persisted as a real source revocation.
        from realitygraph.flash import ExternalEventEnvelope
        from tempfile import TemporaryDirectory
        source = next(p for p in bundles
                      if p.relative_to(args.source_bundles).parts[0] == "source_bisim")
        event = read(source / "event.json")
        simulation = b'{"controlled":true,"real_revocation":false,"source_method":"cslib"}'
        rev = ExternalEventEnvelope.capability_revocation(
            event_id="cslib:source-derived:simulated-revocation:negative-only",
            repository=event["repository"],
            commit=event["commit"],
            authority_snapshot=event["authority_snapshot"],
            verifier_id=event["verifier_id"],
            source_evidence=simulation,
            capability_id=method_id,
            reason="isolated source-method revocation; original Lean proofs remain valid",
        )
        with TemporaryDirectory(prefix="source-method-revoke-") as path:
            attack_dir = Path(path)
            (attack_dir / "event.json").write_text(rev.to_text())
            (attack_dir / "evidence.json").write_bytes(simulation)
            attacked = update_live_state(None, list(bundles) + [attack_dir])["summary"]
        if method_id in attacked["active_capability_ids"]:
            raise AssertionError("REVOKED_METHOD_REMAINED_LIVE")
        if set(attacked["active_capability_ids"]) != set(other["active_capability_ids"]):
            raise AssertionError("METHOD_REVOCATION_AFFECTED_UNRELATED_CAPABILITY")
        if "external:" + method_id not in attacked["open_obligation_ids"]:
            raise AssertionError("METHOD_REVOCATION_FAILED_TO_REOPEN_SOURCE_OBLIGATION")
        if set(attacked["obstruction_ids"]) != set(summary["obstruction_ids"]):
            raise AssertionError("METHOD_REVOCATION_AFFECTED_UNRELATED_OBSTRUCTIONS")
        method_revocation = "PASS_SIMULATED_TYPED_METHOD_REVOCATION"

    # The source-feedback constructor has now made a distinct *native*
    # parametric law available.  DOWN is an independently valid theorem, not a
    # semantic dependency on UP, but its genesis episode does depend on the
    # observed UP failure; model these two relations separately.
    infinite_done = (
        "CSLIB_NATIVE_UNBOUNDED_PASS" in runs
        and "native_unbounded" in manifest["emitters"]
    )
    infinite_ids = {
        "UP": "cslib:nat-infinite-trace:forward-method:v1",
        "DOWN": "cslib:nat-infinite-trace:backward-method:v1",
    }
    infinite_ablation = "NOT_CHECKED"
    infinite_revocation = "NOT_CHECKED"
    if infinite_done:
        active = set(summary["active_capability_ids"])
        if not set(infinite_ids.values()).issubset(active):
            raise AssertionError("QUALIFIED_NATIVE_INDUCTION_NOT_LIVE")
        for cap_id in infinite_ids.values():
            if "external:" + cap_id not in summary["discharged_obligation_ids"]:
                raise AssertionError("NATIVE_INFINITE_SOURCE_OBLIGATION_NOT_SOLVED")
        without = [
            path for path in bundles
            if path.relative_to(args.source_bundles).parts[0] != "native_unbounded"
        ]
        old = update_live_state(None, without)["summary"]
        if set(old["active_capability_ids"]) | set(infinite_ids.values()) != active:
            raise AssertionError("INFINITE_METHOD_CAUSAL_ADMISSION_MISMATCH")
        if set(old["obstruction_ids"]) != set(summary["obstruction_ids"]):
            raise AssertionError("INFINITE_METHOD_CHANGED_OLD_OBSTRUCTIONS")
        infinite_ablation = "PASS_BOTH_SOURCE_METHODS_CAUSALLY_ADMITTED"

        # Keep the backward program if the forward warrant is retracted:
        # its formal method works independently; only the SCIENTIFIC causal
        # development-chain claim must lose support.
        from realitygraph.flash import ExternalEventEnvelope
        from tempfile import TemporaryDirectory
        native_root = args.source_bundles / "native_unbounded"
        for direction, method_name in (("UP", "forward"), ("DOWN", "backward")):
            event = read(native_root / method_name / "event.json")
            raw = (
                '{"scope":"simulated_native_method_withdrawal",'
                '"method":"' + method_name + '","real_revocation":false}'
            ).encode()
            revoke = ExternalEventEnvelope.capability_revocation(
                event_id="cslib:infinite:" + method_name + ":simulated-withdrawal",
                repository=event["repository"],
                commit=event["commit"],
                authority_snapshot=event["authority_snapshot"],
                verifier_id=event["verifier_id"],
                source_evidence=raw,
                capability_id=infinite_ids[direction],
                reason="controlled native method source invalidation, NOT live evidence withdrawal"
            )
            with TemporaryDirectory(prefix="unbounded-method-withdrawal-") as temp:
                attack_root = Path(temp)
                (attack_root / "event.json").write_text(revoke.to_text())
                (attack_root / "evidence.json").write_bytes(raw)
                checked = update_live_state(None, list(bundles) + [attack_root])["summary"]
            expected_caps = active - {infinite_ids[direction]}
            if set(checked["active_capability_ids"]) != expected_caps:
                raise AssertionError("METHOD_LOCAL_REVOCATION_INVALID")
            if "external:" + infinite_ids[direction] not in checked["open_obligation_ids"]:
                raise AssertionError("METHOD_WITHDRAWAL_NOT_REOPENED")
            if set(checked["obstruction_ids"]) != set(summary["obstruction_ids"]):
                raise AssertionError("METHOD_REVOCATION_CORRUPTED_PRIOR_OBSTRUCTIONS")
        infinite_revocation = "PASS_SIMULATED_INDEPENDENT_METHOD_REVOCATIONS"

    # A source-mined theorem vocabulary was extended three times. Each
    # proof remains independently valid after earlier proof witnesses are
    # withdrawn; the development-history claim depends on all three.
    typed_done = "CSLIB_TYPED_METHOD_PASS" in runs and "typed_semantic" in manifest["emitters"]
    typed_stage_ids = {
        stage:"cslib:transport-method:"+stage.lower()+":v1"
        for stage in ("ACQUISITION","HELDOUT","GRAMMAR_REVISION")
    }
    typed_ablation = "NOT_CHECKED"
    typed_revocation = "NOT_CHECKED"
    if typed_done:
        ids = set(typed_stage_ids.values())
        live = set(summary["active_capability_ids"])
        if not ids.issubset(live):
            raise AssertionError("SOURCE_MINED_METHOD_PROOFS_NOT_LIVE")
        if not all("external:"+item in summary["discharged_obligation_ids"]
                   for item in ids):
            raise AssertionError("SOURCE_MINED_METHOD_OBLIGATIONS_NOT_DISCHARGED")
        from realitygraph.flash import ExternalEventEnvelope
        from tempfile import TemporaryDirectory
        source_root = args.source_bundles / "typed_semantic"
        for stage, capability_id in sorted(typed_stage_ids.items()):
            removed = [
                path for path in bundles
                if path != source_root / stage.lower()
            ]
            deleted = update_live_state(None, removed)["summary"]
            if set(deleted["active_capability_ids"]) != live - {capability_id}:
                raise AssertionError("TYPED_METHOD_ABLATION_NOT_ISOLATED:"+stage)
            if set(deleted["obstruction_ids"]) != set(summary["obstruction_ids"]):
                raise AssertionError("TYPED_METHOD_ABLATION_CHANGED_OBSTRUCTIONS")
            e = read(source_root / stage.lower() / "event.json")
            evidence = json.dumps({
                "controlled": True,
                "kind": "typed-grammar-" + stage.lower(),
                "real_revocation": False,
            }, sort_keys=True, separators=(",", ":")).encode()
            revoke = ExternalEventEnvelope.capability_revocation(
                event_id="cslib:transport:"+stage.lower()+":simulated-withdrawal",
                repository=e["repository"], commit=e["commit"],
                authority_snapshot=e["authority_snapshot"],
                verifier_id=e["verifier_id"], source_evidence=evidence,
                capability_id=capability_id,
                reason="simulation only: native proof preserved, live route removed",
            )
            with TemporaryDirectory(prefix="native-typed-method-") as temp:
                attack = Path(temp)
                (attack/"event.json").write_text(revoke.to_text())
                (attack/"evidence.json").write_bytes(evidence)
                withdrawn = update_live_state(None,list(bundles)+[attack])["summary"]
            if set(withdrawn["active_capability_ids"]) != live-{capability_id}:
                raise AssertionError("TYPED_REVOCATION_DID_NOT_ISOLATE:"+stage)
            if "external:"+capability_id not in withdrawn["open_obligation_ids"]:
                raise AssertionError("TYPED_METHOD_REVOCATION_NOT_REOPENED:"+stage)
            if set(withdrawn["obstruction_ids"]) != set(summary["obstruction_ids"]):
                raise AssertionError("TYPED_REVOCATION_CORRUPTED_OTHER_RESEARCH")
        typed_ablation = "PASS_THREE_INDEPENDENT_SOURCE_METHOD_ABLATIONS"
        typed_revocation = "PASS_THREE_SIMULATED_TYPED_METHOD_REVOCATIONS"

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
    native_method_node = None
    if method_done:
        source_qualification = runs["CSLIB_SOURCE_METHOD_PASS"]
        native_method_node = mt.Node("original_source_scoped_native_method", {
            "run": source_qualification["url"],
            "head": source_qualification["commit"],
            "capability_id": method_id,
            "original_sources": ["CslibTests/LTS.lean", "CslibTests/Bisimulation.lean"],
            "relation_pair_counts": [4, 24],
            "human_authored_general_extractor": True,
            "source_deletion_ablation": method_ablation,
            "controlled_revocation": method_revocation,
            "general_generator_invention": "UNKNOWN",
            "native_new_open_theorem": "UNKNOWN",
            "action_authorization": "NONE"},
            (anchors["CSLIB_SOURCE_METHOD_PASS"].id,
             roots[("emitters", "source_bisim")].id,
             flash_event.id))
        log = mt.append(log, native_method_node)
    native_infinite_nodes = {}
    native_infinite_history = None
    if infinite_done:
        for direction, method_key in sorted(infinite_ids.items()):
            node = mt.Node("native_unbounded_induction_proof_method", {
                "qualified_native_run": runs["CSLIB_NATIVE_UNBOUNDED_PASS"]["url"],
                "qualified_source_head": runs["CSLIB_NATIVE_UNBOUNDED_PASS"]["commit"],
                "scope": "original CSLib unbounded natural-number states, arbitrary trace length",
                "method_direction": direction,
                "capability_id": method_key,
                "source_deletion_ablation": infinite_ablation,
                "simulated_revocation": infinite_revocation,
                "human_defined_meta_grammar": True,
                "native_general_method_new_open_theorem": "NOT_CLAIMED",
                "action_authorization": "NONE"
            }, (anchors["CSLIB_NATIVE_UNBOUNDED_PASS"].id,
                roots[("emitters", "native_unbounded")].id,
                flash_event.id))
            log = mt.append(log, node)
            native_infinite_nodes[direction] = node
        native_infinite_history = mt.Node("source_feedback_method_development", {
            "old_finite_method": "UNKNOWN_UNSUPPORTED_NATIVE_INFINITE_STATE",
            "source_up_acquisition": "PASS",
            "source_distinct_up_transfer": "PASS",
            "downward_orientation_obstruction": "REJECTED_NATIVE_UP",
            "source_repair_from_frozen_method_grammar": "PASS",
            "generator_language_self_invention": "UNKNOWN",
            "general_autonomous_development": "UNKNOWN",
        }, (native_infinite_nodes["UP"].id, native_infinite_nodes["DOWN"].id))
        log = mt.append(log, native_infinite_history)
    native_typed_nodes = {}
    native_typed_history = None
    if typed_done:
        source_rules = {
            "ACQUISITION":"Cslib.FLTS.toLTS_mtr",
            "HELDOUT":"Cslib.FLTS.mtr_append_eq",
            "GRAMMAR_REVISION":"Cslib.LTS.toFLTS_mem_mtr",
        }
        for stage,capability_id in sorted(typed_stage_ids.items()):
            node = mt.Node("native_typed_transport_proof", {
                "scope":"exact frozen original source-bound CSLib goal",
                "stage":stage,"capability_id":capability_id,
                "new_source_theorem_primitive":source_rules[stage],
                "proof_program_deletion_ablation":typed_ablation,
                "typed_simulated_revocation":typed_revocation,
                "meta_generator_human_written":True,
                "source_theorems_preexisting":True,
                "scientific_L7":"UNKNOWN",
                "action_authorization":"NONE",
            }, (anchors["CSLIB_TYPED_METHOD_PASS"].id,
                roots[("emitters","typed_semantic")].id,
                flash_event.id))
            log = mt.append(log,node)
            native_typed_nodes[stage] = node
        native_typed_history = mt.Node("native_method_vocabulary_development", {
            "old_native_method":"Nat-interval successor/predecessor only",
            "earned_acquisition":"product to relational trace",
            "earned_heldout":"source compositional trace append",
            "earned_second_change":"set-valued lifted relation",
            "generated_source_methods":3,
            "general_self_generated_meta_substrate":"UNKNOWN",
            "full_equal_information_cost_advantage":"UNMEASURED",
            "independent_open_theorem":"NOT_CLAIMED",
        },tuple(native_typed_nodes[x].id for x in (
            "ACQUISITION","HELDOUT","GRAMMAR_REVISION")))
        log = mt.append(log,native_typed_history)
    future_dependencies = (qualification.id, source_catalogue.id, flash_event.id, residual.id)
    if native_done:
        future_dependencies += (native_node.id,)
    if method_done:
        future_dependencies += (native_method_node.id,)
    if infinite_done:
        future_dependencies += (native_infinite_history.id,)
    if typed_done:
        future_dependencies += (native_typed_history.id,)
    future_name = (
        "autonomous_source_distinct_native_generator_invention_still_open"
        if native_done else "diagnose_native_failure_and_test_new_semantic_repair")
    future_payload = {
        "candidate": future_name,
        "protected_target": bad["url"],
        "native_certificate_backend": "PASS_SCOPED" if native_done else "UNKNOWN",
        "source_native_method_transfer": "PASS_SCOPED" if method_done else "UNKNOWN",
        "source_native_parametric_induction": "PASS_SCOPED" if infinite_done else "UNKNOWN",
        "source_native_typed_method_language": "PASS_SCOPED" if typed_done else "UNKNOWN",
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
    if typed_done:
        typed_history_withdrawn = mt.append(log, mt.Node("revoke",{
            "target":native_typed_nodes["ACQUISITION"].id,
            "reason":"simulated cancellation of one native method-program acquisition",
        }))
        remaining=independent_live(typed_history_withdrawn)
        if native_typed_nodes["ACQUISITION"].id in remaining:
            raise AssertionError("TYPED_ACQUISITION_WARRANT_NOT_WITHDRAWN")
        if not all(native_typed_nodes[x].id in remaining
                   for x in ("HELDOUT","GRAMMAR_REVISION")):
            raise AssertionError("TYPED_LEAN_PROOF_WRONGLY_DEPENDS_ON_EARLIER_PROOF")
        if native_typed_history.id in remaining or frontier.id in remaining:
            raise AssertionError("UNSUPPORTED_METHOD_DEVELOPMENT_HISTORY_STILL_LIVE")
        assert set(mt.live_ids(typed_history_withdrawn))==remaining
    if infinite_done:
        method_science_revoked = mt.append(log, mt.Node("revoke", {
            "target": native_infinite_nodes["UP"].id,
            "reason": "simulated causal-development-support withdrawal",
        }))
        remaining = independent_live(method_science_revoked)
        if native_infinite_nodes["UP"].id in remaining:
            raise AssertionError("FORWARD_INDUCTION_DID_NOT_WITHDRAW")
        if native_infinite_nodes["DOWN"].id not in remaining:
            raise AssertionError("INDEPENDENT_BACKWARD_METHOD_WRONGLY_REVOKED")
        if native_infinite_history.id in remaining or frontier.id in remaining:
            raise AssertionError("SOURCE_FEEDBACK_CAUSAL_LINEAGE_WRONGLY_ACTIVE")
        if set(mt.live_ids(method_science_revoked)) != remaining:
            raise AssertionError("METATRON_INFINITE_METHOD_LIVENESS_INCORRECT")
    if method_done:
        method_withdrawal = mt.append(log, mt.Node("revoke", {
            "target": native_method_node.id,
            "reason": "simulated historical proof-support removal without revoking original Lean",
        }))
        after = independent_live(method_withdrawal)
        if native_method_node.id in after or frontier.id in after:
            raise AssertionError("METATRON_METHOD_SUPPORT_WITHDRAWAL_DID_NOT_RECLOSE")
        if qualification.id not in after or residual.id not in after:
            raise AssertionError("UNRELATED_WARRANT_REVOKED_WITH_METHOD")
        assert set(mt.live_ids(method_withdrawal)) == after
    if native_done:
        simulated_native_withdrawal = mt.append(log, mt.Node("revoke", {
            "target": native_node.id,
            "reason": "controlled removal of native proof support; historical Lean proof unchanged",
        }))
        native_live = independent_live(simulated_native_withdrawal)
        if native_node.id in native_live or frontier.id in native_live:
            raise AssertionError("NATIVE_PROOF_METATRON_WITHDRAWAL_NOT_PROPAGATED")
        if qualification.id not in native_live or residual.id not in native_live:
            raise AssertionError("NATIVE_WITHDRAWAL_REMOVED_UNRELATED_PROOF_AUTHORITY")
        assert set(mt.live_ids(simulated_native_withdrawal)) == native_live
        assert mt.loads(serialized) == log

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
        "source_native_typed_method_grammar": {
            "verdict":"PASS_SCOPED" if typed_done else "UNKNOWN",
            "active_scoped_capability_ids":list(typed_stage_ids.values()) if typed_done else [],
            "earned_method_rule_count":3 if typed_done else 0,
            "proof_plan_ablation":typed_ablation,
            "controlled_revocation":typed_revocation,
            "generator_substrate_human_written":True,
            "autonomous_meta_generator_invention":"UNKNOWN",
            "independently_open_new_theorem":"NOT_CLAIMED",
            "full_lifecycle_advantage":"UNMEASURED",
            "action_authorization":"NONE"
        },
        "source_native_parametric_induction": {
            "verdict": "PASS_SCOPED" if infinite_done else "UNKNOWN",
            "capability_ids": list(infinite_ids.values()) if infinite_done else [],
            "old_finite_grammar": "UNKNOWN_UNSUPPORTED_NATIVE_INFINITE_STATE",
            "new_parametric_induction": "PASS_NATIVE" if infinite_done else "UNKNOWN",
            "source_distinct_transfer": "PASS_NATIVE" if infinite_done else "UNKNOWN",
            "feedback_selected_reverse_method": "PASS_NATIVE" if infinite_done else "UNKNOWN",
            "causal_admission_ablation": infinite_ablation,
            "simulated_typed_revocation": infinite_revocation,
            "method_language_human_defined": True,
            "generator_self_invention": "UNKNOWN",
            "scientific_e2e_system": "UNKNOWN"},
        "source_native_method": {
            "verdict": "PASS_SCOPED" if method_done else "UNKNOWN",
            "capability_id": method_id if method_done else None,
            "source_deletion_ablation": method_ablation,
            "controlled_revocation": method_revocation,
            "human_authored_method": True,
            "scientific_autonomous_genesis": "UNKNOWN",
            "source_distinct_new_open_theorem": "UNKNOWN"},
        "native_scoped_proof": {
            "verdict": "PASS_SCOPED" if native_done else "UNKNOWN",
            "run": runs["CSLIB_NATIVE_PASS"]["url"] if native_done else None,
            "capability_id": native_id if native_done else None,
            "source_deletion_ablation": native_causal,
            "controlled_native_revocation": native_revocation,
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
            "source_distinct_upstream_native_semantics": "PASS_SCOPED" if method_done else "UNKNOWN",
            "native_typed_method_grammar_extension": "PASS_SCOPED" if typed_done else "UNKNOWN",
            "native_typed_method_source_ablation":typed_ablation,
            "native_typed_method_revocation":typed_revocation,
            "native_unbounded_parametric_induction": "PASS_SCOPED" if infinite_done else "UNKNOWN",
            "native_unbounded_causal_admission": infinite_ablation,
            "native_unbounded_independent_revocations": infinite_revocation,
            "source_method_causal_ablation": method_ablation,
            "source_method_typed_revocation": method_revocation,
            "native_semantic_event_ablation": native_causal,
            "native_typed_revocation_control": native_revocation,
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
