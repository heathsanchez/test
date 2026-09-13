#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import BOOL, PROD
from challenge_pack import P, S, Q, duplicate_target, requests
from kernel import Kernel


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    req = requests()
    evidence = {
        "experiment": "compiled_type_constructor_genesis_v4",
        "scientific_freeze_commit": "d5222275fc35ae7ed518df8200f5c01d4d64ac54",
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
    r1 = warm.run(req["recurrence_1"])
    r2 = warm.run(req["recurrence_2"])
    evidence["results"]["recurrence_1"] = r1
    evidence["results"]["recurrence_2"] = r2

    promoted_ids = r2.get("newly_promoted_macro_ids", [])
    promoted_id = promoted_ids[0] if len(promoted_ids) == 1 else None

    warm_transfer = warm.run(req["transfer_tight"])
    evidence["results"]["warm_transfer"] = warm_transfer

    cold_tight = Kernel().run(req["transfer_tight"])
    evidence["results"]["cold_transfer_tight"] = cold_tight

    cold_unknown = Kernel().run(req["transfer_unknown"])
    evidence["results"]["cold_transfer_unknown"] = cold_unknown

    cold_deep = Kernel().run(req["transfer_deep"])
    evidence["results"]["cold_transfer_deep"] = cold_deep

    ablated = False
    if promoted_id is not None:
        ablated = warm.ablate_macro(promoted_id)
    ablation_transfer = warm.run(req["transfer_tight"])
    evidence["results"]["ablation_transfer"] = ablation_transfer

    G = evidence["gates"]
    basis_source = (HERE / "basis.py").read_text().lower()

    G["no_named_duplicate_constructor_primitive"] = all(
        token not in basis_source
        for token in ("duplicatetype", "pairstatetype", "memorytype")
    )

    G["first_formation_primitive"] = (
        r1.get("status") == "VERIFIED"
        and r1.get("route") == "PRIMITIVE_FORMATION"
        and r1.get("formation_cost") == 3
        and r1.get("vocabulary_size") == 0
        and not r1.get("newly_promoted_macro_ids")
        and r1.get("formed_type") == duplicate_target(P).data()
    )

    promoted = r2.get("promoted_macro")
    G["second_distinct_base_promotes_one_constructor"] = (
        r2.get("status") == "VERIFIED"
        and r2.get("route") == "PRIMITIVE_FORMATION"
        and r2.get("formation_cost") == 3
        and len(promoted_ids) == 1
        and r2.get("vocabulary_size") == 1
        and promoted is not None
    )

    G["promotion_is_anonymous_and_parametric"] = (
        promoted is not None
        and promoted.get("macro_id", "").startswith("t_")
        and "duplicate" not in json.dumps(promoted).lower()
        and "pair_state" not in json.dumps(promoted).lower()
        and promoted.get("definition", {}).get("op") == "prod"
        and [a.get("op") for a in promoted.get("definition", {}).get("args", [])]
            == ["var", "var"]
    )

    promoted_base_types = promoted.get("base_types", []) if promoted else []
    G["promotion_has_distinct_bases_and_provenance"] = (
        promoted is not None
        and promoted.get("full_symbolic_replay") is True
        and len(promoted_base_types) == 2
        and promoted_base_types[0] != promoted_base_types[1]
        and set(promoted.get("provenance", []))
            == {"recurrence_1", "recurrence_2"}
        and len(promoted.get("source_formation_digests", [])) == 2
        and len(promoted.get("warrant_digests", [])) == 2
    )

    G["transfer_base_is_unseen"] = (
        Q.data() not in promoted_base_types
        and Q != P
        and Q != S
    )

    G["warm_tight_uses_learned_constructor"] = (
        warm_transfer.get("status") == "VERIFIED"
        and warm_transfer.get("route") == "MACRO_FORMATION"
        and warm_transfer.get("formation_cost") == 2
        and promoted_id in warm_transfer.get("used_macro_ids", [])
        and warm_transfer.get("formed_type") == duplicate_target(Q).data()
    )

    G["warm_language_executes_and_verifies"] = (
        warm_transfer.get("evaluation", {}).get("accepted") is True
        and warm_transfer.get("evaluation", {}).get("protected_ok") is True
        and warm_transfer.get("evaluation", {}).get("witness", {}).get("rows_checked")
            == warm_transfer.get("identity_rows_checked")
        and warm_transfer.get("identity_rows_checked") == 64
    )

    G["cold_tight_fails"] = (
        cold_tight.get("status")
        == "CERTIFIED_NO_FORMATION_IN_DECLARED_CLASS"
    )

    G["cold_unknown_is_conservative"] = (
        cold_unknown.get("status") == "UNKNOWN_SEARCH"
    )

    G["cold_deep_recovers_primitive_formation"] = (
        cold_deep.get("status") == "VERIFIED"
        and cold_deep.get("route") == "PRIMITIVE_FORMATION"
        and cold_deep.get("formation_cost") == 3
        and cold_deep.get("formed_type") == duplicate_target(Q).data()
    )

    G["strict_formation_cost_advantage"] = (
        warm_transfer.get("formation_cost") == 2
        and cold_deep.get("formation_cost") == 3
    )

    G["ablation_restores_obstruction"] = (
        ablated
        and ablation_transfer.get("status")
            == "CERTIFIED_NO_FORMATION_IN_DECLARED_CLASS"
    )

    G["causal_new_signature_reachability"] = (
        G["warm_tight_uses_learned_constructor"]
        and G["cold_tight_fails"]
        and G["ablation_restores_obstruction"]
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_COMPILED_TYPE_CONSTRUCTOR_GENESIS_AND_CAUSAL_SIGNATURE_TRANSFER"
        if evidence["full_pass"]
        else "COMPILED_TYPE_CONSTRUCTOR_GENESIS_V4_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
