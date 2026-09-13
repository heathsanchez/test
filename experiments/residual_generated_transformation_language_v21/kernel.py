#!/usr/bin/env python3
"""Frozen V21 kernel for residual-generated transformation-language growth."""
from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from basis import (
    Cell,
    ConsequenceWorld,
    FactorizedTransform,
    JointSwap,
    all_factorized_transforms,
    is_factorized_symmetry,
    is_joint_swap_symmetry,
    joint_swap_is_factorizable,
)


class UnionFind:
    def __init__(self, items: Iterable[Any]):
        self.parent = {x: x for x in items}
        self.rank = {x: 0 for x in items}

    def find(self, x):
        p = self.parent[x]
        if p != x:
            self.parent[x] = self.find(p)
        return self.parent[x]

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1

    def components(self):
        groups: Dict[Any, List[Any]] = {}
        for x in self.parent:
            groups.setdefault(self.find(x), []).append(x)
        out = [tuple(sorted(v)) for v in groups.values()]
        out.sort(key=lambda z: (len(z), z))
        return tuple(out)


@dataclass(frozen=True)
class CompiledLanguage:
    interface_key: Tuple[int, int]
    generated_swaps: Tuple[JointSwap, ...]
    initial_orbits: Tuple[Tuple[Cell, ...], ...]
    final_orbits: Tuple[Tuple[Cell, ...], ...]
    representative_values: Tuple[int, ...]
    provenance: Tuple[str, ...]

    def data(self) -> Any:
        return {
            "interface_key": list(self.interface_key),
            "generated_swaps": [s.data() for s in self.generated_swaps],
            "initial_orbit_sizes": [len(o) for o in self.initial_orbits],
            "final_orbit_sizes": [len(o) for o in self.final_orbits],
            "representative_values": list(self.representative_values),
            "provenance": list(self.provenance),
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

    def exhaust_l0(self, world: ConsequenceWorld) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth

        candidates = 0
        symmetries: List[FactorizedTransform] = []
        uf = UnionFind(world.cells())

        for t in all_factorized_transforms(world.state_count, world.test_count):
            candidates += 1
            if is_factorized_symmetry(world, t):
                symmetries.append(t)
                for cell in world.cells():
                    uf.union(cell, t.apply(cell))

        orbits = uf.components()

        return {
            "status": "VERIFIED",
            "candidate_count": candidates,
            "symmetry_count": len(symmetries),
            "orbits": [[list(c) for c in o] for o in orbits],
            "_orbits": orbits,
            "_symmetries": tuple(symmetries),
        }

    @staticmethod
    def _orbit_value(
        world: ConsequenceWorld,
        orbit: Sequence[Cell],
    ) -> int:
        values = {world.consequence(c) for c in orbit}
        if len(values) != 1:
            raise AssertionError("lawful L0 orbit must be consequence-homogeneous")
        value = next(iter(values))
        if value is None:
            raise AssertionError("complete authority expected")
        return int(value)

    @staticmethod
    def _residuals(
        world: ConsequenceWorld,
        orbits: Sequence[Sequence[Cell]],
    ) -> List[Dict[str, Any]]:
        out = []
        for i in range(len(orbits)):
            vi = Kernel._orbit_value(world, orbits[i])
            for j in range(i + 1, len(orbits)):
                vj = Kernel._orbit_value(world, orbits[j])
                if vi != vj:
                    continue
                left = tuple(orbits[i][0])
                right = tuple(orbits[j][0])
                out.append({
                    "orbit_pair": [i, j],
                    "value": vi,
                    "witness": [list(left), list(right)],
                })
        return out

    @staticmethod
    def _minimum_new_primitive_count(
        world: ConsequenceWorld,
        orbits: Sequence[Sequence[Cell]],
    ) -> int:
        by_value: Dict[int, int] = {}
        for orbit in orbits:
            v = Kernel._orbit_value(world, orbit)
            by_value[v] = by_value.get(v, 0) + 1
        return sum(max(0, count - 1) for count in by_value.values())

    @staticmethod
    def _candidate_swaps(
        world: ConsequenceWorld,
        orbits: Sequence[Sequence[Cell]],
    ) -> Tuple[JointSwap, ...]:
        candidates = set()
        for i in range(len(orbits)):
            vi = Kernel._orbit_value(world, orbits[i])
            for j in range(i + 1, len(orbits)):
                vj = Kernel._orbit_value(world, orbits[j])
                if vi != vj:
                    continue
                for a in orbits[i]:
                    for b in orbits[j]:
                        candidates.add(JointSwap(tuple(a), tuple(b)))
        return tuple(sorted(candidates))

    @staticmethod
    def _component_index(
        orbits: Sequence[Sequence[Cell]],
    ) -> Dict[Cell, int]:
        return {
            tuple(cell): i
            for i, orbit in enumerate(orbits)
            for cell in orbit
        }

    @staticmethod
    def _components_after_swaps(
        orbits: Sequence[Sequence[Cell]],
        swaps: Sequence[JointSwap],
    ) -> Tuple[Tuple[Cell, ...], ...]:
        cells = tuple(cell for orbit in orbits for cell in orbit)
        uf = UnionFind(cells)
        for orbit in orbits:
            first = orbit[0]
            for cell in orbit[1:]:
                uf.union(first, cell)
        for s in swaps:
            uf.union(s.left, s.right)
        return uf.components()

    @staticmethod
    def _is_complete_consequence_quotient(
        world: ConsequenceWorld,
        components: Sequence[Sequence[Cell]],
    ) -> bool:
        # No component may mix consequence values.
        seen_by_value: Dict[int, int] = {}
        for idx, comp in enumerate(components):
            vals = {world.consequence(c) for c in comp}
            if len(vals) != 1:
                return False
            v0 = next(iter(vals))
            if v0 is None:
                return False
            v = int(v0)
            if v in seen_by_value:
                # Same value remains in multiple components.
                return False
            seen_by_value[v] = idx
        return True

    @staticmethod
    def _reconstruct(
        world: ConsequenceWorld,
        components: Sequence[Sequence[Cell]],
    ) -> Dict[str, Any]:
        rows = [
            [None for _ in range(world.test_count)]
            for _ in range(world.state_count)
        ]
        values = []
        for comp in components:
            v = world.consequence(comp[0])
            if v is None:
                return {"status": "UNKNOWN_AUTHORITY"}
            if any(world.consequence(c) != v for c in comp):
                return {"status": "INVALID_COMPONENT"}
            values.append(int(v))
            for x, c in comp:
                rows[x][c] = int(v)
        exact = tuple(tuple(int(v) for v in r) for r in rows) == world.table
        return {
            "status": "VERIFIED" if exact else "RECONSTRUCTION_FAILED",
            "representative_values": values,
            "reconstructed_table": rows,
            "exact": exact,
        }

    def _minimum_frontier(
        self,
        world: ConsequenceWorld,
        orbits: Sequence[Sequence[Cell]],
        *,
        enumerate_full_frontier: bool,
    ) -> Dict[str, Any]:
        lower = self._minimum_new_primitive_count(world, orbits)
        candidates = self._candidate_swaps(world, orbits)

        if lower == 0:
            return {
                "status": "VERIFIED",
                "lower_bound": 0,
                "candidate_swap_count": len(candidates),
                "frontier": [[]],
                "_frontier_objects": (tuple(),),
            }

        if not enumerate_full_frontier:
            # Exact canonical forest construction. The theorem-level lower
            # bound is exact because every swap joins at most two components.
            by_value: Dict[int, List[Tuple[Cell, ...]]] = {}
            for orbit in orbits:
                v = self._orbit_value(world, orbit)
                by_value.setdefault(v, []).append(tuple(orbit))

            chosen: List[JointSwap] = []
            for value in sorted(by_value):
                comps = sorted(by_value[value])
                root = comps[0]
                for other in comps[1:]:
                    chosen.append(JointSwap(root[0], other[0]))

            final = self._components_after_swaps(orbits, chosen)
            if len(chosen) != lower or not self._is_complete_consequence_quotient(
                world, final
            ):
                raise AssertionError("canonical exact forest construction failed")

            return {
                "status": "VERIFIED",
                "lower_bound": lower,
                "candidate_swap_count": len(candidates),
                "frontier": [[s.data() for s in chosen]],
                "_frontier_objects": (tuple(chosen),),
                "frontier_enumeration": "canonical_exact_lower_bound",
            }

        successful = []
        for combo in itertools.combinations(candidates, lower):
            final = self._components_after_swaps(orbits, combo)
            if self._is_complete_consequence_quotient(world, final):
                successful.append(tuple(combo))

        successful.sort()
        if not successful:
            return {
                "status": "CERTIFIED_NO_REPAIR_WITHIN_GENERATED_LANGUAGE",
                "lower_bound": lower,
                "candidate_swap_count": len(candidates),
                "frontier": [],
                "_frontier_objects": tuple(),
            }

        return {
            "status": "VERIFIED",
            "lower_bound": lower,
            "candidate_swap_count": len(candidates),
            "frontier": [
                [s.data() for s in combo]
                for combo in successful
            ],
            "_frontier_objects": tuple(successful),
            "frontier_enumeration": "complete",
        }

    def develop(
        self,
        world: ConsequenceWorld,
        *,
        consequence_enabled: bool = True,
        growth_enabled: bool = True,
        enumerate_full_frontier: bool = True,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth

        if not consequence_enabled:
            return {
                "status": "UNKNOWN_NO_CONSEQUENCE_AUTHORITY",
                "growth_authorized": False,
                "generated_swaps": [],
            }

        l0 = self.exhaust_l0(world)
        orbits = l0["_orbits"]
        residuals = self._residuals(world, orbits)
        lower = self._minimum_new_primitive_count(world, orbits)

        if not residuals:
            reconstruction = self._reconstruct(world, orbits)
            return {
                "status": "VERIFIED",
                "growth_authorized": False,
                "l0": {
                    k: v for k, v in l0.items()
                    if not k.startswith("_")
                },
                "residuals": [],
                "minimum_growth_count": 0,
                "generated_swaps": [],
                "initial_orbits": [[list(c) for c in o] for o in orbits],
                "final_orbits": [[list(c) for c in o] for o in orbits],
                "initial_orbit_count": len(orbits),
                "final_orbit_count": len(orbits),
                "final_reconstruction": reconstruction,
                "_initial_orbits": orbits,
                "_final_orbits": orbits,
                "_active_swaps": tuple(),
                "_frontier_objects": (tuple(),),
            }

        if not growth_enabled:
            return {
                "status": "CERTIFIED_TRANSFORMATION_LANGUAGE_RESIDUAL",
                "growth_authorized": True,
                "l0": {
                    k: v for k, v in l0.items()
                    if not k.startswith("_")
                },
                "residuals": residuals,
                "minimum_growth_count": lower,
                "generated_swaps": [],
                "initial_orbits": [[list(c) for c in o] for o in orbits],
                "final_orbits": [[list(c) for c in o] for o in orbits],
                "initial_orbit_count": len(orbits),
                "final_orbit_count": len(orbits),
            }

        frontier = self._minimum_frontier(
            world,
            orbits,
            enumerate_full_frontier=enumerate_full_frontier,
        )
        if frontier.get("status") != "VERIFIED":
            return {
                "status": frontier.get("status"),
                "growth_authorized": True,
                "l0": {
                    k: v for k, v in l0.items()
                    if not k.startswith("_")
                },
                "residuals": residuals,
                "minimum_growth_count": lower,
                "repair_search": {
                    k: v for k, v in frontier.items()
                    if not k.startswith("_")
                },
            }

        active = tuple(frontier["_frontier_objects"][0])

        # Every admitted primitive must be residual-earned, replay valid,
        # and outside the exhausted L0 language.
        component_of = self._component_index(orbits)
        checks = []
        for swap in active:
            left_orbit = component_of[swap.left]
            right_orbit = component_of[swap.right]
            residual_earned = (
                left_orbit != right_orbit
                and world.consequence(swap.left)
                    == world.consequence(swap.right)
            )
            replay_ok = is_joint_swap_symmetry(world, swap)
            factorized = joint_swap_is_factorizable(world, swap)
            checks.append({
                "swap": swap.data(),
                "residual_earned": residual_earned,
                "replay_ok": replay_ok,
                "representable_in_l0": factorized,
            })
            if not residual_earned or not replay_ok or factorized:
                return {
                    "status": "REPAIR_PRIMITIVE_REJECTED",
                    "checks": checks,
                }

        final = self._components_after_swaps(orbits, active)
        reconstruction = self._reconstruct(world, final)

        return {
            "status": "VERIFIED",
            "growth_authorized": True,
            "l0": {
                k: v for k, v in l0.items()
                if not k.startswith("_")
            },
            "residuals": residuals,
            "minimum_growth_count": lower,
            "repair_search": {
                k: v for k, v in frontier.items()
                if not k.startswith("_")
            },
            "generated_swaps": [s.data() for s in active],
            "generated_swap_checks": checks,
            "initial_orbits": [[list(c) for c in o] for o in orbits],
            "final_orbits": [[list(c) for c in o] for o in final],
            "initial_orbit_count": len(orbits),
            "final_orbit_count": len(final),
            "final_reconstruction": reconstruction,
            "_initial_orbits": orbits,
            "_final_orbits": final,
            "_active_swaps": active,
            "_frontier_objects": frontier["_frontier_objects"],
        }

    def compile(
        self,
        world: ConsequenceWorld,
        development: Dict[str, Any],
        provenance: Sequence[str],
    ) -> CompiledLanguage:
        if development.get("status") != "VERIFIED":
            raise ValueError("verified development required")

        final = development["_final_orbits"]
        reconstruction = development["final_reconstruction"]

        return CompiledLanguage(
            interface_key=world.interface_key(),
            generated_swaps=tuple(development["_active_swaps"]),
            initial_orbits=tuple(development["_initial_orbits"]),
            final_orbits=tuple(final),
            representative_values=tuple(
                int(v)
                for v in reconstruction["representative_values"]
            ),
            provenance=tuple(provenance),
        )

    def replay_compiled(
        self,
        world: ConsequenceWorld,
        compiled: CompiledLanguage,
    ) -> Dict[str, Any]:
        auth = self._authority(world)
        if auth:
            return auth
        if compiled.interface_key != world.interface_key():
            return {"status": "TYPE_MISMATCH"}

        swap_rows = []
        failed = []
        for swap in compiled.generated_swaps:
            ok = is_joint_swap_symmetry(world, swap)
            row = {
                "swap": swap.data(),
                "replay_ok": ok,
            }
            swap_rows.append(row)
            if not ok:
                failed.append(swap)

        rows = [
            [None for _ in range(world.test_count)]
            for _ in range(world.state_count)
        ]
        for orbit, value in zip(
            compiled.final_orbits,
            compiled.representative_values,
        ):
            for x, c in orbit:
                rows[x][c] = int(value)

        quotient_exact = (
            tuple(tuple(int(v) for v in row) for row in rows)
            == world.table
        )

        return {
            "status": (
                "VERIFIED"
                if not failed and quotient_exact
                else "REPLAY_FAILED"
            ),
            "failed_generated_swap_count": len(failed),
            "generated_swap_replay": swap_rows,
            "old_quotient_exact": quotient_exact,
            "reconstructed_table": rows,
        }

    @staticmethod
    def structural_signature(
        world: ConsequenceWorld,
        development: Dict[str, Any],
    ) -> Dict[str, Any]:
        final_orbits = development["_final_orbits"]
        value_size = sorted(
            [
                [len(o), int(world.consequence(o[0]))]
                for o in final_orbits
            ]
        )
        initial_sizes = sorted(
            len(o) for o in development["_initial_orbits"]
        )
        return {
            "interface": list(world.interface_key()),
            "l0_symmetry_count": development["l0"]["symmetry_count"],
            "initial_orbit_sizes": initial_sizes,
            "minimum_growth_count": development["minimum_growth_count"],
            "final_orbit_size_value_multiset": value_size,
        }
