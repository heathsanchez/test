#!/usr/bin/env python3
"""Post-freeze hidden consequence worlds for V21."""
from __future__ import annotations

from basis import ConsequenceWorld, relabel_world


def make_base() -> ConsequenceWorld:
    n = 5
    table = tuple(
        tuple(
            1 if ((c - x) % n) in (1, n - 1) else 0
            for c in range(n)
        )
        for x in range(n)
    )
    return ConsequenceWorld(table, True, "base_ring_like")


BASE = make_base()

RELABELED = relabel_world(
    BASE,
    state_relabel=(3, 0, 4, 1, 2),
    test_relabel=(1, 4, 2, 0, 3),
    world_id="base_relabelled",
)


def make_broken() -> ConsequenceWorld:
    rows = [list(r) for r in BASE.table]
    rows[0][0] = 1
    return ConsequenceWorld(
        tuple(tuple(r) for r in rows),
        True,
        "base_broken_one_cell",
    )


BROKEN = make_broken()


def make_no_growth() -> ConsequenceWorld:
    n = 4
    table = tuple(
        tuple(1 if x == c else 0 for c in range(n))
        for x in range(n)
    )
    return ConsequenceWorld(table, True, "no_growth_equality_like")


NO_GROWTH = make_no_growth()


def make_heterogeneous_growth() -> ConsequenceWorld:
    n = 4
    table = tuple(
        tuple(
            1 if ((c - x) % n) in (1, n - 1) else 0
            for c in range(n)
        )
        for x in range(n)
    )
    return ConsequenceWorld(
        table,
        True,
        "heterogeneous_cycle_like",
    )


HETEROGENEOUS_GROWTH = make_heterogeneous_growth()

_missing = [list(r) for r in BASE.table]
_missing[2][3] = None
INCOMPLETE = ConsequenceWorld(
    tuple(tuple(r) for r in _missing),
    False,
    "incomplete_authority",
)
