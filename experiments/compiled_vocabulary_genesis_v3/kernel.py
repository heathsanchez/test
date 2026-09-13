#!/usr/bin/env python3
"""Frozen V3 developmental compiler: verified recurrence -> anonymous macro."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from basis import (
    MacroAtom, Program, Synthesizer, Ty, contains_macro, macro_id, values, canon
)


Eval = Dict[str, Any]


PROMOTION_HITS = 2
PROMOTION_MIN_PROGRAM_COST = 6


@dataclass
class Authority:
    input_ty: Ty
    output_ty: Ty
    evaluate: Callable[[Program], Eval]
    coherent: Callable[[], bool] = lambda: True
    residual: Optional[Callable[[Optional[Program]], Any]] = None


@dataclass
class Request:
    request_id: str
    authority: Authority
    max_program_cost: int
    search_complete: bool


@dataclass
class Usage:
    input_ty: Ty
    output_ty: Ty
    table: Tuple[Any, ...]
    origins: List[str] = field(default_factory=list)
    program_digests: List[str] = field(default_factory=list)
    warrant_digests: List[str] = field(default_factory=list)


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def semantic_key(input_ty: Ty, output_ty: Ty, table: Sequence[Any]) -> str:
    return digest_json({
        "input": input_ty.data(),
        "output": output_ty.data(),
        "table": [canon(x) for x in table],
    })


class Kernel:
    def __init__(self) -> None:
        self.vocabulary: List[MacroAtom] = []
        self.usage: Dict[str, Usage] = {}

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
        p: Program,
        ev: Eval,
    ) -> Optional[MacroAtom]:
        # Do not recursively promote a program whose successful computation
        # already uses a promoted atom; V3 isolates genesis from primitives.
        if contains_macro(p.body):
            return None
        if p.cost < PROMOTION_MIN_PROGRAM_COST:
            return None

        table = tuple(p.behavior())
        key = semantic_key(p.input_ty, p.output_ty, table)
        warrant_digest = digest_json(ev.get("witness"))

        u = self.usage.get(key)
        if u is None:
            u = Usage(p.input_ty, p.output_ty, table)
            self.usage[key] = u

        if req.request_id not in u.origins:
            u.origins.append(req.request_id)
            u.program_digests.append(p.digest())
            u.warrant_digests.append(warrant_digest)

        if len(u.origins) < PROMOTION_HITS:
            return None

        mid = macro_id(p.input_ty, p.output_ty, table)
        existing = next((m for m in self.vocabulary if m.macro_id == mid), None)
        if existing is not None:
            return existing

        # Independent full finite replay certificate.
        xs = values(p.input_ty)
        replay = tuple(p.run(x) for x in xs)
        full_replay = replay == table
        if not full_replay:
            raise AssertionError("promotion replay mismatch")

        atom = MacroAtom(
            macro_id=mid,
            input_ty=p.input_ty,
            output_ty=p.output_ty,
            table=table,
            provenance=tuple(u.origins),
            source_program_digests=tuple(u.program_digests),
            full_replay=True,
            warrant_digests=tuple(u.warrant_digests),
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

        residual = (
            req.authority.residual(None)
            if req.authority.residual is not None
            else None
        )

        synth = Synthesizer(
            req.authority.input_ty,
            req.authority.output_ty,
            req.max_program_cost,
            self.vocabulary,
        )

        tested = 0
        accepted: List[Tuple[Program, Eval]] = []
        for p in synth.programs():
            tested += 1
            ev = self._norm(req.authority.evaluate(p))
            if self._accepted(ev):
                accepted.append((p, ev))

        if not accepted:
            return {
                "request_id": req.request_id,
                "status": (
                    "CERTIFIED_NO_PROGRAM_IN_DECLARED_CLASS"
                    if req.search_complete
                    else "UNKNOWN_SEARCH"
                ),
                "route": "STOP",
                "residual": residual,
                "tested_program_count": tested,
                "vocabulary_size": len(self.vocabulary),
                "vocabulary": [m.data() for m in self.vocabulary],
            }

        min_cost = min(p.cost for p, _ in accepted)
        minima = [(p, ev) for p, ev in accepted if p.cost == min_cost]

        # Search is behavior-quotiented, but multiple accepted behaviors could
        # still survive an underdetermined authority. Preserve that uncertainty.
        behavior_groups: Dict[str, Tuple[Program, Eval]] = {}
        for p, ev in minima:
            behavior_groups.setdefault(p.behavior_key(), (p, ev))

        if len(behavior_groups) > 1:
            return {
                "request_id": req.request_id,
                "status": "UNKNOWN_CHOICE",
                "route": "STOP",
                "frontier_size": len(behavior_groups),
                "minimum_cost": min_cost,
                "tested_program_count": tested,
                "vocabulary_size": len(self.vocabulary),
            }

        p, ev = next(iter(behavior_groups.values()))
        before_ids = {m.macro_id for m in self.vocabulary}
        promoted = self._promote_if_earned(req, p, ev)
        after_ids = {m.macro_id for m in self.vocabulary}
        newly_promoted = sorted(after_ids - before_ids)

        used_macro_ids = sorted(
            m.macro_id
            for m in self.vocabulary
            if contains_macro(p.body, m.macro_id)
        )

        return {
            "request_id": req.request_id,
            "status": "VERIFIED",
            "route": "MACRO" if used_macro_ids else "COMPOSE",
            "program_digest": p.digest(),
            "program_cost": p.cost,
            "program_behavior": [canon(x) for x in p.behavior()],
            "program_ast": p.body.to_data(),
            "evaluation": ev,
            "tested_program_count": tested,
            "used_macro_ids": used_macro_ids,
            "newly_promoted_macro_ids": newly_promoted,
            "promoted_macro": promoted.data() if newly_promoted and promoted is not None else None,
            "vocabulary_size": len(self.vocabulary),
            "vocabulary": [m.data() for m in self.vocabulary],
        }
