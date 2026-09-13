#!/usr/bin/env python3
"""Post-freeze hidden worlds for V24 edit-free relation construction."""
from __future__ import annotations

from basis import ConsequenceWorld, relabel_world


BASE = ConsequenceWorld(
    (
        (0, 0, 1),
        (0, 1, 0),
    ),
    True,
    "train_a",
)

WORLD_B = relabel_world(
    BASE,
    state_relabel=(1, 0),
    test_relabel=(2, 0, 1),
    world_id="train_b",
)

WORLD_C = relabel_world(
    BASE,
    state_relabel=(0, 1),
    test_relabel=(1, 2, 0),
    world_id="heldout_c",
)

NO_GROWTH = ConsequenceWorld(
    (
        (0, 0, 0),
        (1, 1, 1),
    ),
    True,
    "no_growth",
)

_missing = [list(r) for r in BASE.table]
_missing[1][2] = None
INCOMPLETE = ConsequenceWorld(
    tuple(tuple(r) for r in _missing),
    False,
    "incomplete",
)
