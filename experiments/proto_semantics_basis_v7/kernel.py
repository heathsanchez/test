#!/usr/bin/env python3
"""Frozen V7 generic developmental kernel over the proto-semantic basis."""
from __future__ import annotations

from dataclasses import dataclass, field
import itertools
import json
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from basis import (
    BIT,
    BasisConfig,
    Carrier,
    CarrierRecipe,
    FunctionalRelation,
    QuotientResult,
    RATOM,
    RBASE,
    RBIT,
    RPROD,
    RQUOT,
    canonical_quotient,
    compose_relations,
    enumerate_functional_relations,
    product_carrier,
    relation_atom_id,
)


Eval = Dict[str, Any]
RELATION_PROMOTION_HITS = 2
RECIPE_PROMOTION_DISTINCT_BASES = 2


@dataclass
class CarrierCandidate:
    carrier: Carrier
    cost: int
    route: str
    witness: Any = None


@dataclass
class RelationCandidate:
    relation: FunctionalRelation
    cost: int
    route: str
    components: Tuple[str, ...] = ()


@dataclass
class RelationUsage:
    relation: FunctionalRelation
    origins: List[str] = field(default_factory=list)
    warrants: List[Any] = field(default_factory=list)


@dataclass
class RecipeUsage:
    recipe: CarrierRecipe
    base_ids: List[str] = field(default_factory=list)
    origins: List[str] = field(default_factory=list)
    warrants: List[Any] = field(default_factory=list)


@dataclass(frozen=True)
class RecipeAtom:
    atom_id: str
    definition: CarrierRecipe
    provenance: Tuple[str, ...]
    base_ids: Tuple[str, ...]


