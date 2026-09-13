#!/usr/bin/env python3
"""Frozen V27 consequence-gated compositional relation-carrier kernel."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from basis import (
    Cell,
    ConsequenceWorld,
    Expr,
    Mapping,
    all_expression_sets,
    consequence_preserving_factorized_mappings,
    expression_width,
    factorized_mapping_set,
    mapping_is_bijection,
    mapping_preserves_consequence,
    orbit_partition_from_mappings,
    relation_distance,
)


@dataclass(frozen=True)
class Residual:
    left: Cell
    right: Cell
    consequence: int
    left_orbit: int
    right_orbit: int

    def data(self) -> Any:
        return {
            "left": list(self.left),
            "right": list(self.right),
            "consequence": self.consequence,
            "left_orbit": self.left_orbit,
            "right_orbit": self.right_orbit,
        }


class Kernel:
    @staticmethod
    def _authority(world: ConsequenceWorld) -> Optional[Dict[str, Any]]:
        if not world.complete:
            return {
                "status": "UNKNOWN_AUTHORITY",
                "reason": "consequence_table_incomplete",
            }
        return None

    def exhaust_current_language(self, world: ConsequenceWorld) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth

        all_l0 = factorized_mapping_set(world)
        lawful = consequence_preserving_factorized_mappings(world)
        orbits = orbit_partition_from_mappings(world, lawful)

        return {
            "status": "VERIFIED",
            "candidate_count": len(all_l0),
            "lawful_count": len(lawful),
            "orbits": [[list(c) for c in orbit] for orbit in orbits],
            "_all_l0": all_l0,
            "_orbits": orbits,
        }

    def diagnose_residual(
        self,
        world: ConsequenceWorld,
        exhausted: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth

        ex = exhausted or self.exhaust_current_language(world)
        orbits = ex["_orbits"]

        for i in range(len(orbits)):
            for j in range(i + 1, len(orbits)):
                for left in orbits[i]:
                    for right in orbits[j]:
                        value = world.consequence(left)
                        if value is not None and value == world.consequence(right):
                            residual = Residual(
                                left=left,
                                right=right,
                                consequence=int(value),
                                left_orbit=i,
                                right_orbit=j,
                            )
                            return {
                                "status": "CERTIFIED_RESIDUAL",
                                "residual": residual.data(),
                                "_residual": residual,
                            }

        return {"status": "NO_RESIDUAL"}

    @staticmethod
    def _role_pairs(width: int) -> Tuple[Tuple[int, int], ...]:
        return tuple(
            (i, j)
            for i in range(int(width))
            for j in range(int(width))
            if i != j
        )

    @staticmethod
    def _inspect_projected(
        world: ConsequenceWorld,
        expressions,
        role_pair: Tuple[int, int],
    ) -> Dict[str, Any]:
        source_pos, target_pos = role_pair
        cells = world.cells()
        outgoing = {cell: [] for cell in cells}
        incoming = {cell: [] for cell in cells}

        for expr in expressions:
            leaves = expr.leaves()
            source = leaves[source_pos]
            target = leaves[target_pos]
            outgoing[source].append(target)
            incoming[target].append(source)

        total = all(len(outgoing[s]) >= 1 for s in cells)
        functional = all(len(outgoing[s]) <= 1 for s in cells)

        mapping = None
        if total and functional:
            mapping = tuple(outgoing[s][0] for s in cells)

        bijection = (
            mapping is not None
            and all(len(incoming[t]) == 1 for t in cells)
            and mapping_is_bijection(world, mapping)
        )

        return {
            "total": total,
            "functional": functional,
            "bijection": bijection,
            "_mapping": mapping,
        }

    def verify_expression_set(
        self,
        world: ConsequenceWorld,
        residual: Residual,
        expressions,
        all_l0: frozenset[Mapping],
        width: int,
        *,
        verification_enabled: bool = True,
    ) -> Dict[str, Any]:
        if not verification_enabled:
            return {
                "status": "UNKNOWN_NO_VERIFIER",
                "accepted": False,
                "role_rows": [],
            }

        cells = world.cells()
        index = {cell: i for i, cell in enumerate(cells)}
        rows = []

        for role_pair in self._role_pairs(width):
            shape = self._inspect_projected(
                world,
                expressions,
                role_pair,
            )
            mapping = shape["_mapping"]

            discharge = (
                mapping is not None
                and mapping[index[residual.left]] == residual.right
            )
            consequence_ok = (
                shape["bijection"]
                and mapping_preserves_consequence(world, mapping)
            )
            novel = (
                mapping is not None
                and mapping not in all_l0
            )

            accepted = (
                shape["total"]
                and shape["functional"]
                and shape["bijection"]
                and discharge
                and consequence_ok
                and novel
            )

            rows.append({
                "role_pair": list(role_pair),
                "accepted": accepted,
                "total": shape["total"],
                "functional": shape["functional"],
                "bijection": shape["bijection"],
                "residual_discharge": discharge,
                "consequence_preserving": consequence_ok,
                "novel_outside_current_language": novel,
                "distance": (
                    relation_distance(world, mapping)
                    if mapping is not None else None
                ),
                "mapping": (
                    [list(c) for c in mapping]
                    if mapping is not None else None
                ),
                "_mapping": mapping,
            })

        accepted_rows = [row for row in rows if row["accepted"]]
        if not accepted_rows:
            return {
                "status": "REJECTED",
                "accepted": False,
                "role_rows": [
                    {k: v for k, v in row.items() if not k.startswith("_")}
                    for row in rows
                ],
            }

        accepted_rows.sort(
            key=lambda row: (
                row["distance"],
                row["role_pair"],
                row["mapping"],
            )
        )
        best = accepted_rows[0]

        return {
            "status": "VERIFIED",
            "accepted": True,
            "selected_role_pair": best["role_pair"],
            "distance": best["distance"],
            "mapping": best["mapping"],
            "role_rows": [
                {k: v for k, v in row.items() if not k.startswith("_")}
                for row in rows
            ],
            "_mapping": best["_mapping"],
        }

    def search_width(
        self,
        world: ConsequenceWorld,
        residual: Residual,
        width: int,
        *,
        cat_enabled: bool = True,
        verification_enabled: bool = True,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {
                "status": "UNKNOWN_NO_VERIFIER",
                "width": width,
                "tested_candidate_count": 0,
            }

        all_l0 = factorized_mapping_set(world)
        tested = 0
        accepted = []
        rejection_counts = {
            "no_role_pair": 0,
            "no_total_role": 0,
            "no_functional_role": 0,
            "no_bijective_role": 0,
        }

        for expressions in all_expression_sets(
            world,
            width,
            cat_enabled=cat_enabled,
        ):
            tested += 1
            verdict = self.verify_expression_set(
                world,
                residual,
                expressions,
                all_l0,
                width,
            )

            role_rows = verdict.get("role_rows", [])
            if not role_rows:
                rejection_counts["no_role_pair"] += 1
            else:
                if not any(row["total"] for row in role_rows):
                    rejection_counts["no_total_role"] += 1
                if not any(row["functional"] for row in role_rows):
                    rejection_counts["no_functional_role"] += 1
                if not any(row["bijection"] for row in role_rows):
                    rejection_counts["no_bijective_role"] += 1

            if verdict.get("accepted"):
                accepted.append((expressions, verdict))

        if not accepted:
            return {
                "status": "CERTIFIED_NO_VERIFIER_CLEAN_STRUCTURE_AT_WIDTH",
                "width": width,
                "tested_candidate_count": tested,
                "rejection_counts": rejection_counts,
                "frontier": [],
                "_frontier_objects": tuple(),
            }

        best_distance = min(v["distance"] for _, v in accepted)
        frontier = [
            (expressions, verdict)
            for expressions, verdict in accepted
            if verdict["distance"] == best_distance
        ]
        frontier.sort(
            key=lambda row: (
                tuple(sorted(expr.leaves() for expr in row[0])),
                row[1]["selected_role_pair"],
            )
        )

        return {
            "status": "VERIFIED",
            "width": width,
            "tested_candidate_count": tested,
            "rejection_counts": rejection_counts,
            "minimum_extensional_distance": best_distance,
            "frontier": [
                {
                    "expressions": [
                        expr.data()
                        for expr in sorted(expressions)
                    ],
                    "flattened_leaves": [
                        [list(cell) for cell in expr.leaves()]
                        for expr in sorted(expressions)
                    ],
                    "selected_role_pair": verdict["selected_role_pair"],
                    "distance": verdict["distance"],
                    "mapping": verdict["mapping"],
                    "role_rows": verdict["role_rows"],
                }
                for expressions, verdict in frontier
            ],
            "_frontier_objects": tuple(frontier),
        }

    def develop(
        self,
        world: ConsequenceWorld,
        *,
        allow_composition_growth: bool = True,
        verification_enabled: bool = True,
        maximum_width: int = 2,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth

        exhausted = self.exhaust_current_language(world)
        diagnosis = self.diagnose_residual(world, exhausted)

        if diagnosis.get("status") == "NO_RESIDUAL":
            return {
                "status": "VERIFIED_NO_GROWTH",
                "composition_growth_authorized": False,
                "current_language": {
                    k: v for k, v in exhausted.items()
                    if not k.startswith("_")
                },
                "diagnosis": diagnosis,
                "generations": [],
            }

        if diagnosis.get("status") != "CERTIFIED_RESIDUAL":
            return diagnosis

        if not verification_enabled:
            return {
                "status": "UNKNOWN_NO_VERIFIER",
                "composition_growth_authorized": False,
                "diagnosis": {
                    k: v for k, v in diagnosis.items()
                    if not k.startswith("_")
                },
                "generations": [],
            }

        residual = diagnosis["_residual"]
        generations = []

        first = self.search_width(
            world,
            residual,
            1,
            cat_enabled=True,
        )
        generations.append({
            k: v for k, v in first.items()
            if not k.startswith("_")
        })

        if first.get("status") == "VERIFIED":
            expressions, verdict = first["_frontier_objects"][0]
            return {
                "status": "VERIFIED",
                "selected_width": 1,
                "composition_growth_authorized": False,
                "generations": generations,
                "_selected": (expressions, verdict),
            }

        if not allow_composition_growth:
            return {
                "status": "CERTIFIED_COMPOSITIONAL_INADEQUACY",
                "selected_width": 1,
                "composition_growth_authorized": True,
                "generations": generations,
            }

        for width in range(2, int(maximum_width) + 1):
            result = self.search_width(
                world,
                residual,
                width,
                cat_enabled=True,
            )
            generations.append({
                k: v for k, v in result.items()
                if not k.startswith("_")
            })

            if result.get("status") == "VERIFIED":
                expressions, verdict = result["_frontier_objects"][0]
                return {
                    "status": "VERIFIED",
                    "selected_width": width,
                    "composition_growth_authorized": True,
                    "generations": generations,
                    "minimum_extensional_distance": result[
                        "minimum_extensional_distance"
                    ],
                    "selected_role_pair": verdict["selected_role_pair"],
                    "mapping": verdict["mapping"],
                    "selected_expressions": [
                        expr.data()
                        for expr in sorted(expressions)
                    ],
                    "selected_flattened_leaves": [
                        [list(cell) for cell in expr.leaves()]
                        for expr in sorted(expressions)
                    ],
                    "_selected": (expressions, verdict),
                }

        return {
            "status": "CERTIFIED_COMPOSITIONAL_INADEQUACY",
            "selected_width": maximum_width,
            "composition_growth_authorized": True,
            "generations": generations,
        }
