#!/usr/bin/env python3
"""Post-freeze hidden residual worlds for V22."""
from __future__ import annotations

from basis import ConsequenceWorld, EditProgram, SetEdit, relabel_world


def make_base(world_id: str) -> ConsequenceWorld:
    n = 5
    table = tuple(
        tuple(
            1 if ((c - x) % n) in (1, n - 1) else 0
            for c in range(n)
        )
        for x in range(n)
    )
    return ConsequenceWorld(table, True, world_id)


WORLD_A = make_base("train_a")

WORLD_B = relabel_world(
    WORLD_A,
    state_relabel=(3, 0, 4, 1, 2),
    test_relabel=(1, 4, 2, 0, 3),
    world_id="train_b",
)

WORLD_C = relabel_world(
    WORLD_A,
    state_relabel=(2, 4, 1, 3, 0),
    test_relabel=(4, 0, 3, 1, 2),
    world_id="heldout_c",
)


def make_no_growth() -> ConsequenceWorld:
    n = 4
    table = tuple(
        tuple(1 if x == c else 0 for c in range(n))
        for x in range(n)
    )
    return ConsequenceWorld(table, True, "no_growth")


NO_GROWTH = make_no_growth()

_missing = [list(r) for r in WORLD_A.table]
_missing[2][3] = None
INCOMPLETE = ConsequenceWorld(
    tuple(tuple(r) for r in _missing),
    False,
    "incomplete",
)


def three_edit_control_program() -> EditProgram:
    # A generic challenge-side shape mismatch control. These three cells all
    # have consequence 0 in WORLD_A.
    return EditProgram((
        SetEdit((0,0),(0,2)),
        SetEdit((0,2),(1,1)),
        SetEdit((1,1),(0,0)),
    ))
