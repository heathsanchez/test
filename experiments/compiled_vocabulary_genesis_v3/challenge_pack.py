#!/usr/bin/env python3
"""Post-freeze challenges for V3 compiled vocabulary genesis."""
from __future__ import annotations

from typing import Any, Dict, Tuple

from basis import BOOL, PROD, Program, values
from kernel import Authority, Request


BB = PROD(BOOL, BOOL)


def exact_authority(input_ty, output_ty, fn, name: str) -> Authority:
    rows = tuple((x, fn(x)) for x in values(input_ty))

    def evaluate(p: Program) -> Dict[str, Any]:
        if p.input_ty != input_ty or p.output_ty != output_ty:
            return {
                "accepted": False,
                "protected_ok": True,
                "loss": len(rows),
                "witness": {"reason": "signature_mismatch", "target": name},
            }
        bad = []
        for x, y in rows:
            try:
                got = p.run(x)
            except Exception as exc:
                return {
                    "accepted": False,
                    "protected_ok": True,
                    "loss": len(rows),
                    "witness": {"reason": "runtime_error", "error": type(exc).__name__},
                }
            if got != y:
                bad.append({"input": x, "expected": y, "got": got})
        return {
            "accepted": not bad,
            "protected_ok": True,
            "loss": len(bad),
            "witness": {
                "target": name,
                "rows_checked": len(rows),
                "counterexamples": bad[:4],
            },
        }

    return Authority(
        input_ty=input_ty,
        output_ty=output_ty,
        evaluate=evaluate,
        coherent=lambda: True,
        residual=lambda p: {
            "kind": "finite_behavior_mismatch",
            "target": name,
            "input_type": str(input_ty),
            "output_type": str(output_ty),
        },
    )


XOR_AUTH = exact_authority(
    BB,
    BOOL,
    lambda x: bool(x[0] ^ x[1]),
    "unnamed_binary_behavior",
)

TRANSFER_AUTH = exact_authority(
    BB,
    BB,
    lambda x: (bool(x[0] ^ x[1]), bool(x[0])),
    "transfer_pair_behavior",
)


def requests() -> Dict[str, Request]:
    return {
        "recurrence_1": Request(
            "recurrence_1", XOR_AUTH, max_program_cost=8, search_complete=True
        ),
        "recurrence_2": Request(
            "recurrence_2", XOR_AUTH, max_program_cost=8, search_complete=True
        ),
        "transfer_tight": Request(
            "transfer_tight", TRANSFER_AUTH, max_program_cost=5, search_complete=True
        ),
        "transfer_unknown": Request(
            "transfer_unknown", TRANSFER_AUTH, max_program_cost=5, search_complete=False
        ),
        "transfer_deep": Request(
            "transfer_deep", TRANSFER_AUTH, max_program_cost=11, search_complete=True
        ),
    }
