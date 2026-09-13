#!/usr/bin/env python3
"""Frozen V23 relational-incidence delta substrate."""
from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Any, Dict, Iterable, Iterator, Sequence, Tuple


Cell = Tuple[int, int]
Edge = Tuple[Cell, Cell]
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
            raise ValueError("complete world cannot contain missing values")

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


@dataclass(frozen=True, order=True)
class IncidenceBit:
    source: Cell
    target: Cell

    def edge(self) -> Edge:
        return (self.source, self.target)

    def data(self) -> Any:
        return {
            "source": list(self.source),
            "target": list(self.target),
        }


@dataclass(frozen=True)
class DeltaProgram:
    bits: Tuple[IncidenceBit, ...]

    def __post_init__(self) -> None:
        if len(set(self.bits)) != len(self.bits):
            raise ValueError("duplicate relation-incidence bit")

    @property
    def depth(self) -> int:
        return len(self.bits)

    def data(self) -> Any:
        return {
            "depth": self.depth,
            "bits": [b.data() for b in self.bits],
        }


def identity_relation(world: ConsequenceWorld) -> frozenset[Edge]:
    return frozenset((cell, cell) for cell in world.cells())


def incidence_universe(world: ConsequenceWorld) -> Tuple[IncidenceBit, ...]:
    return tuple(
        IncidenceBit(source, target)
        for source in world.cells()
        for target in world.cells()
    )


def apply_delta_relation(
    world: ConsequenceWorld,
    program: DeltaProgram,
) -> frozenset[Edge]:
    graph = set(identity_relation(world))
    for bit in program.bits:
        edge = bit.edge()
        if edge in graph:
            graph.remove(edge)
        else:
            graph.add(edge)
    return frozenset(graph)


def relation_to_mapping(
    world: ConsequenceWorld,
    relation: Iterable[Edge],
) -> Mapping | None:
    rows: Dict[Cell, list[Cell]] = {cell: [] for cell in world.cells()}
    for source, target in relation:
        if source not in rows or target not in rows:
            return None
        rows[source].append(target)

    if any(len(rows[source]) != 1 for source in world.cells()):
        return None

    return tuple(rows[source][0] for source in world.cells())


def mapping_is_bijection(world: ConsequenceWorld, mapping: Mapping) -> bool:
    return len(mapping) == len(world.cells()) and set(mapping) == set(world.cells())


def mapping_preserves_consequence(
    world: ConsequenceWorld,
    mapping: Mapping,
) -> bool:
    return all(
        world.consequence(source) == world.consequence(target)
        for source, target in zip(world.cells(), mapping)
    )


def compose_mappings(
    world: ConsequenceWorld,
    first: Mapping,
    second: Mapping,
) -> Mapping:
    cells = world.cells()
    index = {cell: i for i, cell in enumerate(cells)}
    return tuple(second[index[first[i]]] for i in range(len(cells)))


def all_permutations(n: int) -> Iterator[Permutation]:
    yield from itertools.permutations(range(int(n)))


def factorized_mapping_set(world: ConsequenceWorld) -> frozenset[Mapping]:
    cells = world.cells()
    out = set()
    for ps in all_permutations(world.state_count):
        for pt in all_permutations(world.test_count):
            out.add(
                tuple((ps[x], pt[c]) for x, c in cells)
            )
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


def delta_term(world: ConsequenceWorld, program: DeltaProgram) -> tuple:
    return (
        "DELTA",
        *tuple(
            (
                "BIT",
                cell_atom(world, bit.source),
                cell_atom(world, bit.target),
            )
            for bit in program.bits
        ),
    )
