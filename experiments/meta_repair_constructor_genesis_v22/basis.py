#!/usr/bin/env python3
"""Frozen V22 generic pointwise edit substrate.

The only meta-edit is SET(source,target). Higher repair structure is synthesized
and may later be abstracted by generic first-order anti-unification.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Any, Dict, Iterable, Iterator, Sequence, Tuple


Cell = Tuple[int, int]
Mapping = Tuple[Cell, ...]
Permutation = Tuple[int, ...]


@dataclass(frozen=True)
class ConsequenceWorld:
    table: Tuple[Tuple[int | None, ...], ...]
    complete: bool = True
    world_id: str = ""

    def __post_init__(self) -> None:
        if not self.table or not self.table[0]:
            raise ValueError("nonempty consequence table required")
        width = len(self.table[0])
        if any(len(row) != width for row in self.table):
            raise ValueError("rectangular consequence table required")
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
        x, c = cell
        return self.table[int(x)][int(c)]

    def interface_key(self) -> Tuple[int, int]:
        return (self.state_count, self.test_count)


@dataclass(frozen=True, order=True)
class SetEdit:
    source: Cell
    target: Cell

    def data(self) -> Any:
        return {
            "source": list(self.source),
            "target": list(self.target),
        }


@dataclass(frozen=True)
class EditProgram:
    edits: Tuple[SetEdit, ...]

    def __post_init__(self) -> None:
        sources = [e.source for e in self.edits]
        if len(set(sources)) != len(sources):
            raise ValueError("canonical edit program requires distinct sources")

    @property
    def depth(self) -> int:
        return len(self.edits)

    def data(self) -> Any:
        return {
            "depth": self.depth,
            "edits": [e.data() for e in self.edits],
        }


def identity_mapping(world: ConsequenceWorld) -> Mapping:
    return world.cells()


def apply_program(
    world: ConsequenceWorld,
    program: EditProgram,
) -> Mapping:
    cells = world.cells()
    index = {cell: i for i, cell in enumerate(cells)}
    images = list(cells)
    for edit in program.edits:
        images[index[edit.source]] = edit.target
    return tuple(images)


def mapping_is_bijection(world: ConsequenceWorld, mapping: Mapping) -> bool:
    return len(mapping) == len(world.cells()) and set(mapping) == set(world.cells())


def mapping_preserves_consequence(
    world: ConsequenceWorld,
    mapping: Mapping,
) -> bool:
    if not world.complete:
        raise ValueError("complete authority required")
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
            out.add(
                tuple(
                    (ps[x], pt[c])
                    for x, c in cells
                )
            )
    return frozenset(out)


def consequence_preserving_factorized_mappings(
    world: ConsequenceWorld,
) -> Tuple[Mapping, ...]:
    if not world.complete:
        raise ValueError("complete authority required")
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
    parent = {c: c for c in cells}

    def find(a: Cell) -> Cell:
        p = parent[a]
        if p != a:
            parent[a] = find(p)
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
    return f"{world.world_id}::{int(cell[0])}:{int(cell[1])}"


def program_term(world: ConsequenceWorld, program: EditProgram) -> tuple:
    return (
        "SEQ",
        *tuple(
            (
                "SET",
                cell_atom(world, edit.source),
                cell_atom(world, edit.target),
            )
            for edit in program.edits
        ),
    )
