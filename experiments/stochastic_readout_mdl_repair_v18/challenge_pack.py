#!/usr/bin/env python3
"""Post-freeze seeded stochastic multichannel worlds for V17."""
from __future__ import annotations

import random
from basis import StochasticWorld


TESTS = ((0,), (1,))


def draw_counts(p, n, rng):
    ones = sum(1 for _ in range(int(n)) if rng.random() < float(p))
    return (int(n) - ones, ones)


def main_world(seed, world_id, trials=48):
    rng = random.Random(seed)
    contexts = []
    counts = []
    for rep in range(2):
        for b1,b2 in ((0,0),(0,1),(1,0),(1,1)):
            x = (7, b1, 5, 9, b2, 4)
            p0 = 0.10 if b1 == 0 else 0.90
            p1 = 0.20 if b2 == 0 else 0.80
            contexts.append(x)
            counts.append((
                draw_counts(p0, trials, rng),
                draw_counts(p1, trials, rng),
            ))
    return StochasticWorld(
        channel_count=6,
        contexts=tuple(contexts),
        future_tests=TESTS,
        counts=tuple(counts),
        complete=True,
        world_id=world_id,
    )


MAIN_A = main_world(1701, "main_noisy_a")
MAIN_B = main_world(1702, "main_noisy_b")
MAIN_C = main_world(1703, "main_noisy_c")
MAIN_QUAL = main_world(1704, "main_noisy_qualification")


# Non-canonicity: channels 0 and 1 are identical on training, therefore exact
# score ties. Qualification makes channel 0 constant while channel 1 remains
# consequence-bearing.
def noncan_train():
    rng = random.Random(1710)
    contexts = []
    counts = []
    for rep in range(4):
        for b in (0,1):
            contexts.append((b,b,7,7))
            p = 0.12 if b == 0 else 0.88
            counts.append((
                draw_counts(p, 60, rng),
                draw_counts(p, 60, rng),
            ))
    return StochasticWorld(
        channel_count=4,
        contexts=tuple(contexts),
        future_tests=TESTS,
        counts=tuple(counts),
        complete=True,
        world_id="noncanonical_train",
    )


def noncan_qual():
    rng = random.Random(1711)
    contexts = []
    counts = []
    for rep in range(4):
        for b in (0,1):
            contexts.append((0,b,7,7))
            p = 0.12 if b == 0 else 0.88
            counts.append((
                draw_counts(p, 60, rng),
                draw_counts(p, 60, rng),
            ))
    return StochasticWorld(
        channel_count=4,
        contexts=tuple(contexts),
        future_tests=TESTS,
        counts=tuple(counts),
        complete=True,
        world_id="noncanonical_qualification",
    )


NONCAN_TRAIN = noncan_train()
NONCAN_QUAL = noncan_qual()


def wrong_world(seed=1720):
    rng = random.Random(seed)
    contexts = []
    counts = []
    for rep in range(2):
        for b1,b2 in ((0,0),(0,1),(1,0),(1,1)):
            x = (7, 0, b1, 9, 0, b2)
            p0 = 0.10 if b1 == 0 else 0.90
            p1 = 0.20 if b2 == 0 else 0.80
            contexts.append(x)
            counts.append((
                draw_counts(p0, 48, rng),
                draw_counts(p1, 48, rng),
            ))
    return StochasticWorld(
        channel_count=6,
        contexts=tuple(contexts),
        future_tests=TESTS,
        counts=tuple(counts),
        complete=True,
        world_id="wrong_dynamics",
    )


WRONG = wrong_world()


def heterogeneous(seed=1730):
    rng = random.Random(seed)
    contexts = []
    counts = []
    p0map = {
        (0,0):0.08,
        (0,1):0.35,
        (1,0):0.65,
        (1,1):0.92,
    }
    for a,b,c in (
        (0,0,0),(0,0,1),(0,1,0),(0,1,1),
        (1,0,0),(1,0,1),(1,1,0),(1,1,1),
    ):
        contexts.append((a,5,b,8,8,c))
        p0 = p0map[(a,b)]
        p1 = 0.15 if c == 0 else 0.85
        counts.append((
            draw_counts(p0, 64, rng),
            draw_counts(p1, 64, rng),
        ))
    return StochasticWorld(
        channel_count=6,
        contexts=tuple(contexts),
        future_tests=TESTS,
        counts=tuple(counts),
        complete=True,
        world_id="heterogeneous_noisy",
    )


HETEROGENEOUS = heterogeneous()


# Low-data control: a valid tiny realization contains no observed distinction.
LOW_DATA = StochasticWorld(
    channel_count=6,
    contexts=MAIN_A.contexts,
    future_tests=TESTS,
    counts=tuple(
        ((1,0),(1,0))
        for _ in MAIN_A.contexts
    ),
    complete=True,
    world_id="low_data_no_evidence",
)

INCOMPLETE = StochasticWorld(
    channel_count=MAIN_A.channel_count,
    contexts=MAIN_A.contexts,
    future_tests=MAIN_A.future_tests,
    counts=MAIN_A.counts,
    complete=False,
    world_id="incomplete_statistical_authority",
)
