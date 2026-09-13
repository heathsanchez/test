#!/usr/bin/env python3
"""Frozen V21 substrate: factorized finite symmetries plus residual-generated joint cell swaps."""
from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Any, Iterator, Sequence, Tuple


Permutation = Tuple[int, ...]
Cell = Tuple[int, int]


@dataclass(frozen=True)
class ConsequenceWorld:
    table: Tuple[Tuple[int | None, ...], ...]
    complete: bool = True
    world_id: str = ""

    def __post_init__(self) -> None:
        if not self.table or not self.table[0]:
            raise ValueError("nonempty consequence table required")
        m = len(self.table[0])
        if any(len(row) != m for row in self.table):
            raise ValueError("rectangular consequence table required")
        if self.complete and any(v is None for row in self.table for v in row):
            raise ValueError("complete world cannot contain missing consequence")

    @property
    def state_count(self) -> int:
        return len(self.table)

    @property
    def test_count(self) -> int:
        return len(self.table[0])

    @property
    def cell_count(self) -> int:
        return self.state_count * self.test_count

    def consequence(self, cell: Cell) -> int | None:
        x, c = cell
        return self.table[int(x)][int(c)]

    def cells(self) -> Tuple[Cell, ...]:
        return tuple(
            (x, c)
            for x in range(self.state_count)
            for c in range(self.test_count)
        )

    def interface_key(self) -> Tuple[int, int]:
        return (self.state_count, self.test_count)


@dataclass(frozen=True, order=True)
class FactorizedTransform:
    states: Permutation
    tests: Permutation

    def apply(self, cell: Cell) -> Cell:
        x, c = cell
        return (self.states[x], self.tests[c])

    def data(self) -> Any:
        return {
            "states": list(self.states),
            "tests": list(self.tests),
        }


@dataclass(frozen=True, order=True)
class JointSwap:
    left: Cell
    right: Cell

    def __post_init__(self) -> None:
        if self.left == self.right:
            raise ValueError("nontrivial swap requires distinct endpoints")
        if self.right < self.left:
            a, b = self.right, self.left
            object.__setattr__(self, "left", a)
            object.__setattr__(self, "right", b)

    def apply(self, cell: Cell) -> Cell:
        if cell == self.left:
            return self.right
        if cell == self.right:
            return self.left
        return cell

    def data(self) -> Any:
        return {
            "left": list(self.left),
            "right": list(self.right),
        }


def identity_permutation(n: int) -> Permutation:
    return tuple(range(int(n)))


def all_factorized_transforms(n: int, m: int) -> Iterator[FactorizedTransform]:
    for ps in itertools.permutations(range(int(n))):
        for pt in itertools.permutations(range(int(m))):
            yield FactorizedTransform(tuple(ps), tuple(pt))


def is_factorized_symmetry(
    world: ConsequenceWorld,
    t: FactorizedTransform,
) -> bool:
    if not world.complete:
        raise ValueError("complete authority required")
    for cell in world.cells():
        if world.consequence(cell) != world.consequence(t.apply(cell)):
            return False
    return True


def is_joint_swap_symmetry(
    world: ConsequenceWorld,
    swap: JointSwap,
) -> bool:
    if not world.complete:
        raise ValueError("complete authority required")
    return world.consequence(swap.left) == world.consequence(swap.right)


def joint_swap_is_factorizable(
    world: ConsequenceWorld,
    swap: JointSwap,
) -> bool:
    """Independent brute-force test against the complete L0 carrier."""
    for t in all_factorized_transforms(world.state_count, world.test_count):
        if all(t.apply(cell) == swap.apply(cell) for cell in world.cells()):
            return True
    return False


def relabel_world(
    world: ConsequenceWorld,
    state_relabel: Permutation,
    test_relabel: Permutation,
    world_id: str,
) -> ConsequenceWorld:
    if not world.complete:
        raise ValueError("complete world required")
    rows = [[None] * world.test_count for _ in range(world.state_count)]
    for x in range(world.state_count):
        for c in range(world.test_count):
            rows[state_relabel[x]][test_relabel[c]] = world.consequence((x, c))
    return ConsequenceWorld(
        tuple(tuple(int(v) for v in row) for row in rows),
        True,
        world_id,
    )
