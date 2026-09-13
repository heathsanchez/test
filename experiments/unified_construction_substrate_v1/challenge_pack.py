#!/usr/bin/env python3
"""Post-freeze heterogeneous challenge pack for unified construction substrate V1.

This file was added *after* FREEZE.json.  It may use the frozen public API but
must not add host-language repair operators to the substrate/kernel.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from mdc_l1 import (
    BOOL, CODE, Bin, CodeNot, ConstBool, If, Program, Var
)
from kernel import Authority, DevelopmentRequest


def truth_authority(
    required_inputs: Tuple[Any, ...],
    rows: Sequence[Tuple[Tuple[Any, ...], Any]],
) -> Authority:
    """Exact finite external authority for a truth table."""
    def evaluate(p: Program) -> Dict[str, Any]:
        if p.inputs != required_inputs or p.output != BOOL:
            return {
                "accepted": False,
                "protected_ok": True,
                "loss": len(rows),
                "witness": {"reason": "signature_mismatch"},
            }
        bad = []
        for x, y in rows:
            try:
                got = p.run(*x)
            except Exception as exc:
                return {
                    "accepted": False,
                    "protected_ok": True,
                    "loss": len(rows),
                    "witness": {"reason": "runtime_error", "error": type(exc).__name__},
                }
            if got != y:
                bad.append({"input": list(x), "expected": y, "got": got})
        return {
            "accepted": not bad,
            "protected_ok": True,
            "loss": len(bad),
            "witness": {"checked_rows": len(rows), "counterexamples": bad[:4]},
        }

    return Authority(
        evaluate=evaluate,
        coherent=lambda: True,
        residual=lambda p: {"kind": "finite_table_mismatch", "rows": len(rows)},
    )


def bool_rows(fn) -> List[Tuple[Tuple[bool, bool], bool]]:
    out = []
    for a in (False, True):
        for b in (False, True):
            out.append(((a, b), bool(fn(a, b))))
    return out


def unary_rows(fn) -> List[Tuple[Tuple[bool], bool]]:
    return [((x,), bool(fn(x))) for x in (False, True)]


def p_xor() -> Program:
    return Program((BOOL, BOOL), BOOL, Bin("xor", Var(0, BOOL), Var(1, BOOL)))


def p_x() -> Program:
    return Program((BOOL,), BOOL, Var(0, BOOL))


def p_x2() -> Program:
    return Program((BOOL, BOOL), BOOL, Var(0, BOOL))


def p_verbose_x() -> Program:
    return Program(
        (BOOL,),
        BOOL,
        If(Var(0, BOOL), ConstBool(True), ConstBool(False)),
    )


def identity_edit() -> Program:
    task_ty = CODE((BOOL,), BOOL)
    return Program((task_ty,), task_ty, Var(0, task_ty))


def requests() -> Dict[str, DevelopmentRequest]:
    xor_auth = truth_authority((BOOL, BOOL), bool_rows(lambda a, b: a ^ b))
    not_auth = truth_authority((BOOL,), unary_rows(lambda x: not x))
    x_auth = truth_authority((BOOL,), unary_rows(lambda x: x))

    # Meta-authority: candidate itself is an edit Code[Bool->Bool] -> Code[Bool->Bool].
    task_ty = CODE((BOOL,), BOOL)
    identity_task = p_x()

    def eval_edit_program(edit_program: Program) -> Dict[str, Any]:
        if edit_program.inputs != (task_ty,) or edit_program.output != task_ty:
            return {"accepted": False, "protected_ok": True, "loss": 2}
        try:
            produced = edit_program.run(identity_task)
        except Exception as exc:
            return {
                "accepted": False,
                "protected_ok": True,
                "loss": 2,
                "witness": {"error": type(exc).__name__},
            }
        return not_auth.evaluate(produced)

    edit_auth = Authority(
        evaluate=eval_edit_program,
        coherent=lambda: True,
        residual=lambda p: {"kind": "edit_program_inadequate"},
    )

    conflict = Authority(
        evaluate=lambda p: {"accepted": False, "protected_ok": False, "loss": 1},
        coherent=lambda: False,
        residual=lambda p: {"kind": "authority_conflict"},
    )

    # Representation/signature expansion target.  Current has one input; any
    # lawful solution needs two.  The V1 kernel searches only same-signature
    # replacements/edits, so this should expose the signature-change gap.
    rep_auth = truth_authority(
        (BOOL, BOOL),
        bool_rows(lambda observation, history: observation ^ history),
    )

    return {
        "no_change": DevelopmentRequest(
            "no_change", p_xor(), xor_auth,
            max_object_cost=3, max_edit_cost=2,
            object_search_complete=True, edit_search_complete=True,
        ),
        "edit_not": DevelopmentRequest(
            "edit_not", p_x(), not_auth,
            max_object_cost=0, max_edit_cost=2,
            object_search_complete=True, edit_search_complete=True,
            allow_replacements=False, allow_edits=True,
        ),
        "reuse_not": DevelopmentRequest(
            "reuse_not", p_x(), not_auth,
            max_object_cost=0, max_edit_cost=0,
            object_search_complete=False, edit_search_complete=False,
            allow_replacements=False, allow_edits=False,
        ),
        "unknown_search": DevelopmentRequest(
            "unknown_search", p_x2(), xor_auth,
            max_object_cost=1, max_edit_cost=0,
            object_search_complete=False, edit_search_complete=True,
            allow_replacements=True, allow_edits=False,
        ),
        "certified_no_repair": DevelopmentRequest(
            "certified_no_repair", p_x2(), xor_auth,
            max_object_cost=1, max_edit_cost=0,
            object_search_complete=True, edit_search_complete=True,
            allow_replacements=True, allow_edits=False,
        ),
        "authority_conflict": DevelopmentRequest(
            "authority_conflict", p_x(), conflict,
            max_object_cost=2, max_edit_cost=2,
            object_search_complete=True, edit_search_complete=True,
        ),
        "behavioral_duplicate": DevelopmentRequest(
            "behavioral_duplicate", p_x2(), xor_auth,
            max_object_cost=3, max_edit_cost=0,
            object_search_complete=True, edit_search_complete=True,
            allow_replacements=True, allow_edits=False,
        ),
        "contraction": DevelopmentRequest(
            "contraction", p_verbose_x(), x_auth,
            max_object_cost=2, max_edit_cost=0,
            object_search_complete=True, edit_search_complete=True,
            allow_replacements=True, allow_edits=False,
        ),
        "signature_expansion": DevelopmentRequest(
            "signature_expansion", p_x(), rep_auth,
            max_object_cost=5, max_edit_cost=3,
            object_search_complete=True, edit_search_complete=True,
            allow_replacements=True, allow_edits=True,
        ),
        "edit_generator": DevelopmentRequest(
            "edit_generator", identity_edit(), edit_auth,
            max_object_cost=2, max_edit_cost=0,
            object_search_complete=True, edit_search_complete=True,
            allow_replacements=True, allow_edits=False,
        ),
    }
