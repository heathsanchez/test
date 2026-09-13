#!/usr/bin/env python3
"""Frozen V4 developmental compiler for parametric type constructors."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from basis import (
    IdentityProgram,
    Ty,
    TypeExpr,
    TypeMacro,
    TypeSynthesizer,
    contains_macro,
    eval_type_expr,
    type_macro_id,
    values,
)


Eval = Dict[str, Any]

PROMOTION_DISTINCT_BASES = 2
PROMOTION_MIN_FORMATION_COST = 3


@dataclass
class Authority:
    evaluate: Callable[[Ty, IdentityProgram], Eval]
    coherent: Callable[[], bool] = lambda: True
    residual: Optional[Callable[[], Any]] = None


@dataclass
class Request:
    request_id: str
    base_ty: Ty
    authority: Authority
    max_formation_cost: int
    search_complete: bool


@dataclass
class FormationUsage:
    definition: TypeExpr
    origins: List[str] = field(default_factory=list)
    base_types: List[Ty] = field(default_factory=list)
    formed_types: List[Ty] = field(default_factory=list)
    formation_digests: List[str] = field(default_factory=list)
    warrant_digests: List[str] = field(default_factory=list)


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


class Kernel:
    def __init__(self) -> None:
        self.vocabulary: List[TypeMacro] = []
        self.usage: Dict[str, FormationUsage] = {}

    @staticmethod
    def _norm(ev: Mapping[str, Any]) -> Eval:
        if "accepted" not in ev:
            raise ValueError("authority result missing accepted")
        out = dict(ev)
        out.setdefault("protected_ok", True)
        out.setdefault("loss", 0 if out["accepted"] else 1)
        return out

    @staticmethod
    def _accepted(ev: Mapping[str, Any]) -> bool:
        return bool(ev.get("accepted")) and bool(ev.get("protected_ok", True))

    def _promote_if_earned(
        self,
        req: Request,
        formation: TypeExpr,
        formed_ty: Ty,
        ev: Eval,
    ) -> Optional[TypeMacro]:
        # V4 isolates formation genesis from the primitive symbolic algebra.
        if contains_macro(formation):
            return None
        if formation.cost < PROMOTION_MIN_FORMATION_COST:
            return None

        key = formation.serial()
        u = self.usage.get(key)
        if u is None:
            u = FormationUsage(definition=formation)
            self.usage[key] = u

        # Distinct-base recurrence is mandatory. Multiple encounters on the
        # same base do not earn a parametric constructor.
        base_key = json.dumps(req.base_ty.data(), separators=(",", ":"))
        known_base_keys = {
            json.dumps(t.data(), separators=(",", ":")) for t in u.base_types
        }
        if base_key not in known_base_keys:
            u.origins.append(req.request_id)
            u.base_types.append(req.base_ty)
            u.formed_types.append(formed_ty)
            u.formation_digests.append(formation.digest())
            u.warrant_digests.append(digest_json(ev.get("witness")))

        if len(u.base_types) < PROMOTION_DISTINCT_BASES:
            return None

        mid = type_macro_id(formation)
        existing = next((m for m in self.vocabulary if m.macro_id == mid), None)
        if existing is not None:
            return existing

        # Independent replay of the exact symbolic definition on all earning
        # bases. The macro has no new primitive semantics; it is a verified
        # derived formation constructor.
        replay_ok = all(
            eval_type_expr(formation, b, ()) == formed
            for b, formed in zip(u.base_types, u.formed_types)
        )
        if not replay_ok:
            raise AssertionError("type-constructor promotion replay mismatch")

        atom = TypeMacro(
            macro_id=mid,
            definition=formation,
            provenance=tuple(u.origins),
            base_types=tuple(u.base_types),
            source_formation_digests=tuple(u.formation_digests),
            warrant_digests=tuple(u.warrant_digests),
            full_symbolic_replay=True,
        )
        self.vocabulary.append(atom)
        self.vocabulary.sort(key=lambda m: m.macro_id)
        return atom

    def ablate_macro(self, macro_id_value: str) -> bool:
        before = len(self.vocabulary)
        self.vocabulary = [m for m in self.vocabulary if m.macro_id != macro_id_value]
        return len(self.vocabulary) != before

    def run(self, req: Request) -> Eval:
        if not req.authority.coherent():
            return {
                "request_id": req.request_id,
                "status": "AUTHORITY_CONFLICT",
                "route": "STOP",
                "vocabulary_size": len(self.vocabulary),
            }

        residual = req.authority.residual() if req.authority.residual else None
        synth = TypeSynthesizer(req.max_formation_cost, self.vocabulary)

        tested = 0
        accepted: List[Tuple[TypeExpr, Ty, IdentityProgram, Eval]] = []

        for formation in synth.programs():
            tested += 1
            try:
                formed_ty = eval_type_expr(
                    formation, req.base_ty, self.vocabulary
                )
                program = IdentityProgram(formed_ty, formed_ty)
                ev = self._norm(req.authority.evaluate(formed_ty, program))
            except Exception as exc:
                ev = {
                    "accepted": False,
                    "protected_ok": True,
                    "loss": 1,
                    "witness": {"runtime_error": type(exc).__name__},
                }
                continue

            if self._accepted(ev):
                accepted.append((formation, formed_ty, program, ev))

        if not accepted:
            return {
                "request_id": req.request_id,
                "status": (
                    "CERTIFIED_NO_FORMATION_IN_DECLARED_CLASS"
                    if req.search_complete
                    else "UNKNOWN_SEARCH"
                ),
                "route": "STOP",
                "base_type": req.base_ty.data(),
                "residual": residual,
                "tested_formation_count": tested,
                "vocabulary_size": len(self.vocabulary),
                "vocabulary": [m.data() for m in self.vocabulary],
            }

        min_cost = min(f.cost for f, _, _, _ in accepted)
        minima = [x for x in accepted if x[0].cost == min_cost]

        # Distinct symbolic formations are genuinely non-canonical here.
        symbolic = {}
        for item in minima:
            symbolic.setdefault(item[0].serial(), item)

        if len(symbolic) > 1:
            return {
                "request_id": req.request_id,
                "status": "UNKNOWN_CHOICE",
                "route": "STOP",
                "frontier_size": len(symbolic),
                "minimum_formation_cost": min_cost,
                "frontier": [
                    {
                        "formation": f.to_data(),
                        "formed_type": t.data(),
                        "formation_cost": f.cost,
                    }
                    for f, t, _, _ in symbolic.values()
                ],
                "tested_formation_count": tested,
                "vocabulary_size": len(self.vocabulary),
            }

        formation, formed_ty, program, ev = next(iter(symbolic.values()))

        before_ids = {m.macro_id for m in self.vocabulary}
        promoted = self._promote_if_earned(
            req, formation, formed_ty, ev
        )
        after_ids = {m.macro_id for m in self.vocabulary}
        newly_promoted = sorted(after_ids - before_ids)
        used_macro_ids = sorted(
            m.macro_id
            for m in self.vocabulary
            if contains_macro(formation, m.macro_id)
        )

        return {
            "request_id": req.request_id,
            "status": "VERIFIED",
            "route": (
                "MACRO_FORMATION" if used_macro_ids else "PRIMITIVE_FORMATION"
            ),
            "base_type": req.base_ty.data(),
            "formed_type": formed_ty.data(),
            "formation": formation.to_data(),
            "formation_digest": formation.digest(),
            "formation_cost": formation.cost,
            "identity_program_digest": program.digest(),
            "identity_rows_checked": len(values(formed_ty)),
            "evaluation": ev,
            "tested_formation_count": tested,
            "used_macro_ids": used_macro_ids,
            "newly_promoted_macro_ids": newly_promoted,
            "promoted_macro": (
                promoted.data()
                if newly_promoted and promoted is not None
                else None
            ),
            "vocabulary_size": len(self.vocabulary),
            "vocabulary": [m.data() for m in self.vocabulary],
        }
