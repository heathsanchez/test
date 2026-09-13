#!/usr/bin/env python3
"""Post-freeze hidden worlds for V12 predictive causal-state genesis.

Challenge-side hidden states are used only to generate encounter/future-
consequence tables. They are never passed to the frozen kernel.
"""
from __future__ import annotations

import itertools
from typing import Dict, Iterable, List, Sequence, Tuple

from basis import ConsequenceTable


TESTS = (
    (2,),
    (1, 2),
    (1, 1, 2),
    (1, 1, 1, 2),
    (2, 1, 2, 1, 2, 1, 2),
    (2, 1, 2, 1, 2, 1, 2, 1, 2),
)


class HiddenTransducer:
    def __init__(self, states, start, step, name):
        self.states = tuple(states)
        self.start = start
        self.step = step
        self.name = name

    def run_actions(self, state, actions):
        obs = []
        s = state
        for a in actions:
            s, o = self.step(s, int(a))
            obs.append(int(o))
        return s, tuple(obs)

    def history_from_actions(self, actions):
        s = self.start
        hist = []
        for a in actions:
            s, o = self.step(s, int(a))
            hist.append((int(a), int(o)))
        return s, tuple(hist)


def all_action_strings(action_count, max_depth):
    out = [tuple()]
    for n in range(1, int(max_depth) + 1):
        out.extend(
            tuple(x)
            for x in itertools.product(range(action_count), repeat=n)
        )
    return tuple(out)


def build_table(
    world,
    tests=TESTS,
    history_depth=5,
    complete=True,
    table_id="",
):
    action_strings = all_action_strings(3, history_depth)
    histories = []
    latent_after = []

    for actions in action_strings:
        state, hist = world.history_from_actions(actions)
        histories.append(hist)
        latent_after.append(state)

    outcomes = []
    for state in latent_after:
        row = []
        for test in tests:
            _end, obs = world.run_actions(state, test)
            row.append(obs)
        outcomes.append(tuple(row))

    return ConsequenceTable(
        action_count=3,
        observation_count=2,
        histories=tuple(histories),
        tests=tuple(tuple(int(a) for a in t) for t in tests),
        outcomes=tuple(outcomes),
        complete=bool(complete),
        table_id=table_id or world.name,
    )


def cycle_world(length, name, rename=None):
    # State 0 is homogeneous baseline. States 1..length carry a latent
    # disturbance. Action 0 injects/resets the disturbance to phase 1.
    # Action 1 advances it. Action 2 observes only whether it is at phase 1.
    canonical = tuple(range(length + 1))

    def canonical_step(s, a):
        if a == 0:
            return 1, 0
        if a == 1:
            if s == 0:
                return 0, 0
            return (1 + (s % length)), 0
        if a == 2:
            return s, 1 if s == 1 else 0
        raise ValueError(a)

    if rename is None:
        return HiddenTransducer(
            canonical,
            0,
            canonical_step,
            name,
        )

    p = tuple(int(x) for x in rename)
    if sorted(p) != list(canonical):
        raise ValueError("invalid hidden-state renaming")
    inv = {p[i]: i for i in canonical}

    def renamed_step(s, a):
        old = inv[s]
        old2, o = canonical_step(old, a)
        return p[old2], o

    return HiddenTransducer(
        tuple(p),
        p[0],
        renamed_step,
        name,
    )


def heterogeneous_world(name):
    states = (0, 1, 2, 3)

    def step(s, a):
        if a == 0:
            nxt = (1, 3, 0, 2)[s]
            return nxt, 0
        if a == 1:
            nxt = (0, 2, 3, 1)[s]
            return nxt, 0
        if a == 2:
            return s, 1 if s in (1, 3) else 0
        raise ValueError(a)

    return HiddenTransducer(states, 0, step, name)


WORLD_A = cycle_world(4, "cycle4_a")
WORLD_B = cycle_world(4, "cycle4_b", rename=(4, 2, 0, 3, 1))
WORLD_C = cycle_world(4, "cycle4_c", rename=(1, 4, 2, 0, 3))
WORLD_WRONG = cycle_world(5, "cycle5_wrong")
WORLD_HET = heterogeneous_world("heterogeneous_memory")

TABLE_A = build_table(WORLD_A, table_id="cycle4_a")
TABLE_B = build_table(WORLD_B, table_id="cycle4_b")
TABLE_C = build_table(WORLD_C, table_id="cycle4_c")
TABLE_WRONG = build_table(WORLD_WRONG, table_id="cycle5_wrong")
TABLE_HET = build_table(WORLD_HET, table_id="heterogeneous_memory")
TABLE_INCOMPLETE = ConsequenceTable(
    action_count=TABLE_A.action_count,
    observation_count=TABLE_A.observation_count,
    histories=TABLE_A.histories,
    tests=TABLE_A.tests,
    outcomes=TABLE_A.outcomes,
    complete=False,
    table_id="cycle4_incomplete_authority",
)


# ---------------------------------------------------------------------------
# Explicit non-canonicity challenge generated only from anonymous consequence
# tables. The learner receives no semantic feature names.
#
# On training histories, either length-2 future test is a complete minimum
# predictive code. On qualification histories, only test 1 preserves the full
# future-consequence quotient.
# ---------------------------------------------------------------------------

AMBIG_TESTS = ((0, 0), (1, 1))

AMBIG_TRAIN = ConsequenceTable(
    action_count=2,
    observation_count=2,
    histories=(
        tuple(),
        ((0, 0),),
    ),
    tests=AMBIG_TESTS,
    outcomes=(
        ((0, 0), (0, 1)),
        ((1, 1), (1, 0)),
    ),
    complete=True,
    table_id="ambiguous_train",
)

AMBIG_QUAL = ConsequenceTable(
    action_count=2,
    observation_count=2,
    histories=(
        tuple(),
        ((0, 0),),
        ((1, 0),),
    ),
    tests=AMBIG_TESTS,
    outcomes=(
        ((0, 0), (0, 1)),
        ((1, 1), (1, 0)),
        ((0, 0), (1, 1)),
    ),
    complete=True,
    table_id="ambiguous_qualification",
)
