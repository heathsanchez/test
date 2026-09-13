#!/usr/bin/env python3
"""Post-freeze challenges for V5 semantic carrier genesis."""
from __future__ import annotations

from typing import Any, Dict

from basis import IdentityProgram, Ty, cardinality, values
from kernel import Authority, Request


def cardinality_authority(n: int, name: str) -> Authority:
    n = int(n)

    def evaluate(ty: Ty, program: IdentityProgram) -> Dict[str, Any]:
        got_n = cardinality(ty)
        if got_n != n:
            return {
                "accepted": False,
                "protected_ok": True,
                "loss": abs(got_n - n),
                "equivalence_key": f"cardinality:{got_n}",
                "witness": {
                    "reason": "cardinality_mismatch",
                    "target": name,
                    "required_cardinality": n,
                    "got_cardinality": got_n,
                },
            }

        bad = []
        rows = values(ty)
        for x in rows:
            try:
                got = program.run(x)
            except Exception as exc:
                return {
                    "accepted": False,
                    "protected_ok": True,
                    "loss": n,
                    "equivalence_key": f"cardinality:{got_n}",
                    "witness": {
                        "reason": "runtime_error",
                        "error": type(exc).__name__,
                    },
                }
            if got != x:
                bad.append({"input": x, "got": got})

        return {
            "accepted": not bad,
            "protected_ok": True,
            "loss": len(bad),
            "equivalence_key": f"cardinality:{n}",
            "witness": {
                "target": name,
                "required_cardinality": n,
                "rows_checked": len(rows),
                "identity_failures": bad[:4],
            },
        }

    return Authority(
        evaluate=evaluate,
        coherent=lambda: True,
        residual=lambda: {
            "kind": "required_finite_carrier_cardinality",
            "target": name,
            "required_cardinality": n,
        },
    )


def requests():
    return {
        "old_basis_control": Request(
            "old_basis_control",
            authority=cardinality_authority(4, "old_basis_control"),
            max_type_cost=3,
            search_complete=True,
            meta_max_carrier_size=5,
        ),
        "genesis_3": Request(
            "genesis_3",
            authority=cardinality_authority(3, "new_semantic_carrier"),
            max_type_cost=7,
            search_complete=True,
            meta_max_carrier_size=5,
        ),
        "transfer_6": Request(
            "transfer_6",
            authority=cardinality_authority(6, "post_genesis_transfer"),
            max_type_cost=3,
            search_complete=True,
            meta_max_carrier_size=0,
        ),
        "transfer_6_unknown": Request(
            "transfer_6_unknown",
            authority=cardinality_authority(6, "bounded_incomplete_transfer"),
            max_type_cost=1,
            search_complete=False,
            meta_max_carrier_size=0,
        ),
        "cold_6_deep": Request(
            "cold_6_deep",
            authority=cardinality_authority(6, "cold_impossibility_control"),
            max_type_cost=9,
            search_complete=True,
            meta_max_carrier_size=0,
        ),
    }
