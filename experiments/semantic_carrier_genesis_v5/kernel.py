#!/usr/bin/env python3
"""Frozen V5 developmental kernel for certified semantic carrier growth."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from basis import (
    CARRIER,
    CarrierRecord,
    IdentityProgram,
    Ty,
    TypeSynthesizer,
    active_ground_cardinalities,
    can_generate_cardinality,
    cardinality,
    obstruction_certificate,
    type_cost,
    values,
)


Eval = Dict[str, Any]


@dataclass
class Authority:
    evaluate: Callable[[Ty, IdentityProgram], Eval]
    coherent: Callable[[], bool] = lambda: True
    residual: Optional[Callable[[], Any]] = None


@dataclass
class Request:
    request_id: str
    authority: Authority
    max_type_cost: int
    search_complete: bool
    meta_max_carrier_size: int = 0


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


class Kernel:
    def __init__(self) -> None:
        self.learned_carriers: List[CarrierRecord] = []

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

    def ablate_carrier(self, atom_id: str) -> bool:
        before = len(self.learned_carriers)
        self.learned_carriers = [
            r for r in self.learned_carriers if r.ty.atom_id != atom_id
        ]
        return len(self.learned_carriers) != before

    def _search_object_basis(self, req: Request) -> Dict[str, Any]:
        synth = TypeSynthesizer(self.learned_carriers, req.max_type_cost)
        accepted = []
        tested = 0

        for ty in synth.types():
            tested += 1
            program = IdentityProgram(ty)
            ev = self._norm(req.authority.evaluate(ty, program))
            if self._accepted(ev):
                accepted.append((ty, program, ev))

        if not accepted:
            return {
                "accepted": False,
                "tested_type_count": tested,
            }

        min_cost = min(type_cost(ty) for ty, _, _ in accepted)
        minima = [
            (ty, p, ev)
            for ty, p, ev in accepted
            if type_cost(ty) == min_cost
        ]

        # Authority may explicitly declare accepted candidates consequence-equivalent.
        groups: Dict[str, Tuple[Ty, IdentityProgram, Eval]] = {}
        for ty, p, ev in minima:
            key = str(ev.get("equivalence_key", json.dumps(ty.data(), sort_keys=True)))
            old = groups.get(key)
            if old is None:
                groups[key] = (ty, p, ev)
            else:
                old_ty = old[0]
                if json.dumps(ty.data(), sort_keys=True) < json.dumps(
                    old_ty.data(), sort_keys=True
                ):
                    groups[key] = (ty, p, ev)

        if len(groups) > 1:
            return {
                "accepted": True,
                "noncanonical": True,
                "frontier": [
                    {
                        "type": ty.data(),
                        "cardinality": cardinality(ty),
                        "evaluation": ev,
                    }
                    for ty, _, ev in groups.values()
                ],
                "tested_type_count": tested,
                "min_cost": min_cost,
            }

        ty, program, ev = next(iter(groups.values()))
        return {
            "accepted": True,
            "noncanonical": False,
            "type": ty,
            "program": program,
            "evaluation": ev,
            "tested_type_count": tested,
            "min_cost": min_cost,
        }

    def run(self, req: Request) -> Eval:
        if not req.authority.coherent():
            return {
                "request_id": req.request_id,
                "status": "AUTHORITY_CONFLICT",
                "route": "STOP",
                "learned_carrier_count": len(self.learned_carriers),
            }

        residual = req.authority.residual() if req.authority.residual else {}
        object_result = self._search_object_basis(req)

        if object_result.get("accepted"):
            if object_result.get("noncanonical"):
                return {
                    "request_id": req.request_id,
                    "status": "UNKNOWN_CHOICE",
                    "route": "STOP",
                    "residual": residual,
                    "frontier": object_result["frontier"],
                    "frontier_size": len(object_result["frontier"]),
                    "tested_type_count": object_result["tested_type_count"],
                    "learned_carrier_count": len(self.learned_carriers),
                }

            ty = object_result["type"]
            ev = object_result["evaluation"]
            uses_learned = sorted(
                {
                    r.ty.atom_id
                    for r in self.learned_carriers
                    if r.ty.atom_id and r.ty.atom_id in json.dumps(ty.data())
                }
            )
            return {
                "request_id": req.request_id,
                "status": "VERIFIED",
                "route": "OBJECT_BASIS",
                "residual": residual,
                "type": ty.data(),
                "type_cost": object_result["min_cost"],
                "cardinality": cardinality(ty),
                "identity_program_digest": object_result["program"].digest(),
                "identity_rows_checked": len(values(ty)),
                "evaluation": ev,
                "used_learned_carrier_ids": uses_learned,
                "tested_type_count": object_result["tested_type_count"],
                "learned_carrier_count": len(self.learned_carriers),
                "learned_carriers": [r.data() for r in self.learned_carriers],
            }

        required = residual.get("required_cardinality")
        if type(required) is not int or required <= 0:
            return {
                "request_id": req.request_id,
                "status": (
                    "UNKNOWN_SEARCH"
                    if not req.search_complete
                    else "UNKNOWN"
                ),
                "route": "STOP",
                "residual": residual,
                "tested_type_count": object_result["tested_type_count"],
                "learned_carrier_count": len(self.learned_carriers),
            }

        cert = obstruction_certificate(required, self.learned_carriers)

        # If the active algebra can generate the required cardinality in principle
        # but the bounded object search did not reach it, this is search failure,
        # not expressive inadequacy.
        if cert["target_reachable"]:
            return {
                "request_id": req.request_id,
                "status": (
                    "UNKNOWN_SEARCH"
                    if not req.search_complete
                    else "CERTIFIED_NO_TYPE_IN_DECLARED_BOUNDED_SEARCH"
                ),
                "route": "STOP",
                "residual": residual,
                "obstruction_certificate": cert,
                "tested_type_count": object_result["tested_type_count"],
                "learned_carrier_count": len(self.learned_carriers),
            }

        # Structural expressive obstruction is now certified.
        if req.meta_max_carrier_size <= 0:
            return {
                "request_id": req.request_id,
                "status": "CERTIFIED_NO_TYPE_IN_CURRENT_BASIS",
                "route": "STOP",
                "residual": residual,
                "obstruction_certificate": cert,
                "tested_type_count": object_result["tested_type_count"],
                "learned_carrier_count": len(self.learned_carriers),
                "learned_carriers": [r.data() for r in self.learned_carriers],
            }

        # Generic bounded meta-search. No target-specific carrier constructor.
        meta_tested = 0
        accepted_meta: List[Tuple[Ty, IdentityProgram, Eval]] = []
        for size in range(1, req.meta_max_carrier_size + 1):
            candidate = CARRIER(size)
            meta_tested += 1
            program = IdentityProgram(candidate)
            ev = self._norm(req.authority.evaluate(candidate, program))
            if self._accepted(ev):
                accepted_meta.append((candidate, program, ev))

        if not accepted_meta:
            return {
                "request_id": req.request_id,
                "status": (
                    "CERTIFIED_NO_CARRIER_IN_META_BOUND"
                    if req.search_complete
                    else "UNKNOWN_EXPRESSIVITY"
                ),
                "route": "STOP",
                "residual": residual,
                "obstruction_certificate": cert,
                "tested_type_count": object_result["tested_type_count"],
                "meta_tested_carrier_count": meta_tested,
                "learned_carrier_count": len(self.learned_carriers),
            }

        # Canonical meta-generator produces at most one atom per cardinality.
        # If authority accepts several distinct cardinalities, preserve ambiguity.
        groups: Dict[int, Tuple[Ty, IdentityProgram, Eval]] = {}
        for ty, p, ev in accepted_meta:
            groups.setdefault(cardinality(ty), (ty, p, ev))

        if len(groups) > 1:
            return {
                "request_id": req.request_id,
                "status": "UNKNOWN_CHOICE",
                "route": "STOP",
                "residual": residual,
                "obstruction_certificate": cert,
                "frontier": [
                    {"type": ty.data(), "cardinality": cardinality(ty)}
                    for ty, _, _ in groups.values()
                ],
                "frontier_size": len(groups),
                "meta_tested_carrier_count": meta_tested,
            }

        ty, program, ev = next(iter(groups.values()))
        warrant_digest = digest_json(ev.get("witness"))
        record = CarrierRecord(
            ty=ty,
            origin=req.request_id,
            warrant_digest=warrant_digest,
            obstruction_certificate=cert,
        )
        if all(r.ty.atom_id != ty.atom_id for r in self.learned_carriers):
            self.learned_carriers.append(record)
            self.learned_carriers.sort(key=lambda r: r.ty.atom_id)

        return {
            "request_id": req.request_id,
            "status": "VERIFIED",
            "route": "BASIS_GROWTH",
            "residual": residual,
            "obstruction_certificate": cert,
            "type": ty.data(),
            "cardinality": cardinality(ty),
            "identity_program_digest": program.digest(),
            "identity_rows_checked": len(values(ty)),
            "evaluation": ev,
            "new_carrier": record.data(),
            "meta_tested_carrier_count": meta_tested,
            "tested_type_count": object_result["tested_type_count"],
            "learned_carrier_count": len(self.learned_carriers),
            "learned_carriers": [r.data() for r in self.learned_carriers],
        }
