#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import can_generate_cardinality
from challenge_pack import requests
from kernel import Kernel


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    req = requests()
    evidence = {
        "experiment": "semantic_carrier_genesis_v5",
        "scientific_freeze_commit": "9fdd35bf6e89755512a650bd05e8474665263010",
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

    # Growth must not happen when the old basis already suffices.
    k0 = Kernel()
    old_control = k0.run(req["old_basis_control"])
    evidence["results"]["old_basis_control"] = old_control

    # Main developmental trajectory.
    warm = Kernel()
    genesis = warm.run(req["genesis_3"])
    evidence["results"]["genesis_3"] = genesis

    learned = genesis.get("new_carrier")
    learned_id = None
    if learned is not None:
        t = learned.get("type", [])
        if isinstance(t, list) and len(t) >= 2:
            learned_id = t[1]

    warm_transfer = warm.run(req["transfer_6"])
    evidence["results"]["warm_transfer_6"] = warm_transfer

    bounded_unknown = warm.run(req["transfer_6_unknown"])
    evidence["results"]["warm_transfer_6_unknown"] = bounded_unknown

    # Cold control: even deep Product nesting cannot make cardinality 6.
    cold_deep = Kernel().run(req["cold_6_deep"])
    evidence["results"]["cold_6_deep"] = cold_deep

    # Causal ablation.
    ablated = False
    if learned_id is not None:
        ablated = warm.ablate_carrier(learned_id)
    ablation = warm.run(req["cold_6_deep"])
    evidence["results"]["ablation_6"] = ablation

    G = evidence["gates"]
    basis_src = (HERE / "basis.py").read_text().lower()
    kernel_src = (HERE / "kernel.py").read_text().lower()

    G["initial_object_basis_has_no_target_specific_carrier"] = (
        "carrier(3)" not in basis_src
        and "carrier(3)" not in kernel_src
        and "carrier(6)" not in basis_src
        and "carrier(6)" not in kernel_src
    )

    G["old_basis_solves_old_case_without_growth"] = (
        old_control.get("status") == "VERIFIED"
        and old_control.get("route") == "OBJECT_BASIS"
        and old_control.get("cardinality") == 4
        and old_control.get("learned_carrier_count") == 0
    )

    G["cardinality_3_structurally_impossible_before_growth"] = (
        can_generate_cardinality(3, []) is False
        and genesis.get("obstruction_certificate", {}).get("target_reachable") is False
        and genesis.get("obstruction_certificate", {}).get("complete") is True
    )

    G["generic_meta_growth_constructs_one_anonymous_carrier"] = (
        genesis.get("status") == "VERIFIED"
        and genesis.get("route") == "BASIS_GROWTH"
        and genesis.get("cardinality") == 3
        and genesis.get("learned_carrier_count") == 1
        and learned is not None
        and isinstance(learned_id, str)
        and learned_id.startswith("c_")
        and "three" not in learned_id.lower()
    )

    G["growth_was_authorized_by_certified_obstruction"] = (
        genesis.get("obstruction_certificate", {}).get("complete") is True
        and genesis.get("obstruction_certificate", {}).get("target_reachable") is False
        and genesis.get("obstruction_certificate", {}).get("active_ground_cardinalities") == [2]
    )

    G["learned_carrier_not_macro_expandable_in_old_basis"] = (
        can_generate_cardinality(3, []) is False
    )

    G["warm_transfer_constructs_cardinality_6_from_learned_basis"] = (
        warm_transfer.get("status") == "VERIFIED"
        and warm_transfer.get("route") == "OBJECT_BASIS"
        and warm_transfer.get("cardinality") == 6
        and learned_id in warm_transfer.get("used_learned_carrier_ids", [])
        and warm_transfer.get("type_cost") == 3
    )

    G["warm_transfer_exhaustively_verifies_identity"] = (
        warm_transfer.get("evaluation", {}).get("accepted") is True
        and warm_transfer.get("evaluation", {}).get("protected_ok") is True
        and warm_transfer.get("identity_rows_checked") == 6
        and warm_transfer.get("evaluation", {}).get("witness", {}).get("rows_checked") == 6
    )

    G["cold_initial_basis_cannot_generate_cardinality_6"] = (
        cold_deep.get("status") == "CERTIFIED_NO_TYPE_IN_CURRENT_BASIS"
        and cold_deep.get("obstruction_certificate", {}).get("target_reachable") is False
        and cold_deep.get("obstruction_certificate", {}).get("complete") is True
        and cold_deep.get("obstruction_certificate", {}).get("active_ground_cardinalities") == [2]
    )

    G["bounded_but_generable_failure_is_unknown_search"] = (
        bounded_unknown.get("status") == "UNKNOWN_SEARCH"
        and bounded_unknown.get("obstruction_certificate", {}).get("target_reachable") is True
    )

    G["ablation_restores_structural_impossibility"] = (
        ablated
        and ablation.get("status") == "CERTIFIED_NO_TYPE_IN_CURRENT_BASIS"
        and ablation.get("obstruction_certificate", {}).get("target_reachable") is False
    )

    G["causal_semantic_basis_expansion"] = (
        G["warm_transfer_constructs_cardinality_6_from_learned_basis"]
        and G["cold_initial_basis_cannot_generate_cardinality_6"]
        and G["ablation_restores_structural_impossibility"]
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_SEMANTIC_CARRIER_GENESIS_AND_CAUSAL_BASIS_EXPANSION"
        if evidence["full_pass"]
        else "SEMANTIC_CARRIER_GENESIS_V5_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
