#!/usr/bin/env python3
"""Adversarial future-relative observation-basis falsifier.

Reuses original source/native transformer and FLASH V13 unchanged. This is an
informed follow-on to original 1301-world trial, not a blind held-out source.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run as base

FROZEN_RECORD_SHA256 = "f2701f8e61883de10c97f6de14ca629f66754329009aa83dd14f04794778dd62"
UPSTREAM_ARTIFACT_SHA256 = "464f2101e31a773837236cfd046819cf1667c7fb9b986a834532cc3e6708d26c"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def native_refine(db, old_worlds, records, protocol):
    old_world_digests = {base.hash_obj(w) for w in old_worlds}
    basis_features = [t + "." + c for t in ("t", "u") for c in ("a", "b", "c")]
    replacements = protocol["row_domain"]
    attempts = 0
    executions = 0
    for record in records:
        if record["status"] != "WARRANTED_BOUNDED_FINITE_EQUIVALENCE":
            continue
        selected_basis = record["minimal_observation_input"]["columns"]
        missing_features = sorted(set(basis_features) - set(selected_basis))
        query = record["original_sql"]
        optimized = record["optimized_sql"]
        ordered = "ORDER BY" in query.upper()
        for old_index, original_world in enumerate(old_worlds):
            for missing in missing_features:
                table, column = missing.split(".")
                k = ("a", "b", "c").index(column)
                for row_index, old_row in enumerate(original_world[table]):
                    for replacement in replacements:
                        if replacement == old_row[k]:
                            continue
                        new_world = copy.deepcopy(original_world)
                        new_world[table][row_index][k] = replacement
                        if base.hash_obj(new_world) in old_world_digests:
                            continue
                        assert base.world_projection(original_world, set(selected_basis)) == \
                               base.world_projection(new_world, set(selected_basis))
                        attempts += 1
                        base.load_world(db, original_world)
                        observed_before = base.observe(db, query, ordered)
                        optimized_before = base.observe(db, optimized, ordered)
                        base.load_world(db, new_world)
                        observed_after = base.observe(db, query, ordered)
                        optimized_after = base.observe(db, optimized, ordered)
                        executions += 4
                        if any(r["state"] != "NATIVE_OBSERVED"
                               for r in (observed_before, optimized_before, observed_after, optimized_after)):
                            continue
                        if observed_before != optimized_before or observed_after != optimized_after:
                            continue
                        if observed_before == observed_after:
                            continue
                        # One omitted feature just distinguished two previously
                        # basis-indistinguishable worlds. This is not a SQL bug.
                        signatures = []
                        for world in old_worlds:
                            base.load_world(db, world)
                            result = base.observe(db, query, ordered)
                            assert result["state"] == "NATIVE_OBSERVED"
                            signatures.append(base.hash_obj(result))
                        observed_new_digest = base.hash_obj(observed_after)
                        original_calculated = base.minimal_sufficient_basis(old_worlds, signatures)
                        assert original_calculated["columns"] == selected_basis, \
                            "HISTORICAL_MINIMAL_BASIS_NOT_REPRODUCED"
                        expanded_basis = base.minimal_sufficient_basis(
                            old_worlds + [new_world], signatures + [observed_new_digest])
                        assert expanded_basis["columns"] != selected_basis, \
                            "FUTURE_CONFLICT_FAILED_TO_REFINE_INTERFACE"
                        assert missing in expanded_basis["columns"], \
                            "DISCRIMINATING_FEATURE_NOT_PRESERVED"
                        return {
                            "target_query": record["id"],
                            "missing_observation": missing,
                            "world_original_index": old_index,
                            "old_world": original_world,
                            "new_world": new_world,
                            "old_world_not_repeated": True,
                            "old_basis": selected_basis,
                            "new_basis": expanded_basis["columns"],
                            "old_basis_fails_new_world": True,
                            "historical_scope": len(old_worlds),
                            "expanded_scope": len(old_worlds) + 1,
                            "old_native_result": observed_before,
                            "new_native_result": observed_after,
                            "original_and_optimized_agree_both_worlds": True,
                            "search_candidate_mutations": attempts,
                            "new_native_oracle_executions": executions,
                            "old_record_sql_sha": base.hash_obj(query),
                            "optimized_sql_sha": base.hash_obj(optimized),
                            "expanded_world_sha256": base.hash_obj(old_worlds + [new_world])
                        }
    return {"state": "UNKNOWN_NO_BASIS_COUNTEREXAMPLE",
            "search_candidate_mutations": attempts,
            "new_native_oracle_executions": executions}

def consequence_state(witness, protocol, future):
    sys.path.insert(0, str(base.FLASH))
    from flash_engine import RecloseEngine, EventRejected
    from reference_oracle import FullReference
    facts = ["receipt:old_1301", "receipt:future_1302"]
    fixture = {
      "version": "flash-v13-20261012",
      "scope": "sqlglot_native_future_refinement_no_future_universal_claim",
      "source_authorities": {
        "upstream": protocol["external_source"]["commit"],
        "old_digest": witness["old_record_sql_sha"],
        "expanded_world_digest": witness["expanded_world_sha256"]},
      "base_facts": ["source:qualified_at_immutable_sha", "sqlite:independent_native"],
      "allowed_events": {"promote": facts, "revoke": facts},
      "rules": [
        {"id": "native_historical_warrant", "when": [
          "source:qualified_at_immutable_sha", "sqlite:independent_native",
          "receipt:old_1301"], "then": "warrant:old_1301"},
        {"id": "native_expanded_warrant", "when": [
          "source:qualified_at_immutable_sha", "sqlite:independent_native",
          "receipt:future_1302"], "then": "warrant:future_1302"}
      ],
      "frontiers": [
        {"id": "past_scope", "budget": 2,
         "options": [
             {"id": "unknown", "when": [], "unless": [], "cost": 2},
             {"id": "use_past", "when": ["warrant:old_1301"], "unless": [], "cost": 0}
         ]},
        {"id": "expanded_future_scope", "budget": 2,
         "options": [
             {"id": "recheck_future", "when": [], "unless": [], "cost": 2},
             {"id": "use_refined_basis", "when": ["warrant:future_1302"], "unless": [], "cost": 0}
         ]}
      ], "events": [], "restart_after_event_index": 0,
      "adversarial_tests": []}
    inc = RecloseEngine(fixture)
    ref = FullReference(fixture)
    for fact in facts:
        ev = {"kind": "promote", "fact": fact, "authority": "synthetic_event"}
        inc.apply(ev)
        ref.apply(ev)
        assert inc.state() == ref.current
    assert inc.frontiers["past_scope"]["selected"] == "use_past"
    assert inc.frontiers["expanded_future_scope"]["selected"] == "use_refined_basis"
    snap = inc.snapshot()
    restored = RecloseEngine.restore(fixture, json.loads(base.dump(snap)))
    assert restored.state() == ref.current
    bad = copy.deepcopy(snap)
    bad["state"]["base"].append("FORGED_FUTURE")
    try:
        RecloseEngine.restore(fixture, bad)
        raise AssertionError("WRONG_SNAPSHOT_ACCEPTED")
    except EventRejected:
        pass
    change = {"kind": "revoke", "fact": "receipt:future_1302",
              "authority": "synthetic_revoker"}
    delta = restored.apply(change)
    ref.apply(change)
    assert restored.state() == ref.current
    assert restored.frontiers["past_scope"]["selected"] == "use_past"
    assert restored.frontiers["expanded_future_scope"]["selected"] == "recheck_future"
    assert "warrant:old_1301" in restored.active
    assert "warrant:future_1302" not in restored.active
    before = restored.snapshot()
    try:
        restored.apply({"kind": "promote", "fact": "receipt:future_1302",
                        "authority": "fake_upstream"})
        raise AssertionError("FORGED_FUTURE_ACCEPTED")
    except EventRejected:
        pass
    assert restored.snapshot() == before
    restore = {"kind": "promote", "fact": "receipt:future_1302", "authority": "synthetic_event"}
    restored.apply(restore)
    ref.apply(restore)
    assert restored.state() == ref.current
    assert restored.frontiers["expanded_future_scope"]["selected"] == "use_refined_basis"
    return {
      "status": "PASS_HISTORICAL_AND_FUTURE_SCOPE_SEPARATED",
      "historical_warrant_remains_active_on_new_scope_withdrawal": True,
      "new_scope_warrant_withdrawn_and_restored": True,
      "independent_full_batch_equal_each_step": True,
      "FLASH_source": future["parent_source_sha"] + "/FLASH_V13@" + protocol["flash_source"]["commit"],
      "simulated_revocation_not_authenticated_third_party": True,
      "retraction_changed": delta["changed_facts"],
      "retraction_touched_frontiers": delta["checked_frontiers"]
    }

def main():
    started = time.perf_counter()
    future = json.loads((HERE / "FUTURE_ADVERSARIAL_PROTOCOL.json").read_text())
    frozen = json.loads((HERE / "FROZEN_PROTOCOL.json").read_text())
    assert future["parent_source_sha"] == frozen["external_source"]["commit"]
    assert future["parent_artifact_sha256"] == UPSTREAM_ARTIFACT_SHA256
    assert sha(HERE / "out" / "records.json") == FROZEN_RECORD_SHA256, \
        "CHANGED_PRIOR_EVIDENCE_REPLAY"
    source_blob = base.check_pin(frozen)
    sys.path.insert(0, str(base.SOURCE))
    import sqlglot
    records = json.loads((HERE / "out" / "records.json").read_text())
    assert [r["id"] for r in records] == [f"q{i:02d}" for i in range(1, 15)]
    assert all(r["source_blob_sha"] == source_blob and
               r["upstream_sha"] == frozen["external_source"]["commit"]
               for r in records)
    worlds = base.worlds_of(frozen)
    db = base.connection()
    witness = native_refine(db, worlds, records, frozen)
    if witness.get("state") == "UNKNOWN_NO_BASIS_COUNTEREXAMPLE":
        report = {"status": witness["state"], "witness_search": witness}
    else:
        closure = consequence_state(witness, frozen, future)
        report = {
          "status": "PASS_FINITE_FUTURE_RELATIVE_META_REFINEMENT",
          "source_exact": frozen["external_source"]["commit"],
          "source_optimizer_blob": source_blob,
          "original_parent_run": future["parent_run"],
          "original_source_bound_artifact_sha256": future["parent_artifact_sha256"],
          "original_records_sha256": FROZEN_RECORD_SHA256,
          "original_query_count": len(records),
          "witness": witness,
          "incremental_graph": closure,
          "seconds": round(time.perf_counter() - started, 3),
          "strong_baseline": "An equal-information SQLite evaluator with one-cell search can obtain the same counterexample; no accuracy/time superiority established.",
          "scientific_boundary": "An originally minimum input projection over 1301 finite worlds failed on a new native state; representation repaired to a new minimum over 1302. Old 1301-state observation remains warranted. No universal SQL or future completeness theorem.",
          "generator_boundary": "Fixed one-cell change grammar selected by humans; program automatically found missing input feature and native counterexample, without a per-query correspondence.",
          "action_authorization": "NONE"
        }
    p = HERE / "out" / "future_report.json"
    p.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"],
                      "source": frozen["external_source"]["commit"],
                      "id": witness.get("target_query"),
                      "missing_feature": witness.get("missing_observation"),
                      "old_basis": witness.get("old_basis"),
                      "new_basis": witness.get("new_basis"),
                      "candidate_probes": witness["search_candidate_mutations"],
                      "new_native_executions": witness["new_native_oracle_executions"],
                      "seconds": report.get("seconds")}, indent=2))
    assert report["status"] == "PASS_FINITE_FUTURE_RELATIVE_META_REFINEMENT"

if __name__ == "__main__":
    main()
