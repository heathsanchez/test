#!/usr/bin/env python3
"""Post-freeze challenge pack for Typed Generative Basis V2."""
from __future__ import annotations

from typing import Any, Dict, Tuple

from basis import (
    BOOL, PROD, B, Bin, Fst, If, Language, Pair, Program, Snd, Var, values
)
from kernel import Authority, Request


BB = PROD(BOOL, BOOL)


def identity_bool() -> Program:
    L = Language(BOOL, BOOL, frozenset())
    return Program(L, Var(BOOL))


def verbose_identity() -> Program:
    L = Language(BOOL, BOOL, frozenset({"not", "and", "or", "xor", "if"}))
    return Program(L, If(Var(BOOL), B(True), B(False)))


def pair_first() -> Program:
    L = Language(BB, BOOL, frozenset())
    return Program(L, Fst(Var(BB)))


def pair_and() -> Program:
    L = Language(BB, BOOL, frozenset({"xor"}))
    x = Var(BB)
    # Deliberately wrong current program inside the right language.
    return Program(L, Fst(x))


def table_authority(input_ty, output_ty, fn, name: str) -> Authority:
    rows = tuple((x, fn(x)) for x in values(input_ty))

    def evaluate(lang: Language, p: Program) -> Dict[str, Any]:
        if lang.input_ty != input_ty or lang.output_ty != output_ty:
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
        evaluate=evaluate,
        coherent=lambda: True,
        residual=lambda lang, p: {
            "kind": "finite_behavior_mismatch",
            "target": name,
            "required_input_type": str(input_ty),
            "required_output_type": str(output_ty),
        },
    )


def authorities():
    return {
        "id": table_authority(BOOL, BOOL, lambda x: x, "identity"),
        "xor": table_authority(BB, BOOL, lambda x: bool(x[0] ^ x[1]), "xor"),
        "state": table_authority(
            BB,
            BB,
            lambda x: (bool(x[0] ^ x[1]), bool(x[0])),
            "state_transition",
        ),
    }


def requests() -> Dict[str, Request]:
    A = authorities()

    conflict = Authority(
        evaluate=lambda lang, p: {
            "accepted": False,
            "protected_ok": False,
            "loss": 1,
        },
        coherent=lambda: False,
        residual=lambda lang, p: {"kind": "authority_conflict"},
    )

    # Current language cannot express XOR with no Boolean semantic operators.
    grammar_current = pair_first()

    # Current signature has one Bool input; target authority requires Bool×Bool.
    sig_current = Program(
        Language(BOOL, BOOL, frozenset({"xor"})),
        Var(BOOL),
    )

    # Stateful target changes both input/output types and requires XOR.
    state_current = identity_bool()

    return {
        "no_change": Request(
            "no_change", identity_bool(), A["id"],
            max_type_depth=1, max_language_edit=0, max_program_cost=2,
            search_complete=True,
        ),
        "grammar_growth": Request(
            "grammar_growth", grammar_current, A["xor"],
            max_type_depth=1, max_language_edit=1, max_program_cost=5,
            search_complete=True,
        ),
        "signature_growth": Request(
            "signature_growth", sig_current, A["xor"],
            max_type_depth=1, max_language_edit=1, max_program_cost=5,
            search_complete=True,
        ),
        "stateful_language": Request(
            "stateful_language", state_current, A["state"],
            max_type_depth=1, max_language_edit=3, max_program_cost=8,
            search_complete=True,
        ),
        "contraction": Request(
            "contraction", verbose_identity(), A["id"],
            max_type_depth=1, max_language_edit=5, max_program_cost=4,
            search_complete=True,
        ),
        "behavioral_quotient": Request(
            "behavioral_quotient", pair_and(), A["xor"],
            max_type_depth=1, max_language_edit=0, max_program_cost=5,
            search_complete=True,
        ),
        "unknown_search": Request(
            "unknown_search", state_current, A["state"],
            max_type_depth=1, max_language_edit=1, max_program_cost=5,
            search_complete=False,
        ),
        "certified_no_language": Request(
            "certified_no_language", state_current, A["state"],
            max_type_depth=1, max_language_edit=1, max_program_cost=5,
            search_complete=True,
        ),
        "authority_conflict": Request(
            "authority_conflict", identity_bool(), conflict,
            max_type_depth=1, max_language_edit=3, max_program_cost=5,
            search_complete=True,
        ),
        # Used only after grammar_growth has compiled the XOR language/program.
        "reuse": Request(
            "reuse", grammar_current, A["xor"],
            max_type_depth=0, max_language_edit=0, max_program_cost=1,
            search_complete=False,
        ),
    }
