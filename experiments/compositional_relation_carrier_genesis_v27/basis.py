#!/usr/bin/env python3
"""Frozen V27 atomic-symbol + generic CAT composition substrate."""
from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Any, Dict, Iterator, Sequence, Tuple


Cell = Tuple[int, int]
Permutation = Tuple[int, ...]
Mapping = Tuple[Cell, ...]


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


@dataclass(frozen=True, order=True)
class Atom:
    value: Cell

    def leaves(self) -> Tuple[Cell, ...]:
        return (self.value,)

    def data(self) -> Any:
        return ["ATOM", list(self.value)]


@dataclass(frozen=True, order=True)
class Cat:
    prefix: Any
    tail: Atom

    def leaves(self) -> Tuple[Cell, ...]:
        return self.prefix.leaves() + self.tail.leaves()

    def data(self) -> Any:
        return ["CAT", self.prefix.data(), self.tail.data()]


Expr = Atom | Cat


def expression_width(expr: Expr) -> int:
    return len(expr.leaves())


def atomic_expressions(world: ConsequenceWorld) -> Tuple[Atom, ...]:
    return tuple(Atom(cell) for cell in world.cells())


def expressions_of_width(
    world: ConsequenceWorld,
    width: int,
    *,
    cat_enabled: bool = True,
) -> Tuple[Expr, ...]:
    if width <= 0:
        raise ValueError("width must be positive")

    atoms = atomic_expressions(world)
    if width == 1:
        return atoms
    if not cat_enabled:
        return tuple()

    level: Tuple[Expr, ...] = atoms
    for _ in range(2, int(width) + 1):
        level = tuple(
            Cat(prefix, atom)
            for prefix in level
            for atom in atoms
        )
    return level


def all_expression_sets(
    world: ConsequenceWorld,
    width: int,
    *,
    cat_enabled: bool = True,
) -> Iterator[frozenset[Expr]]:
    universe = expressions_of_width(
        world,
        width,
        cat_enabled=cat_enabled,
    )
    for mask in range(1 << len(universe)):
        yield frozenset(
            expr
            for i, expr in enumerate(universe)
            if (mask >> i) & 1
        )


def mapping_is_bijection(
    world: ConsequenceWorld,
    mapping: Mapping,
) -> bool:
    return (
        len(mapping) == len(world.cells())
        and set(mapping) == set(world.cells())
    )


def mapping_preserves_consequence(
    world: ConsequenceWorld,
    mapping: Mapping,
) -> bool:
    return all(
        world.consequence(source) == world.consequence(target)
        for source, target in zip(world.cells(), mapping)
    )


def identity_mapping(world: ConsequenceWorld) -> Mapping:
    return world.cells()


def relation_distance(
    world: ConsequenceWorld,
    mapping: Mapping,
) -> int:
    identity = frozenset(zip(world.cells(), identity_mapping(world)))
    candidate = frozenset(zip(world.cells(), mapping))
    return len(identity ^ candidate)


def all_permutations(n: int) -> Iterator[Permutation]:
    yield from itertools.permutations(range(int(n)))


def factorized_mapping_set(
    world: ConsequenceWorld,
) -> frozenset[Mapping]:
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