class ProtoKernel:
    def __init__(self, config: BasisConfig):
        self.config = config
        self.retained_carriers: Dict[str, Carrier] = {}
        self.relation_atoms: Dict[str, FunctionalRelation] = {}
        self.relation_usage: Dict[str, RelationUsage] = {}
        self.recipe_atoms: Dict[str, RecipeAtom] = {}
        self.recipe_usage: Dict[str, RecipeUsage] = {}

    # ------------------------------------------------------------------
    # Carrier construction
    # ------------------------------------------------------------------

    @staticmethod
    def _carrier_semantic_key(c: Carrier) -> Tuple[int]:
        # For V7 carrier search, authority cares about finite distinction count.
        # Provenance is retained separately.
        return (c.size,)

    def _carrier_levels(
        self,
        max_cost: int,
        size_cap: int,
        allow_retained: bool,
    ) -> Dict[int, Dict[Tuple[int], CarrierCandidate]]:
        levels: Dict[int, Dict[Tuple[int], CarrierCandidate]] = {}

        def admit(cost: int, candidate: CarrierCandidate) -> None:
            if candidate.carrier.size <= 0 or candidate.carrier.size > size_cap:
                return
            key = self._carrier_semantic_key(candidate.carrier)
            bucket = levels.setdefault(cost, {})
            old = bucket.get(key)
            if old is None or candidate.carrier.carrier_id < old.carrier.carrier_id:
                # Do not admit a semantic size already available more cheaply.
                for c0 in range(1, cost):
                    if key in levels.get(c0, {}):
                        return
                bucket[key] = candidate

        if max_cost >= 1:
            admit(1, CarrierCandidate(BIT, 1, "BIT"))
            if allow_retained:
                for c in self.retained_carriers.values():
                    admit(1, CarrierCandidate(c, 1, "RETAINED_CARRIER"))

        for cost in range(2, max_cost + 1):
            if self.config.product:
                for ca in range(1, cost - 1):
                    cb = cost - 1 - ca
                    if cb < 1:
                        continue
                    for a in levels.get(ca, {}).values():
                        for b in levels.get(cb, {}).values():
                            c = product_carrier(a.carrier, b.carrier)
                            admit(cost, CarrierCandidate(c, cost, "PRODUCT"))

            if self.config.quotient:
                src_cost = cost - 1
                for src in levels.get(src_cost, {}).values():
                    for k in range(1, src.carrier.size + 1):
                        q = canonical_quotient(src.carrier, k)
                        admit(
                            cost,
                            CarrierCandidate(
                                q.quotient,
                                cost,
                                "QUOTIENT",
                                witness=q.data(),
                            ),
                        )

        return levels

    def construct_carrier(
        self,
        target_size: int,
        max_cost: int,
        search_complete: bool,
        allow_retained: bool = True,
        retain_verified: bool = False,
    ) -> Eval:
        target_size = int(target_size)
        size_cap = max(2, target_size * 2)
        levels = self._carrier_levels(max_cost, size_cap, allow_retained)

        tested = sum(len(x) for x in levels.values())
        matches: List[CarrierCandidate] = []
        for cost in range(1, max_cost + 1):
            for c in levels.get(cost, {}).values():
                if c.carrier.size == target_size:
                    matches.append(c)
            if matches:
                break

        if not matches:
            return {
                "status": (
                    "CERTIFIED_NO_CARRIER_IN_DECLARED_CLASS"
                    if search_complete
                    else "UNKNOWN_SEARCH"
                ),
                "target_size": target_size,
                "tested_carrier_classes": tested,
                "basis": self.config.data(),
            }

        matches.sort(key=lambda c: (c.cost, c.carrier.carrier_id))
        c = matches[0]
        if retain_verified:
            self.retained_carriers.setdefault(c.carrier.carrier_id, c.carrier)

        return {
            "status": "VERIFIED",
            "route": c.route,
            "target_size": target_size,
            "cost": c.cost,
            "carrier": c.carrier,
            "carrier_data": c.carrier.data(),
            "construction_witness": c.witness,
            "tested_carrier_classes": tested,
            "basis": self.config.data(),
        }

    def retain_carrier(self, c: Carrier) -> None:
        self.retained_carriers.setdefault(c.carrier_id, c)

    def ablate_carrier(self, carrier_id: str) -> bool:
        return self.retained_carriers.pop(carrier_id, None) is not None

    # ------------------------------------------------------------------
    # Relations / computations / predicates
    # ------------------------------------------------------------------

    @staticmethod
    def _rel_key(r: FunctionalRelation) -> Tuple[str, str, str]:
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
        allow_direct: bool = True,
    ) -> Tuple[List[RelationCandidate], int]:
        best: Dict[Tuple[str, str, str], RelationCandidate] = {}
        generated = 0

        def admit(c: RelationCandidate) -> None:
            key = self._rel_key(c.relation)
            old = best.get(key)
            if old is None or (c.cost, c.route) < (old.cost, old.route):
                best[key] = c

        # Retained/reified relations are cheap atoms.
        for atom_id, r in self.relation_atoms.items():
            if (
                r.domain.carrier_id == domain.carrier_id
                and r.codomain.carrier_id == codomain.carrier_id
                and 1 <= max_cost
            ):
                generated += 1
                admit(RelationCandidate(r, 1, "ATOM", (atom_id,)))

        # Modular composition of retained atoms.
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
                        generated += 1
                        comp = compose_relations(r1, r2)
                        admit(
                            RelationCandidate(
                                comp,
                                3,
                                "COMPOSE",
                                (id1, id2),
                            )
                        )

        # Direct extensional relation construction.
        direct_cost = 1 + domain.size
        if (
            allow_direct
            and self.config.relation
            and direct_cost <= max_cost
        ):
            for r in enumerate_functional_relations(domain, codomain):
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
        evaluator: Callable[[FunctionalRelation], Mapping[str, Any]],
        max_cost: int,
        search_complete: bool,
        allow_direct: bool = True,
        record_lawful: bool = True,
    ) -> Eval:
        candidates, generated = self._relation_candidates(
            domain, codomain, max_cost, allow_direct
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

        # candidates are already quotient-collapsed by extensional behavior.
        if record_lawful:
            for c, ev in minima:
                self._record_relation_lawful(
                    c.relation, request_id, ev.get("witness")
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
                        "candidate": c,
                        "relation": c.relation.data(),
                        "cost": c.cost,
                        "route": c.route,
                        "components": list(c.components),
                        "evaluation": ev,
                    }
                    for c, ev in minima
                ],
                "_frontier_objects": [(c, ev) for c, ev in minima],
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
        evaluator: Callable[[FunctionalRelation], Mapping[str, Any]],
    ) -> Eval:
        survivors: List[Tuple[RelationCandidate, Eval]] = []
        for c, _old_ev in frontier_objects:
            ev = dict(evaluator(c.relation))
            ev.setdefault("protected_ok", True)
            if bool(ev.get("accepted")) and bool(ev.get("protected_ok")):
                self._record_relation_lawful(
                    c.relation, request_id, ev.get("witness")
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
        r: FunctionalRelation,
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
        r: FunctionalRelation,
    ) -> Optional[str]:
        key = "|".join(self._rel_key(r))
        u = self.relation_usage.get(key)
        if u is None or len(u.origins) < RELATION_PROMOTION_HITS:
            return None
        atom_id = relation_atom_id(r)
        if atom_id not in self.relation_atoms:
            self.relation_atoms[atom_id] = FunctionalRelation(
                r.domain,
                r.codomain,
                r.outputs,
                provenance=(
                    "COMPILED_RELATION",
                    *tuple(u.origins),
                ),
                atom_id=atom_id,
            )
        return atom_id

    def force_promote_relation(
        self,
        r: FunctionalRelation,
        request_id: str,
        warrant: Any = None,
    ) -> str:
        self._record_relation_lawful(r, request_id, warrant)
        key = "|".join(self._rel_key(r))
        u = self.relation_usage[key]
        # Force is used only after an externally verified developmental
        # selection; preserve the fact in provenance by a second warrant label.
        if len(u.origins) < RELATION_PROMOTION_HITS:
            u.origins.append(request_id + ":compile")
            u.warrants.append(warrant)
        return self._promote_relation_if_earned(r) or ""

    def ablate_relation_atom(self, atom_id: str) -> bool:
        return self.relation_atoms.pop(atom_id, None) is not None

    # ------------------------------------------------------------------
    # Parametric carrier formation / grammar compilation
    # ------------------------------------------------------------------

    def _eval_recipe(
        self,
        recipe: CarrierRecipe,
        base: Carrier,
    ) -> Carrier:
        if recipe.op == "base":
            return base
        if recipe.op == "bit":
            return BIT
        if recipe.op == "product":
            if not self.config.product:
                raise ValueError("PRODUCT unavailable")
            a = self._eval_recipe(recipe.args[0], base)
            b = self._eval_recipe(recipe.args[1], base)
            return product_carrier(a, b)
        if recipe.op == "quotient":
            if not self.config.quotient:
                raise ValueError("QUOTIENT unavailable")
            src = self._eval_recipe(recipe.args[0], base)
            return canonical_quotient(
                src, int(recipe.quotient_classes)
            ).quotient
        if recipe.op == "recipe_atom":
            atom = self.recipe_atoms.get(str(recipe.recipe_atom_id))
            if atom is None:
                raise KeyError(recipe.recipe_atom_id)
            return self._eval_recipe(atom.definition, base)
        raise ValueError(recipe.op)

    def _recipe_candidates(
        self,
        base: Carrier,
        max_cost: int,
        target_size: int,
    ) -> List[CarrierRecipe]:
        levels: Dict[int, Dict[str, CarrierRecipe]] = {}

        def admit(cost: int, r: CarrierRecipe) -> None:
            if r.cost != cost:
                return
            try:
                c = self._eval_recipe(r, base)
            except Exception:
                return
            # Bound growth around the requested target.
            if c.size > max(2, target_size * 2):
                return
            key = r.serial()
            levels.setdefault(cost, {}).setdefault(key, r)

        if max_cost >= 1:
            admit(1, RBASE())
            admit(1, RBIT())
            for atom_id in sorted(self.recipe_atoms):
                admit(1, RATOM(atom_id))

        for cost in range(2, max_cost + 1):
            if self.config.quotient:
                for src in levels.get(cost - 1, {}).values():
                    try:
                        sc = self._eval_recipe(src, base)
                    except Exception:
                        continue
                    for k in range(1, sc.size + 1):
                        admit(cost, RQUOT(src, k))

            if self.config.product:
                for ca in range(1, cost - 1):
                    cb = cost - 1 - ca
                    if cb < 1:
                        continue
                    for a in levels.get(ca, {}).values():
                        for b in levels.get(cb, {}).values():
                            admit(cost, RPROD(a, b))

        out = []
        for cost in range(1, max_cost + 1):
            out.extend(levels.get(cost, {}).values())
        out.sort(key=lambda r: (r.cost, r.serial()))
        return out

    def synthesize_formation(
        self,
        request_id: str,
        base: Carrier,
        target_size: int,
        max_cost: int,
        search_complete: bool,
        record_lawful: bool = True,
    ) -> Eval:
        candidates = self._recipe_candidates(
            base, max_cost, int(target_size)
        )
        accepted: List[Tuple[CarrierRecipe, Carrier]] = []
        for r in candidates:
            c = self._eval_recipe(r, base)
            if c.size == int(target_size):
                accepted.append((r, c))

        if not accepted:
            return {
                "request_id": request_id,
                "status": (
                    "CERTIFIED_NO_FORMATION_IN_DECLARED_CLASS"
                    if search_complete
                    else "UNKNOWN_SEARCH"
                ),
                "target_size": int(target_size),
                "basis": self.config.data(),
                "tested_recipe_count": len(candidates),
            }

        min_cost = min(r.cost for r, _ in accepted)
        minima = [(r, c) for r, c in accepted if r.cost == min_cost]

        # Quotient candidates by symbolic recipe, not only resulting size:
        # different formation laws remain distinct until future consequence.
        uniq: Dict[str, Tuple[CarrierRecipe, Carrier]] = {}
        for r, c in minima:
            uniq.setdefault(r.serial(), (r, c))
        minima = list(uniq.values())

        if record_lawful:
            for r, _c in minima:
                self._record_recipe_lawful(
                    r, base, request_id, {"target_size": target_size}
                )

        if len(minima) > 1:
            return {
                "request_id": request_id,
                "status": "VERIFIED",
                "route": "FRONTIER",
                "target_size": int(target_size),
                "minimum_cost": min_cost,
                "frontier_size": len(minima),
                "frontier": [
                    {
                        "recipe": r.to_data(),
                        "formed": c.data(),
                    }
                    for r, c in minima
                ],
                "_frontier_objects": minima,
            }

        r, c = minima[0]
        promoted = None
        if record_lawful:
            promoted = self._promote_recipe_if_earned(r)

        return {
            "request_id": request_id,
            "status": "VERIFIED",
            "route": "RECIPE_ATOM" if r.op == "recipe_atom" else "FORMATION",
            "target_size": int(target_size),
            "minimum_cost": r.cost,
            "recipe": r,
            "recipe_data": r.to_data(),
            "formed": c,
            "formed_data": c.data(),
            "promoted_recipe_atom_id": promoted,
            "tested_recipe_count": len(candidates),
        }

    def _record_recipe_lawful(
        self,
        r: CarrierRecipe,
        base: Carrier,
        request_id: str,
        warrant: Any,
    ) -> None:
        # Only primitive symbolic recipes earn promotion; a compiled atom does
        # not recursively promote itself in V7.
        if r.op == "recipe_atom":
            return
        key = r.serial()
        u = self.recipe_usage.get(key)
        if u is None:
            u = RecipeUsage(r)
            self.recipe_usage[key] = u
        if base.carrier_id not in u.base_ids:
            u.base_ids.append(base.carrier_id)
            u.origins.append(request_id)
            u.warrants.append(warrant)

    def _promote_recipe_if_earned(
        self,
        r: CarrierRecipe,
    ) -> Optional[str]:
        if r.op == "recipe_atom":
            return None
        u = self.recipe_usage.get(r.serial())
        if u is None or len(u.base_ids) < RECIPE_PROMOTION_DISTINCT_BASES:
            return None
        atom_id = "g_" + r.digest()[:16]
        if atom_id not in self.recipe_atoms:
            self.recipe_atoms[atom_id] = RecipeAtom(
                atom_id=atom_id,
                definition=r,
                provenance=tuple(u.origins),
                base_ids=tuple(u.base_ids),
            )
        return atom_id

    def ablate_recipe_atom(self, atom_id: str) -> bool:
        return self.recipe_atoms.pop(atom_id, None) is not None
