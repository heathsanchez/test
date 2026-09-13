#!/usr/bin/env python3
"""Post-freeze challenges for V4 compiled type-constructor genesis."""
from __future__ import annotations

from typing import Any, Dict

from basis import BOOL, PROD, IdentityProgram, Ty, values
from kernel import Authority, Request


P = PROD(BOOL, BOOL)
S = PROD(BOOL, P)
Q = PROD(P, BOOL)


def duplicate_target(base: Ty) -> Ty:
    # Challenge-side target only. The frozen kernel is not given this function.
    return PROD(base, base)


def identity_authority(target_ty: Ty, name: str) -> Authority:
    rows = values(target_ty)

    def evaluate(formed_ty: Ty, program: IdentityProgram) -> Dict[str, Any]:
        if formed_ty != target_ty:
            return {
                "accepted": False,
                "protected_ok": True,
                "loss": len(rows),
                "witness": {
                    "reason": "signature_mismatch",
                    "target": name,
                    "expected_type": target_ty.data(),
                    "got_type": formed_ty.data(),
                },
            }

        bad = []
        for x in rows:
            try:
                got = program.run(x)
            except Exception as exc:
                return {
                    "accepted": False,
                    "protected_ok": True,
                    "loss": len(rows),
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
            "witness": {
                "target": name,
                "rows_checked": len(rows),
                "identity_failures": bad[:4],
                "verified_type": target_ty.data(),
            },
        }

    return Authority(
        evaluate=evaluate,
        coherent=lambda: True,
        residual=lambda: {
            "kind": "finite_signature_obstruction",
            "target": name,
            "required_type": target_ty.data(),
        },
    )


A1 = identity_authority(duplicate_target(P), "formation_recurrence_1")
A2 = identity_authority(duplicate_target(S), "formation_recurrence_2")
AT = identity_authority(duplicate_target(Q), "unseen_base_transfer")


def requests():
    return {
        "recurrence_1": Request(
            "recurrence_1",
            base_ty=P,
            authority=A1,
            max_formation_cost=3,
            search_complete=True,
        ),
        "recurrence_2": Request(
            "recurrence_2",
            base_ty=S,
            authority=A2,
            max_formation_cost=3,
            search_complete=True,
        ),
        "transfer_tight": Request(
            "transfer_tight",
            base_ty=Q,
            authority=AT,
            max_formation_cost=2,
            search_complete=True,
        ),
        "transfer_unknown": Request(
            "transfer_unknown",
            base_ty=Q,
            authority=AT,
            max_formation_cost=2,
            search_complete=False,
        ),
        "transfer_deep": Request(
            "transfer_deep",
            base_ty=Q,
            authority=AT,
            max_formation_cost=3,
            search_complete=True,
        ),
    }
