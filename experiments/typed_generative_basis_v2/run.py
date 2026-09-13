#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import BOOL, PROD
from challenge_pack import requests
from kernel import Kernel


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    req = requests()
    evidence = {
        "experiment": "typed_generative_basis_v2",
        "scientific_freeze_commit": "125da06b2228aa08c6b56b4c6c7a4d24ea261f93",
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

    # Isolated probes.
    for name in [
        "no_change",
        "grammar_growth",
        "signature_growth",
        "stateful_language",
        "contraction",
        "behavioral_quotient",
        "unknown_search",
        "certified_no_language",
        "authority_conflict",
    ]:
        evidence["results"][name] = Kernel().run(req[name])

    # Explicit compile -> reuse sequence.
    k = Kernel()
    evidence["results"]["compile_source"] = k.run(req["grammar_growth"])
    evidence["results"]["reuse"] = k.run(req["reuse"])

    R = evidence["results"]
    G = evidence["gates"]
    BB = PROD(BOOL, BOOL)

    G["no_change"] = (
        R["no_change"]["status"] == "VERIFIED"
        and R["no_change"]["route"] == "NO_CHANGE"
    )

    G["grammar_constructed"] = (
        R["grammar_growth"]["status"] == "VERIFIED"
        and R["grammar_growth"]["route"] == "GRAMMAR"
        and "xor" in R["grammar_growth"]["language"]["ops"]
    )

    G["signature_constructed"] = (
        R["signature_growth"]["status"] == "VERIFIED"
        and R["signature_growth"]["route"] == "SIGNATURE"
        and R["signature_growth"]["language"]["input"] == BB.data()
        and R["signature_growth"]["language"]["output"] == BOOL.data()
    )

    G["stateful_language_constructed"] = (
        R["stateful_language"]["status"] == "VERIFIED"
        and R["stateful_language"]["route"] == "SIGNATURE"
        and R["stateful_language"]["language"]["input"] == BB.data()
        and R["stateful_language"]["language"]["output"] == BB.data()
        and "xor" in R["stateful_language"]["language"]["ops"]
    )

    G["contraction"] = (
        R["contraction"]["status"] == "VERIFIED"
        and R["contraction"]["route"] == "CONTRACT"
        and R["contraction"]["program_cost"] == 1
        and R["contraction"]["language"]["ops"] == []
    )

    G["behavioral_quotient"] = (
        R["behavioral_quotient"]["status"] == "VERIFIED"
        and R["behavioral_quotient"].get("frontier_size") == 1
    )

    G["unknown_search"] = R["unknown_search"]["status"] == "UNKNOWN_SEARCH"
    G["certified_no_language"] = (
        R["certified_no_language"]["status"]
        == "CERTIFIED_NO_LANGUAGE_IN_DECLARED_BASIS_REGION"
    )
    G["authority_conflict"] = (
        R["authority_conflict"]["status"] == "AUTHORITY_CONFLICT"
    )
    G["compiled_reuse"] = (
        R["compile_source"]["status"] == "VERIFIED"
        and R["reuse"]["status"] == "VERIFIED"
        and R["reuse"]["route"] == "REUSE"
        and R["reuse"]["tested_language_count"] == 0
        and R["reuse"]["tested_program_count"] == 0
    )

    # The result must include at least three distinct verified task languages:
    # minimal unary, binary XOR, and stateful transition.
    verified_langs = {
        json.dumps(R[n]["language"], sort_keys=True)
        for n in ("no_change", "grammar_growth", "signature_growth", "stateful_language", "contraction")
        if R[n].get("status") == "VERIFIED"
    }
    evidence["distinct_verified_language_count"] = len(verified_langs)
    G["multiple_languages_from_one_basis"] = len(verified_langs) >= 3

    evidence["full_pass"] = all(G.values())
    evidence["verdict"] = (
        "VERIFIED_FROZEN_TYPED_GENERATIVE_BASIS_CONSTRUCTS_MULTIPLE_LANGUAGES"
        if evidence["full_pass"]
        else "TYPED_GENERATIVE_BASIS_V2_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
