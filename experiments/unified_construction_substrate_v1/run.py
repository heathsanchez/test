#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from challenge_pack import requests
from kernel import DevelopmentalKernel


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    req = requests()
    evidence = {
        "experiment": "unified_construction_substrate_v1",
        "freeze_commit": "9152e3e95e9352fed2eb85df859444d986eb0626",
        "post_freeze_challenge_pack": True,
        "hashes": {
            "PROTOCOL.md": sha256(HERE / "PROTOCOL.md"),
            "FREEZE.json": sha256(HERE / "FREEZE.json"),
            "mdc_l1.py": sha256(HERE / "mdc_l1.py"),
            "kernel.py": sha256(HERE / "kernel.py"),
            "challenge_pack.py": sha256(HERE / "challenge_pack.py"),
        },
        "results": {},
        "gates": {},
        "gaps": [],
    }

    # Independent kernels keep probes from contaminating one another,
    # except the explicit compile/reuse sequence.
    for name in [
        "no_change",
        "unknown_search",
        "certified_no_repair",
        "authority_conflict",
        "behavioral_duplicate",
        "contraction",
        "signature_expansion",
        "edit_generator",
    ]:
        k = DevelopmentalKernel()
        evidence["results"][name] = k.run(req[name])

    # Explicit development -> retained reuse sequence.
    k = DevelopmentalKernel()
    evidence["results"]["edit_not"] = k.run(req["edit_not"])
    evidence["results"]["reuse_not"] = k.run(req["reuse_not"])

    R = evidence["results"]
    G = evidence["gates"]

    # Constitutional/basic gates.
    G["no_change"] = R["no_change"]["status"] == "VERIFIED" and R["no_change"]["route"] == "NO_CHANGE"
    G["typed_edit_constructed"] = R["edit_not"]["status"] == "VERIFIED" and R["edit_not"]["route"] == "EDIT"
    G["compiled_reuse"] = R["reuse_not"]["status"] == "VERIFIED" and R["reuse_not"]["route"] == "REUSE"
    G["unknown_search_conservative"] = R["unknown_search"]["status"] == "UNKNOWN_SEARCH"
    G["certified_no_repair"] = R["certified_no_repair"]["status"] == "CERTIFIED_NO_REPAIR_IN_DECLARED_CLASS"
    G["authority_conflict"] = R["authority_conflict"]["status"] == "AUTHORITY_CONFLICT"

    # Full-protocol stretch gates.  These are intentionally demanding:
    # V1 should expose rather than hide missing machinery.
    G["behavioral_quotient_wired_into_search"] = R["behavioral_duplicate"]["status"] == "VERIFIED"
    current_contraction_cost = req["contraction"].current.cost
    G["contraction_on_verified_redundancy"] = (
        R["contraction"]["status"] == "VERIFIED"
        and int(R["contraction"].get("active_program_cost", current_contraction_cost)) < current_contraction_cost
    )
    G["signature_representation_growth"] = R["signature_expansion"]["status"] == "VERIFIED"
    G["edit_generator_constructed"] = R["edit_generator"]["status"] == "VERIFIED"

    # Interface-level probes for protocol requirements not yet represented in
    # DevelopmentRequest/KernelState.
    request_fields = set(req["no_change"].__dataclass_fields__)
    G["active_discriminator_interface"] = bool(
        {"future", "discriminator", "experiment"} & request_fields
    )

    # V1 uses a single lexicographic CostVector key rather than retaining a
    # true multiobjective Pareto frontier.
    G["pareto_frontier"] = False

    # Retained records do carry core proof/warrant metadata fields.
    from kernel import Retained
    retained_fields = set(Retained.__dataclass_fields__)
    G["proof_carrying_retention_schema"] = {
        "warrant", "scope", "dependencies", "revocation"
    }.issubset(retained_fields)

    gap_messages = {
        "behavioral_quotient_wired_into_search":
            "Semantic duplicate candidate programs are not quotient-collapsed in kernel search; XOR exposes UNKNOWN_CHOICE.",
        "contraction_on_verified_redundancy":
            "Kernel returns immediately on a sufficient present and never searches for a cheaper equivalent realization.",
        "signature_representation_growth":
            "Replacement/edit search preserves the current program signature, so representation/state expansion cannot change the interface.",
        "edit_generator_constructed":
            "First-class code reaches edit synthesis, but the current authority/kernel may leave competing edit-generators non-canonical and has no active discriminator loop.",
        "active_discriminator_interface":
            "UNKNOWN_CHOICE has no endogenous experiment/discriminator construction interface.",
        "pareto_frontier":
            "Cost is lexicographically scalarized; admissible set and Pareto lawful frontier are not represented separately.",
    }
    for key, msg in gap_messages.items():
        if not G[key]:
            evidence["gaps"].append({"gate": key, "detail": msg})

    core_names = [
        "no_change",
        "typed_edit_constructed",
        "compiled_reuse",
        "unknown_search_conservative",
        "certified_no_repair",
        "authority_conflict",
        "proof_carrying_retention_schema",
    ]
    full_names = list(G)
    evidence["core_pass"] = all(G[k] for k in core_names)
    evidence["full_protocol_pass"] = all(G[k] for k in full_names)
    evidence["verdict"] = (
        "VERIFIED_UNIFIED_CONSTRUCTION_SUBSTRATE_V1"
        if evidence["full_protocol_pass"]
        else (
            "PARTIAL_V1_CORE_PASSES_FULL_PROTOCOL_GAPS_EXPOSED"
            if evidence["core_pass"]
            else "V1_CORE_FAILURE"
        )
    )

    out = HERE / "evidence.json"
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2, sort_keys=True))

    # Scientific pass is strict: protocol-level gaps keep the workflow red.
    return 0 if evidence["full_protocol_pass"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise
