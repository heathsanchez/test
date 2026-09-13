#!/usr/bin/env python3
"""Post-freeze exact anonymous multichannel worlds for V16.

These are challenge-side generators/tables. Channel semantics are intentionally
absent from the frozen learner.
"""
from __future__ import annotations

from basis import MultichannelWorld


FUTURE_TESTS = ((0,), (1,))


def outcome_row(label: int):
    # Anonymous future consequences; unique row per predictive class.
    table = {
        0: ((0,), (0,)),
        1: ((0,), (1,)),
        2: ((1,), (0,)),
        3: ((1,), (1,)),
        4: ((0, 1), (1, 0)),
        5: ((1, 0), (0, 1)),
        6: ((1, 1), (0, 0)),
        7: ((0, 0), (1, 1)),
    }
    return table[int(label)]


def make_main(order, world_id):
    # Six anonymous raw channels. Only present channels 1 and 4 are jointly
    # sufficient. The others are constants: no engineered distractor feature.
    states = [
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    ]
    windows = []
    outcomes = []

    rows = []
    for rep in range(2):
        for b1, b2 in states:
            current = (7, b1, 5, 9, b2, 4)
            previous = (3, rep, 8, 8, rep, 6)
            label = 2 * b1 + b2
            rows.append(((current, previous), outcome_row(label)))

    for idx in order:
        w, o = rows[idx]
        windows.append(w)
        outcomes.append(o)

    return MultichannelWorld(
        channel_count=6,
        max_lag=1,
        windows=tuple(windows),
        future_tests=FUTURE_TESTS,
        outcomes=tuple(outcomes),
        complete=True,
        world_id=world_id,
    )


MAIN_A = make_main(tuple(range(8)), "main_a")
MAIN_B = make_main((4,0,5,1,6,2,7,3), "main_b")
MAIN_C = make_main((7,3,6,2,5,1,4,0), "main_c")


def make_memory_world():
    # Present vectors are identical inside consequentially distinct pairs.
    # Previous channel 2 is the minimum sufficient memory readout.
    windows = []
    outcomes = []
    for rep in range(3):
        for state in (0, 1):
            current = (5, 5, 5, 5, 5, 5)
            previous = (9, 9, state, 9, 9, 9)
            windows.append((current, previous))
            outcomes.append(outcome_row(state))
    return MultichannelWorld(
        channel_count=6,
        max_lag=1,
        windows=tuple(windows),
        future_tests=FUTURE_TESTS,
        outcomes=tuple(outcomes),
        complete=True,
        world_id="memory_required",
    )


MEMORY_WORLD = make_memory_world()


# Non-canonicity: c0 and c1 are equal-cost sufficient readouts on training.
NONCAN_TRAIN = MultichannelWorld(
    channel_count=4,
    max_lag=0,
    windows=(
        ((0,0,7,7),),
        ((1,1,7,7),),
        ((0,0,7,7),),
        ((1,1,7,7),),
    ),
    future_tests=FUTURE_TESTS,
    outcomes=(
        outcome_row(0),
        outcome_row(1),
        outcome_row(0),
        outcome_row(1),
    ),
    complete=True,
    world_id="noncanonical_train",
)

# Qualification: c0 is now constant while c1 still carries the future split.
NONCAN_QUAL = MultichannelWorld(
    channel_count=4,
    max_lag=0,
    windows=(
        ((0,0,7,7),),
        ((0,1,7,7),),
        ((0,0,7,7),),
        ((0,1,7,7),),
    ),
    future_tests=FUTURE_TESTS,
    outcomes=(
        outcome_row(0),
        outcome_row(1),
        outcome_row(0),
        outcome_row(1),
    ),
    complete=True,
    world_id="noncanonical_qualification",
)


def make_wrong_world():
    # Same interface, different consequence-bearing raw coordinates.
    windows = []
    outcomes = []
    for rep in range(2):
        for b1, b2 in ((0,0),(0,1),(1,0),(1,1)):
            current = (7, 0, b1, 9, 0, b2)
            previous = (3, rep, 8, 8, rep, 6)
            windows.append((current, previous))
            outcomes.append(outcome_row(2*b1+b2))
    return MultichannelWorld(
        channel_count=6,
        max_lag=1,
        windows=tuple(windows),
        future_tests=FUTURE_TESTS,
        outcomes=tuple(outcomes),
        complete=True,
        world_id="wrong_dynamics",
    )


WRONG_WORLD = make_wrong_world()


def make_heterogeneous_world():
    # Eight consequential classes encoded by three raw present coordinates.
    windows = []
    outcomes = []
    for bits in (
        (0,0,0),(0,0,1),(0,1,0),(0,1,1),
        (1,0,0),(1,0,1),(1,1,0),(1,1,1),
    ):
        a,b,c = bits
        current = (a, 5, b, 8, 8, c)
        previous = (9,9,9,9,9,9)
        label = 4*a + 2*b + c
        windows.append((current, previous))
        outcomes.append(outcome_row(label))
    return MultichannelWorld(
        channel_count=6,
        max_lag=1,
        windows=tuple(windows),
        future_tests=FUTURE_TESTS,
        outcomes=tuple(outcomes),
        complete=True,
        world_id="heterogeneous_three_coordinate",
    )


HETEROGENEOUS = make_heterogeneous_world()

INCOMPLETE = MultichannelWorld(
    channel_count=MAIN_A.channel_count,
    max_lag=MAIN_A.max_lag,
    windows=MAIN_A.windows,
    future_tests=MAIN_A.future_tests,
    outcomes=MAIN_A.outcomes,
    complete=False,
    world_id="incomplete_authority",
)
