#!/usr/bin/env python3
"""Frozen V20 anonymous finite transformation/consequence substrate."""
from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Any, Iterable, Iterator, Sequence, Tuple


Permutation = Tuple[int, ...]


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

    def consequence(self, state: int, test: int) -> int | None:
        return self.table[int(state)][int(test)]

    def interface_key(self) -> Tuple[int, int]:
        return (self.state_count, self.test_count)

    def data(self) -> Any:
        return {
            "world_id": self.world_id,
            "state_count": self.state_count,
            "test_count": self.test_count,
            "complete": self.complete,
        }


@dataclass(frozen=True, order=True)
class Transform:
    states: Permutation
    tests: Permutation

    def data(self) -> Any:
        return {
            "states": list(self.states),
            "tests": list(self.tests),
            "cost": transform_cost(self),
        }


def identity_permutation(n: int) -> Permutation:
    return tuple(range(int(n)))


def identity_transform(n: int, m: int) -> Transform:
    return Transform(identity_permutation(n), identity_permutation(m))


def all_permutations(n: int) -> Iterator[Permutation]:
    yield from itertools.permutations(range(int(n)))


def all_transforms(n: int, m: int) -> Iterator[Transform]:
    for ps in all_permutations(n):
        for pt in all_permutations(m):
            yield Transform(tuple(ps), tuple(pt))


def compose_perm(first: Permutation, second: Permutation) -> Permutation:
    """Apply first, then second."""
    if len(first) != len(second):
        raise ValueError("permutation size mismatch")
    return tuple(second[first[i]] for i in range(len(first)))


def inverse_perm(p: Permutation) -> Permutation:
    out = [0] * len(p)
    for i, j in enumerate(p):
        out[j] = i
    return tuple(out)


def compose_transform(first: Transform, second: Transform) -> Transform:
    return Transform(
        compose_perm(first.states, second.states),
        compose_perm(first.tests, second.tests),
    )


def inverse_transform(t: Transform) -> Transform:
    return Transform(inverse_perm(t.states), inverse_perm(t.tests))


def cycle_count(p: Permutation) -> int:
    seen = set()
    cycles = 0
    for i in range(len(p)):
        if i in seen:
            continue
        cycles += 1
        j = i
        while j not in seen:
            seen.add(j)
            j = p[j]
    return cycles


def permutation_transposition_cost(p: Permutation) -> int:
    return len(p) - cycle_count(p)


def transform_cost(t: Transform) -> int:
    return (
        permutation_transposition_cost(t.states)
        + permutation_transposition_cost(t.tests)
    )


def is_identity(t: Transform) -> bool:
    return (
        t.states == identity_permutation(len(t.states))
        and t.tests == identity_permutation(len(t.tests))
    )


def is_consequence_symmetry(world: ConsequenceWorld, t: Transform) -> bool:
    if not world.complete:
        raise ValueError("symmetry requires complete authority")
    for x in range(world.state_count):
        for c in range(world.test_count):
            if world.consequence(x, c) != world.consequence(t.states[x], t.tests[c]):
                return False
    return True


def relabel_world(
    world: ConsequenceWorld,
    state_relabel: Permutation,
    test_relabel: Permutation,
    world_id: str,
) -> ConsequenceWorld:
    """Rename old labels to new labels."""
    if not world.complete:
        raise ValueError("relabel requires complete world")
    if sorted(state_relabel) != list(range(world.state_count)):
        raise ValueError("invalid state relabel")
    if sorted(test_relabel) != list(range(world.test_count)):
        raise ValueError("invalid test relabel")

    rows = [[None] * world.test_count for _ in range(world.state_count)]
    for old_x in range(world.state_count):
        for old_c in range(world.test_count):
            rows[state_relabel[old_x]][test_relabel[old_c]] = world.consequence(old_x, old_c)

    return ConsequenceWorld(
        tuple(tuple(int(v) for v in row) for row in rows),
        complete=True,
        world_id=world_id,
    )
