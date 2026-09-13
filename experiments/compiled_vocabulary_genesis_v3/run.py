#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import PRIMITIVE_OPS, contains_macro
from challenge_pack import requests
from kernel import Kernel


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ast_has_macro(node) -> bool:
    if isinstance(node, dict):
        if node.get("op") == "macro":
            return True
        return any(ast_has_macro(v) for v in node.values())
    if isinstance(node, list):
        return any(ast_has_macro(v) for v in node)
    return False


def main() -> int:
    req = requests()
    evidence = {
        "experiment": "compiled_vocabulary_genesis_v3",
        "scientific_freeze_commit": "63c43296ff2e0942cb4437ba62e48ac15612fad8",
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

    # Warm developmental trajectory: construct the same expensive finite behavior twice.
    warm = Kernel()
    r1 = warm.run(req["recurrence_1"])
    r2 = warm.run(req["recurrence_2"])
    evidence["results"]["recurrence_1"] = r1
    evidence["results"]["recurrence_2"] = r2

    promoted_ids = r2.get("newly_promoted_macro_ids", [])
    promoted_id = promoted_ids[0] if len(promoted_ids) == 1 else None

    # New, structurally different task: learned behavior must occur as a
    # proper sub-computation of a product-valued program.
    warm_transfer = warm.run(req["transfer_tight"])
    evidence["results"]["warm_transfer"] = warm_transfer

    # Cold controls.
    cold_tight = Kernel().run(req["transfer_tight"])
    evidence["results"]["cold_transfer_tight"] = cold_tight

    cold_unknown = Kernel().run(req["transfer_unknown"])
    evidence["results"]["cold_transfer_unknown"] = cold_unknown

    cold_deep = Kernel().run(req["transfer_deep"])
    evidence["results"]["cold_transfer_deep"] = cold_deep

    # Explicit causal ablation: remove only the learned atom, keep the rest of
    # the warm kernel state, then replay the same tight transfer obligation.
    ablated = False
    if promoted_id is not None:
        ablated = warm.ablate_macro(promoted_id)
    ablation_transfer = warm.run(req["transfer_tight"])
    evidence["results"]["ablation_transfer"] = ablation_transfer

    G = evidence["gates"]

    G["xor_primitive_absent"] = "xor" not in PRIMITIVE_OPS

    G["first_composite_constructed"] = (
        r1.get("status") == "VERIFIED"
        and r1.get("route") == "COMPOSE"
        and r1.get("program_cost") == 8
        and r1.get("vocabulary_size") == 0
        and not r1.get("newly_promoted_macro_ids")
    )

    promoted = r2.get("promoted_macro")
    G["second_recurrence_promotes_one_atom"] = (
        r2.get("status") == "VERIFIED"
        and r2.get("route") == "COMPOSE"
        and len(promoted_ids) == 1
        and r2.get("vocabulary_size") == 1
        and promoted is not None
        and promoted.get("macro_id", "").startswith("m_")
    )

    G["promotion_is_anonymous"] = (
        promoted is not None
        and "xor" not in promoted.get("macro_id", "").lower()
        and "xor" not in json.dumps(promoted).lower()
    )

    G["promotion_has_full_replay_and_provenance"] = (
        promoted is not None
        and promoted.get("full_replay") is True
        and len(promoted.get("provenance", [])) == 2
        and set(promoted.get("provenance", [])) == {"recurrence_1", "recurrence_2"}
        and len(promoted.get("source_program_digests", [])) == 2
        and len(promoted.get("warrant_digests", [])) == 2
        and len(promoted.get("table", [])) == 4
    )

    G["warm_transfer_uses_promoted_atom"] = (
        warm_transfer.get("status") == "VERIFIED"
        and warm_transfer.get("route") == "MACRO"
        and warm_transfer.get("program_cost") == 5
        and promoted_id in warm_transfer.get("used_macro_ids", [])
        and ast_has_macro(warm_transfer.get("program_ast"))
        and warm_transfer.get("program_ast", {}).get("op") == "pair"
    )

    G["cold_tight_fails"] = (
        cold_tight.get("status") == "CERTIFIED_NO_PROGRAM_IN_DECLARED_CLASS"
    )

    G["cold_unknown_is_conservative"] = (
        cold_unknown.get("status") == "UNKNOWN_SEARCH"
    )

    G["cold_deep_recovers_composite"] = (
        cold_deep.get("status") == "VERIFIED"
        and cold_deep.get("route") == "COMPOSE"
        and cold_deep.get("program_cost") == 11
    )

    G["strict_cost_advantage"] = (
        warm_transfer.get("program_cost") == 5
        and cold_deep.get("program_cost") == 11
    )

    G["ablation_restores_obstruction"] = (
        ablated
        and ablation_transfer.get("status") == "CERTIFIED_NO_PROGRAM_IN_DECLARED_CLASS"
    )

    G["causal_new_reachability"] = (
        G["warm_transfer_uses_promoted_atom"]
        and G["cold_tight_fails"]
        and G["ablation_restores_obstruction"]
    )

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_COMPILED_VOCABULARY_GENESIS_AND_CAUSAL_TRANSFER"
        if evidence["full_pass"]
        else "COMPILED_VOCABULARY_GENESIS_V3_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
