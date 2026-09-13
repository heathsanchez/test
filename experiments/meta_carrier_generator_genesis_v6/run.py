#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import MetaSynthesizer
from challenge_pack import requests
from kernel import Kernel


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def is_succ_current(rule_data):
    if not isinstance(rule_data, dict) or rule_data.get("op") != "succ":
        return False
    args = rule_data.get("args", [])
    return len(args) == 1 and args[0].get("op") == "current"


def is_succ_succ_current(rule_data):
    if not isinstance(rule_data, dict) or rule_data.get("op") != "succ":
        return False
    args = rule_data.get("args", [])
    return len(args) == 1 and is_succ_current(args[0])


def is_add_current_delta(rule_data):
    if not isinstance(rule_data, dict) or rule_data.get("op") != "add":
        return False
    args = rule_data.get("args", [])
    if len(args) != 2:
        return False
    return {args[0].get("op"), args[1].get("op")} == {"current", "delta"}


def main() -> int:
    req = requests()
    evidence = {
        "experiment": "meta_carrier_generator_genesis_v6",
        "scientific_freeze_commit": "b8417afd3d688c6b4d04291b5f332115a99ef12f",
        "post_freeze_challenges": True,
        "hashes": {
            "PROTOCOL.md": sha256(HERE / "PROTOCOL.md"),
            "FREEZE.json": sha256(HERE / "FREEZE.json"),
            "basis.py": sha256(HERE / "basis.py"),
            "kernel.py": sha256(HERE / "kernel.py"),
            "challenge_pack.py": sha256(HERE / "challenge_pack.py"),
        },
        "results": {},
        "gates": {},
    }

    warm = Kernel()

    e1 = warm.run(req["e1"])
    evidence["results"]["e1"] = e1
    compiled_after_e1 = (
        warm.compiled_rule.to_data() if warm.compiled_rule is not None else None
    )

    e2 = warm.run(req["e2"])
    evidence["results"]["e2"] = e2
    frontier_after_e2 = [r.to_data() for r in warm.frontier]
    compiled_absent_after_e2 = warm.compiled_rule is None

    e3 = warm.run(req["e3"])
    evidence["results"]["e3"] = e3
    compiled_after_e3 = (
        warm.compiled_rule.to_data() if warm.compiled_rule is not None else None
    )

    e4 = warm.run(req["e4_reuse"])
    evidence["results"]["e4_reuse"] = e4

    cold_zero = Kernel().run(req["e4_cold_zero"])
    evidence["results"]["e4_cold_zero"] = cold_zero

    cold_search = Kernel().run(req["e4_cold_search"])
    evidence["results"]["e4_cold_search"] = cold_search

    incomplete = Kernel().run(req["e2_incomplete"])
    evidence["results"]["e2_incomplete"] = incomplete

    ablated = warm.ablate_compiled_rule()
    ablation = warm.run(req["e4_cold_zero"])
    evidence["results"]["e4_after_ablation"] = ablation

    G = evidence["gates"]

    atomic_ops = {
        p.op
        for p in MetaSynthesizer(1).programs()
    }
    G["no_target_projection_primitive"] = (
        atomic_ops == {"current", "delta", "one"}
    )

    G["first_rule_is_succ_current"] = (
        e1.get("status") == "VERIFIED"
        and e1.get("route") == "META_SEARCH_UNIQUE"
        and e1.get("proposal_size") == 3
        and e1.get("carrier", {}).get("size") == 3
        and is_succ_current(e1.get("compiled_rule", {}).get("rule"))
        and is_succ_current(compiled_after_e1)
    )

    failed = e2.get("failed_compiled_rule")
    G["retained_first_rule_fails_on_second"] = (
        failed is not None
        and failed.get("proposal_size") == 4
        and failed.get("evaluation", {}).get("accepted") is False
        and is_succ_current(failed.get("rule", {}).get("rule"))
    )

    frontier_rules = [
        x.get("rule") for x in e2.get("frontier", [])
    ]
    G["second_encounter_preserves_two_behavior_frontier"] = (
        e2.get("status") == "VERIFIED"
        and e2.get("route") == "META_SEARCH_NONCANONICAL"
        and e2.get("proposal_size") == 5
        and e2.get("frontier_size") == 2
        and compiled_absent_after_e2
        and len(frontier_after_e2) == 2
        and any(is_succ_succ_current(r) for r in frontier_rules)
        and any(is_add_current_delta(r) for r in frontier_rules)
    )

    G["future_consequence_selects_add_rule"] = (
        e3.get("status") == "VERIFIED"
        and e3.get("route") == "FUTURE_SELECT"
        and e3.get("proposal_size") == 9
        and is_add_current_delta(e3.get("compiled_rule", {}).get("rule"))
        and is_add_current_delta(compiled_after_e3)
    )

    selected_prov = e3.get("compiled_rule", {}).get("provenance", [])
    G["selected_rule_has_cross_encounter_provenance"] = (
        selected_prov == ["e2", "e3"]
        or set(selected_prov) == {"e2", "e3"}
    )

    G["warm_reuses_compiled_meta_rule_zero_search"] = (
        e4.get("status") == "VERIFIED"
        and e4.get("route") == "META_REUSE"
        and e4.get("proposal_size") == 15
        and e4.get("carrier", {}).get("size") == 15
        and e4.get("tested_meta_program_count") == 0
        and is_add_current_delta(e4.get("compiled_rule", {}).get("rule"))
    )

    G["cold_zero_budget_stops_conservatively"] = (
        cold_zero.get("status") == "UNKNOWN_META_RULE"
        and cold_zero.get("tested_meta_program_count") == 0
    )

    G["cold_search_rediscovers_resolving_rule"] = (
        cold_search.get("status") == "VERIFIED"
        and cold_search.get("route") == "META_SEARCH_UNIQUE"
        and cold_search.get("proposal_size") == 15
        and is_add_current_delta(cold_search.get("compiled_rule", {}).get("rule"))
        and cold_search.get("tested_meta_program_count", 0) > 0
    )

    G["incomplete_meta_search_remains_unknown"] = (
        incomplete.get("status") == "UNKNOWN_META_SEARCH"
    )

    G["ablation_restores_zero_budget_failure"] = (
        ablated
        and ablation.get("status") == "UNKNOWN_META_RULE"
        and ablation.get("tested_meta_program_count") == 0
    )

    generated = [e1, e2, e3, e4, cold_search]
    G["all_generated_carriers_anonymous_and_verified"] = all(
        x.get("status") == "VERIFIED"
        and str(x.get("carrier", {}).get("carrier_id", "")).startswith("c_")
        and x.get("evaluation", {}).get("accepted") is True
        and x.get("evaluation", {}).get("protected_ok") is True
        and x.get("evaluation", {}).get("witness", {}).get("rows_checked")
            == x.get("carrier", {}).get("size")
        for x in generated
    )

    G["causal_meta_rule_compilation"] = (
        G["warm_reuses_compiled_meta_rule_zero_search"]
        and G["cold_zero_budget_stops_conservatively"]
        and G["ablation_restores_zero_budget_failure"]
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_META_GENERATOR_GENESIS_REVISION_SELECTION_AND_CAUSAL_REUSE"
        if evidence["full_pass"]
        else "META_CARRIER_GENERATOR_GENESIS_V6_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
