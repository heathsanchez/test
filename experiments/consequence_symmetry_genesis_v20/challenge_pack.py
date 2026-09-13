#!/usr/bin/env python3
"""Post-freeze hidden consequence worlds for V20.

The challenge generator uses familiar finite structures only to create tables.
Those names/structures are not passed to the frozen learner.
"""
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
    return ConsequenceWorld(
        table,
        complete=True,
        world_id="hidden_base",
    )


BASE = make_base()

RELABELED = relabel_world(
    BASE,
    state_relabel=(3, 0, 4, 1, 2),
    test_relabel=(1, 4, 2, 0, 3),
    world_id="hidden_base_relabelled",
)


def make_broken() -> ConsequenceWorld:
    rows = [list(r) for r in BASE.table]
    rows[0][0] = 1 - rows[0][0]
    return ConsequenceWorld(
        tuple(tuple(r) for r in rows),
        complete=True,
        world_id="hidden_broken",
    )


BROKEN = make_broken()


def make_heterogeneous() -> ConsequenceWorld:
    n = 4
    table = tuple(
        tuple(1 if x == c else 0 for c in range(n))
        for x in range(n)
    )
    return ConsequenceWorld(
        table,
        complete=True,
        world_id="hidden_heterogeneous",
    )


HETEROGENEOUS = make_heterogeneous()

_missing = [list(r) for r in BASE.table]
_missing[2][3] = None
INCOMPLETE = ConsequenceWorld(
    tuple(tuple(r) for r in _missing),
    complete=False,
    world_id="hidden_incomplete",
)
