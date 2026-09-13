#!/usr/bin/env python3
"""Frozen V6 kernel: develop the carrier-specification meta-rule itself."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from basis import (
    Carrier,
    MetaExpr,
    MetaSynthesizer,
    behavior_key,
    eval_meta,
    materialize_carrier,
)


Eval = Dict[str, Any]


@dataclass
class Authority:
    evaluate: Callable[[Carrier], Eval]
    coherent: Callable[[], bool] = lambda: True
    residual: Optional[Callable[[], Dict[str, Any]]] = None


@dataclass
class Request:
    request_id: str
    authority: Authority
    max_meta_cost: int
    search_complete: bool
    allow_meta_search: bool = True


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


class Kernel:
    def __init__(self) -> None:
        self.compiled_rule: Optional[MetaExpr] = None
        self.frontier: List[MetaExpr] = []
        self.provenance: Dict[str, List[str]] = {}
        self.warrants: Dict[str, List[str]] = {}

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

    def _record(self, rule: MetaExpr, request_id: str, ev: Eval) -> None:
        d = rule.digest()
        self.provenance.setdefault(d, [])
        self.warrants.setdefault(d, [])
        if request_id not in self.provenance[d]:
            self.provenance[d].append(request_id)
            self.warrants[d].append(digest_json(ev.get("witness")))

    def _proposal(
        self,
        rule: MetaExpr,
        current: int,
        delta: int,
        authority: Authority,
    ) -> Tuple[int, Carrier, Eval]:
        size = eval_meta(rule, current, delta)
        if size <= 0:
            return size, materialize_carrier(1), {
                "accepted": False,
                "protected_ok": True,
                "loss": 1,
                "witness": {"reason": "nonpositive_spec"},
            }
        carrier = materialize_carrier(size)
        ev = self._norm(authority.evaluate(carrier))
        return size, carrier, ev

    def ablate_compiled_rule(self) -> bool:
        had = self.compiled_rule is not None
        self.compiled_rule = None
        return had

    def _rule_data(self, rule: MetaExpr) -> Dict[str, Any]:
        d = rule.digest()
        return {
            "rule_digest": d,
            "rule": rule.to_data(),
            "rule_cost": rule.cost,
            "behavior_key": behavior_key(rule),
            "provenance": list(self.provenance.get(d, [])),
            "warrant_digests": list(self.warrants.get(d, [])),
        }

    def run(self, req: Request) -> Eval:
        if not req.authority.coherent():
            return {
                "request_id": req.request_id,
                "status": "AUTHORITY_CONFLICT",
                "route": "STOP",
            }

        residual = req.authority.residual() if req.authority.residual else {}
        if not bool(residual.get("basis_obstruction_certified")):
            return {
                "request_id": req.request_id,
                "status": "UNKNOWN_AUTHORIZATION",
                "route": "STOP",
                "residual": residual,
            }

        current = residual.get("current")
        delta = residual.get("delta")
        if type(current) is not int or type(delta) is not int:
            return {
                "request_id": req.request_id,
                "status": "UNKNOWN_RESIDUAL",
                "route": "STOP",
                "residual": residual,
            }

        failed_compiled = None

        # Reuse the uniquely compiled rule first.
        if self.compiled_rule is not None:
            rule = self.compiled_rule
            size, carrier, ev = self._proposal(rule, current, delta, req.authority)
            if self._accepted(ev):
                self._record(rule, req.request_id, ev)
                return {
                    "request_id": req.request_id,
                    "status": "VERIFIED",
                    "route": "META_REUSE",
                    "residual": residual,
                    "carrier": carrier.data(),
                    "proposal_size": size,
                    "evaluation": ev,
                    "tested_meta_program_count": 0,
                    "compiled_rule": self._rule_data(rule),
                    "frontier_size": 0,
                }

            failed_compiled = {
                "rule": self._rule_data(rule),
                "proposal_size": size,
                "evaluation": ev,
            }
            # A failed retained rule loses active compiled status.
            self.compiled_rule = None

        # If non-canonical rules were preserved, let this encounter act as
        # independent future consequence before conducting any new search.
        if self.frontier:
            survivors = []
            tested = 0
            for rule in self.frontier:
                tested += 1
                size, carrier, ev = self._proposal(
                    rule, current, delta, req.authority
                )
                if self._accepted(ev):
                    self._record(rule, req.request_id, ev)
                    survivors.append((rule, size, carrier, ev))

            if survivors:
                self.frontier = [x[0] for x in survivors]
                if len(survivors) == 1:
                    rule, size, carrier, ev = survivors[0]
                    self.compiled_rule = rule
                    self.frontier = []
                    return {
                        "request_id": req.request_id,
                        "status": "VERIFIED",
                        "route": "FUTURE_SELECT",
                        "residual": residual,
                        "carrier": carrier.data(),
                        "proposal_size": size,
                        "evaluation": ev,
                        "tested_meta_program_count": tested,
                        "compiled_rule": self._rule_data(rule),
                        "frontier_size": 0,
                        "failed_compiled_rule": failed_compiled,
                    }

                # More than one lawful behavior still survives. The encounter
                # itself is settled, but developmental choice remains open.
                rule, size, carrier, ev = survivors[0]
                return {
                    "request_id": req.request_id,
                    "status": "VERIFIED",
                    "route": "FRONTIER_PRESERVED",
                    "residual": residual,
                    "carrier": carrier.data(),
                    "proposal_size": size,
                    "evaluation": ev,
                    "tested_meta_program_count": tested,
                    "frontier_size": len(survivors),
                    "frontier": [self._rule_data(x[0]) for x in survivors],
                    "failed_compiled_rule": failed_compiled,
                }

            self.frontier = []

        if not req.allow_meta_search:
            return {
                "request_id": req.request_id,
                "status": "UNKNOWN_META_RULE",
                "route": "STOP",
                "residual": residual,
                "tested_meta_program_count": 0,
                "failed_compiled_rule": failed_compiled,
            }

        synth = MetaSynthesizer(req.max_meta_cost)
        accepted = []
        tested = 0
        for rule in synth.programs():
            tested += 1
            size, carrier, ev = self._proposal(
                rule, current, delta, req.authority
            )
            if self._accepted(ev):
                accepted.append((rule, size, carrier, ev))

        if not accepted:
            return {
                "request_id": req.request_id,
                "status": (
                    "CERTIFIED_NO_META_RULE_IN_DECLARED_CLASS"
                    if req.search_complete
                    else "UNKNOWN_META_SEARCH"
                ),
                "route": "STOP",
                "residual": residual,
                "tested_meta_program_count": tested,
                "failed_compiled_rule": failed_compiled,
            }

        min_cost = min(x[0].cost for x in accepted)
        minima = [x for x in accepted if x[0].cost == min_cost]

        # MetaSynthesizer already quotients syntax by complete calibration behavior.
        by_behavior: Dict[str, Tuple[MetaExpr, int, Carrier, Eval]] = {}
        for x in minima:
            by_behavior.setdefault(behavior_key(x[0]), x)
        minima = list(by_behavior.values())

        for rule, _, _, ev in minima:
            self._record(rule, req.request_id, ev)

        if len(minima) == 1:
            rule, size, carrier, ev = minima[0]
            self.compiled_rule = rule
            self.frontier = []
            return {
                "request_id": req.request_id,
                "status": "VERIFIED",
                "route": "META_SEARCH_UNIQUE",
                "residual": residual,
                "carrier": carrier.data(),
                "proposal_size": size,
                "evaluation": ev,
                "tested_meta_program_count": tested,
                "compiled_rule": self._rule_data(rule),
                "frontier_size": 0,
                "failed_compiled_rule": failed_compiled,
            }

        self.compiled_rule = None
        self.frontier = [x[0] for x in minima]
        rule, size, carrier, ev = minima[0]
        return {
            "request_id": req.request_id,
            "status": "VERIFIED",
            "route": "META_SEARCH_NONCANONICAL",
            "residual": residual,
            "carrier": carrier.data(),
            "proposal_size": size,
            "evaluation": ev,
            "tested_meta_program_count": tested,
            "frontier_size": len(minima),
            "frontier": [self._rule_data(x[0]) for x in minima],
            "failed_compiled_rule": failed_compiled,
        }
