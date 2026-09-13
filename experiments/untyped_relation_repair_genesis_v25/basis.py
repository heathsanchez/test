#!/usr/bin/env python3
"""Frozen V25 unrestricted finite-relation substrate."""
from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Any, Dict, Iterator, Sequence, Tuple


Cell = Tuple[int, int]
Edge = Tuple[Cell, Cell]
Relation = frozenset[Edge]
Mapping = Tuple[Cell, ...]
Permutation = Tuple[int, ...]


@dataclass(frozen=True)
class ConsequenceWorld:
    table: Tuple[Tuple[int | None, ...], ...]
    complete: bool = True
    world_id: str = ""

    def __post_init__(self) -> None:
        if not self.table or not self.table[0]:
            raise ValueError("nonempty table required")
        width = len(self.table[0])
        if any(len(row) != width for row in self.table):
            raise ValueError("rectangular table required")
        if self.complete and any(v is None for row in self.table for v in row):
            raise ValueError("complete world cannot contain missing consequence")

    @property
    def state_count(self) -> int:
        return len(self.table)

    @property
    def test_count(self) -> int:
        return len(self.table[0])

    def cells(self) -> Tuple[Cell, ...]:
        return tuple(
            (x, c)
            for x in range(self.state_count)
            for c in range(self.test_count)
        )

    def consequence(self, cell: Cell) -> int | None:
        return self.table[cell[0]][cell[1]]

    def interface_key(self) -> Tuple[int, int]:
        return (self.state_count, self.test_count)


def relation_universe(world: ConsequenceWorld) -> Tuple[Edge, ...]:
    cells = world.cells()
    return tuple((a, b) for a in cells for b in cells)


def relation_from_mask(
    world: ConsequenceWorld,
    mask: int,
) -> Relation:
    universe = relation_universe(world)
    return frozenset(
        edge
        for i, edge in enumerate(universe)
        if (int(mask) >> i) & 1
    )


def all_relations(world: ConsequenceWorld) -> Iterator[Relation]:
    width = len(relation_universe(world))
    for mask in range(1 << width):
        yield relation_from_mask(world, mask)


def identity_mapping(world: ConsequenceWorld) -> Mapping:
    return world.cells()


def mapping_relation(
    world: ConsequenceWorld,
    mapping: Mapping,
) -> Relation:
    return frozenset(zip(world.cells(), mapping))


def identity_relation(world: ConsequenceWorld) -> Relation:
    return mapping_relation(world, identity_mapping(world))


def extensional_distance(
    world: ConsequenceWorld,
    relation: Relation,
) -> int:
    return len(relation ^ identity_relation(world))


def difference_edges(
    world: ConsequenceWorld,
    relation: Relation,
) -> Tuple[Edge, ...]:
    return tuple(sorted(relation ^ identity_relation(world)))


def compose_mappings(
    world: ConsequenceWorld,
    first: Mapping,
    second: Mapping,
) -> Mapping:
    cells = world.cells()
    index = {cell: i for i, cell in enumerate(cells)}
    return tuple(second[index[first[i]]] for i in range(len(cells)))


def mapping_is_bijection(
    world: ConsequenceWorld,
    mapping: Mapping,
) -> bool:
    return len(mapping) == len(world.cells()) and set(mapping) == set(world.cells())


def mapping_preserves_consequence(
    world: ConsequenceWorld,
    mapping: Mapping,
) -> bool:
    return all(
        world.consequence(source) == world.consequence(target)
        for source, target in zip(world.cells(), mapping)
    )


def all_permutations(n: int) -> Iterator[Permutation]:
    yield from itertools.permutations(range(int(n)))


def factorized_mapping_set(world: ConsequenceWorld) -> frozenset[Mapping]:
    cells = world.cells()
    out = set()
    for ps in all_permutations(world.state_count):
        for pt in all_permutations(world.test_count):
            out.add(tuple((ps[x], pt[c]) for x, c in cells))
    return frozenset(out)


def consequence_preserving_factorized_mappings(
    world: ConsequenceWorld,
) -> Tuple[Mapping, ...]:
    return tuple(
        mapping
        for mapping in factorized_mapping_set(world)
        if mapping_preserves_consequence(world, mapping)
    )


def orbit_partition_from_mappings(
    world: ConsequenceWorld,
    mappings: Sequence[Mapping],
) -> Tuple[Tuple[Cell, ...], ...]:
    cells = world.cells()
    parent = {cell: cell for cell in cells}

    def find(a: Cell) -> Cell:
        if parent[a] != a:
            parent[a] = find(parent[a])
        return parent[a]

    def union(a: Cell, b: Cell) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for mapping in mappings:
        for source, target in zip(cells, mapping):
            union(source, target)

    groups: Dict[Cell, list[Cell]] = {}
    for cell in cells:
        groups.setdefault(find(cell), []).append(cell)

    out = [tuple(sorted(v)) for v in groups.values()]
    out.sort(key=lambda z: (len(z), z))
    return tuple(out)


def relabel_world(
    world: ConsequenceWorld,
    state_relabel: Permutation,
    test_relabel: Permutation,
    world_id: str,
) -> ConsequenceWorld:
    rows = [[None] * world.test_count for _ in range(world.state_count)]
    for x in range(world.state_count):
        for c in range(world.test_count):
            rows[state_relabel[x]][test_relabel[c]] = world.consequence((x, c))
    return ConsequenceWorld(
        tuple(tuple(int(v) for v in row) for row in rows),
        True,
        world_id,
    )


def cell_atom(world: ConsequenceWorld, cell: Cell) -> str:
    return f"{world.world_id}::{cell[0]}:{cell[1]}"


def difference_term(
    world: ConsequenceWorld,
    relation: Relation,
) -> tuple:
    return (
        "DIFF",
        *tuple(
            (
                "EDGE",
                cell_atom(world, source),
                cell_atom(world, target),
            )
            for source, target in difference_edges(world, relation)
        ),
    )
