#!/usr/bin/env python3
"""Frozen V8 developmental kernel over RELATION + COMPOSE.

PRODUCT-like and QUOTIENT-like carriers are not object-language primitives.
They can arise only by verified relational reification:

- EDGE-REIFY: a verified relation becomes a carrier of its incidences.
- CLASS-REIFY: a verified equivalence relation becomes a carrier of classes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from basis import (
    BIT,
    BasisConfig,
    Carrier,
    Relation,
    compose_relations,
    enumerate_functions,
    enumerate_relations,
    equivalence_classes,
    is_equivalence_relation,
    relation_atom_id,
    total_relation,
)


Eval = Dict[str, Any]
RELATION_PROMOTION_HITS = 2
FORMATION_PROMOTION_DISTINCT_BASES = 2


@dataclass
class RelationCandidate:
    relation: Relation
    cost: int
    route: str
    components: Tuple[str, ...] = ()


@dataclass
class RelationUsage:
    relation: Relation
    origins: List[str] = field(default_factory=list)
    warrants: List[Any] = field(default_factory=list)


@dataclass(frozen=True)
class FormationAtom:
    atom_id: str
    pattern: str
    provenance: Tuple[str, ...]
    base_ids: Tuple[str, ...]

    def data(self) -> Any:
        return {
            "atom_id": self.atom_id,
            "pattern": self.pattern,
            "provenance": list(self.provenance),
            "base_ids": list(self.base_ids),
        }


@dataclass
class FormationUsage:
    pattern: str
    base_ids: List[str] = field(default_factory=list)
    origins: List[str] = field(default_factory=list)


class ProtoKernel:
    def __init__(self, config: BasisConfig):
        self.config = config
        self.retained_carriers: Dict[str, Carrier] = {}
        self.relation_atoms: Dict[str, Relation] = {}
        self.relation_usage: Dict[str, RelationUsage] = {}
        self.formation_atoms: Dict[str, FormationAtom] = {}
        self.formation_usage: Dict[str, FormationUsage] = {}

    # ------------------------------------------------------------------
    # Developmental reification
    # ------------------------------------------------------------------

    @staticmethod
    def reify_edges(
        relation: Relation,
        verified: bool,
        warrant: Any,
    ) -> Carrier:
        if not verified:
            raise ValueError("EDGE-REIFY requires verified relation")
        elems = tuple(
            ("edge", relation.digest(), i, j)
            for i, j in sorted(relation.edges)
        )
        cid = "e_" + relation.digest()[:16]
        return Carrier(
            cid,
            elems,
            provenance=(
                "EDGE_REIFY",
                relation.digest(),
                json.dumps(warrant, sort_keys=True, default=str),
            ),
        )

    @staticmethod
    def reify_classes(
        relation: Relation,
        verified: bool,
        warrant: Any,
    ) -> Carrier:
        if not verified:
            raise ValueError("CLASS-REIFY requires verified relation")
        if not is_equivalence_relation(relation):
            raise ValueError("CLASS-REIFY requires equivalence relation")

        classes = equivalence_classes(relation)
        elems = tuple(
            (
                "class",
                relation.digest(),
                tuple(cls),
            )
            for cls in classes
        )
        cid = "c_" + relation.digest()[:16]
        return Carrier(
            cid,
            elems,
            provenance=(
                "CLASS_REIFY",
                relation.digest(),
                json.dumps(warrant, sort_keys=True, default=str),
            ),
        )

    def retain_carrier(self, c: Carrier) -> None:
        self.retained_carriers.setdefault(c.carrier_id, c)

    def ablate_carrier(self, carrier_id: str) -> bool:
        return self.retained_carriers.pop(carrier_id, None) is not None

    # ------------------------------------------------------------------
    # Relation synthesis and compilation
    # ------------------------------------------------------------------

    @staticmethod
    def _rel_key(r: Relation) -> Tuple[str, str, str]:
        return (
            r.domain.carrier_id,
            r.codomain.carrier_id,
            r.behavior_key(),
        )

    def _relation_candidates(
        self,
        domain: Carrier,
        codomain: Carrier,
        max_cost: int,
        functional_only: bool,
        allow_direct: bool,
    ) -> Tuple[List[RelationCandidate], int]:
        best: Dict[Tuple[str, str, str], RelationCandidate] = {}
        generated = 0

        def admit(c: RelationCandidate) -> None:
            key = self._rel_key(c.relation)
            old = best.get(key)
            if old is None or (c.cost, c.route) < (old.cost, old.route):
                best[key] = c

        # Retained relation atoms.
        for atom_id, r in self.relation_atoms.items():
            if (
                r.domain.carrier_id == domain.carrier_id
                and r.codomain.carrier_id == codomain.carrier_id
                and max_cost >= 1
                and (not functional_only or r.is_function())
            ):
                generated += 1
                admit(RelationCandidate(r, 1, "ATOM", (atom_id,)))

        # Sequential composition of retained atoms.
        if self.config.compose and max_cost >= 3:
            atoms = list(self.relation_atoms.items())
            for id1, r1 in atoms:
                if r1.domain.carrier_id != domain.carrier_id:
                    continue
                for id2, r2 in atoms:
                    if (
                        r1.codomain.carrier_id == r2.domain.carrier_id
                        and r2.codomain.carrier_id == codomain.carrier_id
                    ):
                        comp = compose_relations(r1, r2)
                        if functional_only and not comp.is_function():
                            continue
                        generated += 1
                        admit(
                            RelationCandidate(
                                comp,
                                3,
                                "COMPOSE",
                                (id1, id2),
                            )
                        )

        # Direct extensional relation construction.
        direct_cost = 1 + domain.size * codomain.size
        if (
            allow_direct
            and self.config.relation
            and direct_cost <= max_cost
        ):
            iterator = (
                enumerate_functions(domain, codomain)
                if functional_only
                else enumerate_relations(domain, codomain)
            )
            for r in iterator:
                generated += 1
                admit(RelationCandidate(r, direct_cost, "RELATION"))

        out = list(best.values())
        out.sort(
            key=lambda c: (
                c.cost,
                c.relation.behavior_key(),
                c.route,
            )
        )
        return out, generated

    def synthesize_relation(
        self,
        request_id: str,
        domain: Carrier,
        codomain: Carrier,
        evaluator: Callable[[Relation], Mapping[str, Any]],
        max_cost: int,
        search_complete: bool,
        functional_only: bool = False,
        allow_direct: bool = True,
        record_lawful: bool = True,
    ) -> Eval:
        candidates, generated = self._relation_candidates(
            domain,
            codomain,
            int(max_cost),
            bool(functional_only),
            bool(allow_direct),
        )

        accepted: List[Tuple[RelationCandidate, Eval]] = []
        for c in candidates:
            ev = dict(evaluator(c.relation))
            ev.setdefault("protected_ok", True)
            if bool(ev.get("accepted")) and bool(ev.get("protected_ok")):
                accepted.append((c, ev))

        if not accepted:
            return {
                "request_id": request_id,
                "status": (
                    "CERTIFIED_NO_RELATION_IN_DECLARED_CLASS"
                    if search_complete
                    else "UNKNOWN_SEARCH"
                ),
                "basis": self.config.data(),
                "generated_candidate_count": generated,
                "frontier_size": 0,
            }

        min_cost = min(c.cost for c, _ in accepted)
        minima = [(c, ev) for c, ev in accepted if c.cost == min_cost]

        # Extensional behavior already quotients syntactic duplicates.
        if record_lawful:
            for c, ev in minima:
                self._record_relation_lawful(
                    c.relation,
                    request_id,
                    ev.get("witness"),
                )

        if len(minima) > 1:
            return {
                "request_id": request_id,
                "status": "VERIFIED",
                "route": "FRONTIER",
                "basis": self.config.data(),
                "minimum_cost": min_cost,
                "generated_candidate_count": generated,
                "frontier_size": len(minima),
                "frontier": [
                    {
                        "relation": c.relation.data(),
                        "cost": c.cost,
                        "route": c.route,
                        "components": list(c.components),
                        "evaluation": ev,
                    }
                    for c, ev in minima
                ],
                "_frontier_objects": minima,
            }

        c, ev = minima[0]
        promoted = None
        if record_lawful:
            promoted = self._promote_relation_if_earned(c.relation)

        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": c.route,
            "basis": self.config.data(),
            "minimum_cost": c.cost,
            "generated_candidate_count": generated,
            "frontier_size": 1,
            "relation": c.relation,
            "relation_data": c.relation.data(),
            "components": list(c.components),
            "evaluation": ev,
            "promoted_atom_id": promoted,
        }

    def select_relation_frontier(
        self,
        request_id: str,
        frontier_objects: Sequence[Tuple[RelationCandidate, Eval]],
        evaluator: Callable[[Relation], Mapping[str, Any]],
    ) -> Eval:
        survivors: List[Tuple[RelationCandidate, Eval]] = []

        for c, _ in frontier_objects:
            ev = dict(evaluator(c.relation))
            ev.setdefault("protected_ok", True)
            if bool(ev.get("accepted")) and bool(ev.get("protected_ok")):
                self._record_relation_lawful(
                    c.relation,
                    request_id,
                    ev.get("witness"),
                )
                survivors.append((c, ev))

        if not survivors:
            return {
                "request_id": request_id,
                "status": "CERTIFIED_FRONTIER_ELIMINATED",
                "frontier_size": 0,
            }

        if len(survivors) > 1:
            return {
                "request_id": request_id,
                "status": "VERIFIED",
                "route": "FRONTIER_PRESERVED",
                "frontier_size": len(survivors),
                "_frontier_objects": survivors,
            }

        c, ev = survivors[0]
        promoted = self._promote_relation_if_earned(c.relation)
        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": "FUTURE_SELECT",
            "frontier_size": 1,
            "relation": c.relation,
            "relation_data": c.relation.data(),
            "evaluation": ev,
            "promoted_atom_id": promoted,
        }

    def _record_relation_lawful(
        self,
        r: Relation,
        request_id: str,
        warrant: Any,
    ) -> None:
        key = "|".join(self._rel_key(r))
        u = self.relation_usage.get(key)
        if u is None:
            u = RelationUsage(r)
            self.relation_usage[key] = u

        if request_id not in u.origins:
            u.origins.append(request_id)
            u.warrants.append(warrant)

    def _promote_relation_if_earned(
        self,
        r: Relation,
    ) -> Optional[str]:
        key = "|".join(self._rel_key(r))
        u = self.relation_usage.get(key)
        if u is None or len(u.origins) < RELATION_PROMOTION_HITS:
            return None

        atom_id = relation_atom_id(r)
        if atom_id not in self.relation_atoms:
            self.relation_atoms[atom_id] = Relation(
                r.domain,
                r.codomain,
                r.edges,
                provenance=("COMPILED_RELATION", *tuple(u.origins)),
                atom_id=atom_id,
            )
        return atom_id

    def ablate_relation_atom(self, atom_id: str) -> bool:
        return self.relation_atoms.pop(atom_id, None) is not None

    # ------------------------------------------------------------------
    # Generic total-relation EDGE-REIFY formation and compilation
    # ------------------------------------------------------------------

    @staticmethod
    def _formation_atom_id(pattern: str) -> str:
        import hashlib
        return "g_" + hashlib.sha256(pattern.encode()).hexdigest()[:16]

    def construct_total_edge_self(
        self,
        request_id: str,
        base: Carrier,
        max_cost: int,
        search_complete: bool,
        record_lawful: bool = True,
    ) -> Eval:
        pattern = "TOTAL_EDGE_SELF"
        atom_id = self._formation_atom_id(pattern)

        if atom_id in self.formation_atoms and max_cost >= 1:
            rel = total_relation(base, base)
            c = self.reify_edges(
                rel,
                verified=True,
                warrant={"compiled_pattern": pattern},
            )
            return {
                "request_id": request_id,
                "status": "VERIFIED",
                "route": "FORMATION_ATOM",
                "cost": 1,
                "carrier": c,
                "carrier_data": c.data(),
                "formation_atom_id": atom_id,
            }

        primitive_cost = 2 + base.size * base.size
        if not self.config.relation or primitive_cost > max_cost:
            return {
                "request_id": request_id,
                "status": (
                    "CERTIFIED_NO_FORMATION_IN_DECLARED_CLASS"
                    if search_complete
                    else "UNKNOWN_SEARCH"
                ),
                "route": "STOP",
                "required_primitive_cost": primitive_cost,
            }

        rel = total_relation(base, base)
        c = self.reify_edges(
            rel,
            verified=True,
            warrant={"relation_totality": True, "pattern": pattern},
        )

        promoted = None
        if record_lawful:
            u = self.formation_usage.get(pattern)
            if u is None:
                u = FormationUsage(pattern)
                self.formation_usage[pattern] = u
            if base.carrier_id not in u.base_ids:
                u.base_ids.append(base.carrier_id)
                u.origins.append(request_id)

            if len(u.base_ids) >= FORMATION_PROMOTION_DISTINCT_BASES:
                if atom_id not in self.formation_atoms:
                    self.formation_atoms[atom_id] = FormationAtom(
                        atom_id=atom_id,
                        pattern=pattern,
                        provenance=tuple(u.origins),
                        base_ids=tuple(u.base_ids),
                    )
                promoted = atom_id

        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": "RELATION_REIFY",
            "cost": primitive_cost,
            "carrier": c,
            "carrier_data": c.data(),
            "promoted_formation_atom_id": promoted,
        }

    def construct_total_edge_between(
        self,
        request_id: str,
        left: Carrier,
        right: Carrier,
        max_cost: int,
        search_complete: bool,
    ) -> Eval:
        primitive_cost = 2 + left.size * right.size
        if not self.config.relation or primitive_cost > max_cost:
            return {
                "request_id": request_id,
                "status": (
                    "CERTIFIED_NO_FORMATION_IN_DECLARED_CLASS"
                    if search_complete
                    else "UNKNOWN_SEARCH"
                ),
                "route": "STOP",
                "required_primitive_cost": primitive_cost,
            }

        rel = total_relation(left, right)
        c = self.reify_edges(
            rel,
            verified=True,
            warrant={
                "relation_totality": True,
                "left": left.carrier_id,
                "right": right.carrier_id,
            },
        )
        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": "RELATION_REIFY",
            "cost": primitive_cost,
            "carrier": c,
            "carrier_data": c.data(),
        }

    # ------------------------------------------------------------------
    # Cardinality-level complete over-approximation for bounded obstruction
    # ------------------------------------------------------------------

    def reachable_sizes(
        self,
        max_cost: int,
        size_cap: int,
    ) -> Dict[int, int]:
        """Minimum developmental cost for carrier cardinalities.

        Seed/retained carriers cost 0 to access.

        Generic relational reification operations:
          edge-reify total A<->B costs 2 + |A||B|
          class-reify an equivalence on A costs 2 + |A|^2 and can yield
          any k in [1, |A|].

        This is an over-approximation of semantic reach. If a target size is
        absent here, it is certainly unreachable under the declared budget.
        """
        best: Dict[int, int] = {2: 0}
        for c in self.retained_carriers.values():
            best[c.size] = min(best.get(c.size, 10**9), 0)

        if not self.config.relation:
            return best

        changed = True
        while changed:
            changed = False
            items = list(best.items())

            # EDGE-REIFY of total relations.
            for a, ca in items:
                for b, cb in items:
                    k = a * b
                    if k > size_cap:
                        continue
                    cost = ca + cb + 2 + a * b
                    if cost <= max_cost and cost < best.get(k, 10**9):
                        best[k] = cost
                        changed = True

            # CLASS-REIFY of equivalence relations.
            items = list(best.items())
            for n, cn in items:
                op_cost = 2 + n * n
                total = cn + op_cost
                if total > max_cost:
                    continue
                for k in range(1, n + 1):
                    if k > size_cap:
                        continue
                    if total < best.get(k, 10**9):
                        best[k] = total
                        changed = True

        return best
