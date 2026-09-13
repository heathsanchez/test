from __future__ import annotations
from itertools import combinations, product, permutations
from typing import Any

from basis import World

MAX_SITES = 6

class Kernel:
    @staticmethod
    def authority(world: World) -> dict[str, Any] | None:
        if not world.complete or not world.rows:
            return {"status": "UNKNOWN_AUTHORITY"}
        if any(r.consequence is None for r in world.rows):
            return {"status": "UNKNOWN_AUTHORITY"}
        n = len(world.rows[0].configuration)
        if n < 1 or n > MAX_SITES:
            return {"status": "OUTSIDE_FROZEN_SITE_BOUND"}
        configs = [tuple(int(b) for b in r.configuration) for r in world.rows]
        if any(len(x) != n for x in configs):
            return {"status": "UNKNOWN_AUTHORITY"}
        if any(any(b not in (0, 1) for b in x) for x in configs):
            return {"status": "INVALID_RAW_ALPHABET"}
        if len(set(configs)) != len(configs):
            return {"status": "INVALID_DUPLICATE_CONFIGURATION"}
        required = set(product((0, 1), repeat=n))
        if set(configs) != required:
            return {"status": "UNKNOWN_AUTHORITY"}
        return None

    @staticmethod
    def _permute_configuration(x: tuple[int, ...], p: tuple[int, ...]) -> tuple[int, ...]:
        y = [0] * len(x)
        for i, value in enumerate(x):
            y[p[i]] = int(value)
        return tuple(y)

    @staticmethod
    def _pairs(n: int) -> tuple[tuple[int, int], ...]:
        return tuple(combinations(range(n), 2))

    @classmethod
    def consequence_symmetry(cls, world: World) -> tuple[tuple[int, ...], ...]:
        n = len(world.rows[0].configuration)
        values = {
            tuple(int(b) for b in r.configuration): int(r.consequence)
            for r in world.rows
        }
        surviving = []
        for p in permutations(range(n)):
            pp = tuple(int(i) for i in p)
            if all(
                values[x] == values[cls._permute_configuration(x, pp)]
                for x in values
            ):
                surviving.append(pp)
        return tuple(surviving)

    @staticmethod
    def _map_edge(edge: tuple[int, int], p: tuple[int, ...]) -> tuple[int, int]:
        a, b = p[edge[0]], p[edge[1]]
        return (a, b) if a < b else (b, a)

    @classmethod
    def _pair_orbits(
        cls,
        n: int,
        group: tuple[tuple[int, ...], ...],
    ) -> tuple[tuple[tuple[int, int], ...], ...]:
        unseen = set(cls._pairs(n))
        out = []
        while unseen:
            seed = min(unseen)
            orbit = {cls._map_edge(seed, p) for p in group}
            out.append(tuple(sorted(orbit)))
            unseen -= orbit
        return tuple(out)

    @classmethod
    def relation_automorphisms(
        cls,
        n: int,
        edges: tuple[tuple[int, int], ...],
    ) -> tuple[tuple[int, ...], ...]:
        relation = set(edges)
        out = []
        for p in permutations(range(n)):
            pp = tuple(int(i) for i in p)
            if {cls._map_edge(edge, pp) for edge in relation} == relation:
                out.append(pp)
        return tuple(out)

    @classmethod
    def minimum_relation_frontier(
        cls,
        n: int,
        group: tuple[tuple[int, ...], ...],
    ) -> dict[str, Any]:
        target = set(group)
        pair_orbits = cls._pair_orbits(n, group)
        best_edge_count: int | None = None
        frontier: list[tuple[tuple[int, int], ...]] = []

        for selector in product((0, 1), repeat=len(pair_orbits)):
            edges: set[tuple[int, int]] = set()
            for active, orbit in zip(selector, pair_orbits):
                if active:
                    edges.update(orbit)
            edge_count = len(edges)
            if best_edge_count is not None and edge_count > best_edge_count:
                continue
            relation = tuple(sorted(edges))
            if set(cls.relation_automorphisms(n, relation)) != target:
                continue
            if best_edge_count is None or edge_count < best_edge_count:
                best_edge_count = edge_count
                frontier = [relation]
            elif edge_count == best_edge_count:
                frontier.append(relation)

        if best_edge_count is None:
            return {
                "status": "CERTIFIED_BINARY_RELATION_CLASS_INADEQUATE",
                "pair_orbit_count": len(pair_orbits),
                "frontier": [],
            }

        unique_frontier = tuple(sorted(set(frontier)))
        return {
            "status": "VERIFIED",
            "pair_orbit_count": len(pair_orbits),
            "minimum_edge_count": int(best_edge_count),
            "frontier": [
                [[int(i), int(j)] for i, j in relation]
                for relation in unique_frontier
            ],
            "frontier_count": len(unique_frontier),
        }

    @classmethod
    def minimum_raw_support(cls, world: World) -> dict[str, Any]:
        n = len(world.rows[0].configuration)
        rows = [
            (tuple(int(b) for b in r.configuration), int(r.consequence))
            for r in world.rows
        ]
        for k in range(n + 1):
            supports = []
            for support in combinations(range(n), k):
                seen: dict[tuple[int, ...], int] = {}
                ok = True
                for x, y in rows:
                    key = tuple(x[i] for i in support)
                    if key in seen and seen[key] != y:
                        ok = False
                        break
                    seen[key] = y
                if ok:
                    supports.append(tuple(int(i) for i in support))
            if supports:
                return {
                    "minimum_support_size": int(k),
                    "supports": [list(s) for s in supports],
                    "support_count": len(supports),
                }
        raise AssertionError("complete finite table must admit full support")

    def synthesize(
        self,
        world: World,
        *,
        verification_enabled: bool = True,
        relation_enabled: bool = True,
    ) -> dict[str, Any]:
        auth = self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {
                "status": "UNKNOWN_NO_VERIFIER",
                "symmetry_size": 0,
                "relation_frontier": [],
            }

        n = len(world.rows[0].configuration)
        group = self.consequence_symmetry(world)
        out: dict[str, Any] = {
            "status": "VERIFIED",
            "site_count": n,
            "symmetry_size": len(group),
            "symmetry": [list(p) for p in group],
            "raw_support": self.minimum_raw_support(world),
        }

        if relation_enabled:
            relation = self.minimum_relation_frontier(n, group)
            out["relation"] = relation
            if relation["status"] != "VERIFIED":
                out["status"] = relation["status"]
        else:
            out["relation"] = {
                "status": "DISABLED",
                "frontier": [],
                "frontier_count": 0,
            }
        return out
