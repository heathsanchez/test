#!/usr/bin/env python3
"""Post-freeze hidden worlds for V13 generated predictive phrases.

Hidden state and dynamics exist only on the challenge side to generate complete
bounded consequence oracles. The frozen learner sees only anonymous histories,
atomic action alphabet, phrase-length bound, and phrase outcomes.
"""
from __future__ import annotations

import itertools
from typing import Dict, Sequence, Tuple

from basis import PhraseWorld, generate_phrases


ACTION_COUNT = 3
OBSERVATION_COUNT = 2
MAX_PHRASE_LENGTH = 7
HISTORY_DEPTH = 4


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


def all_action_strings(action_count, max_depth, include_empty=True):
    out = [tuple()] if include_empty else []
    for n in range(1, int(max_depth) + 1):
        out.extend(
            tuple(x)
            for x in itertools.product(range(action_count), repeat=n)
        )
    return tuple(out)


def build_world(
    hidden,
    *,
    max_phrase_length=MAX_PHRASE_LENGTH,
    history_depth=HISTORY_DEPTH,
    complete=True,
    world_id="",
):
    history_actions = all_action_strings(
        ACTION_COUNT,
        history_depth,
        include_empty=True,
    )
    histories = []
    latent = []
    for actions in history_actions:
        state, hist = hidden.history_from_actions(actions)
        histories.append(hist)
        latent.append(state)

    phrases = generate_phrases(
        ACTION_COUNT,
        max_phrase_length,
        concat_enabled=True,
    )
    outcomes = {}
    for phrase in phrases:
        row = []
        for state in latent:
            _end, obs = hidden.run_actions(state, phrase)
            row.append(obs)
        outcomes[phrase] = tuple(row)

    return PhraseWorld(
        action_count=ACTION_COUNT,
        observation_count=OBSERVATION_COUNT,
        histories=tuple(histories),
        max_phrase_length=max_phrase_length,
        outcomes=outcomes,
        complete=bool(complete),
        world_id=world_id or hidden.name,
    )


def cycle_world(length, name, rename=None):
    canonical = tuple(range(length + 1))

    def canonical_step(s, a):
        # a=0 inject/reset disturbance; a=1 advance; a=2 probe.
        if a == 0:
            return 1, 0
        if a == 1:
            if s == 0:
                return 0, 0
            return 1 + (s % length), 0
        if a == 2:
            return s, 1 if s == 1 else 0
        raise ValueError(a)

    if rename is None:
        return HiddenTransducer(canonical, 0, canonical_step, name)

    p = tuple(int(x) for x in rename)
    if sorted(p) != list(canonical):
        raise ValueError("invalid hidden-state renaming")
    inv = {p[i]: i for i in canonical}

    def renamed_step(s, a):
        old = inv[s]
        old2, o = canonical_step(old, a)
        return p[old2], o

    return HiddenTransducer(tuple(p), p[0], renamed_step, name)


def heterogeneous_world(name):
    states = (0, 1, 2, 3)

    def step(s, a):
        if a == 0:
            return (1, 3, 0, 2)[s], 0
        if a == 1:
            return (0, 2, 3, 1)[s], 0
        if a == 2:
            return s, 1 if s in (1, 3) else 0
        raise ValueError(a)

    return HiddenTransducer(states, 0, step, name)


WORLD_A_HIDDEN = cycle_world(4, "cycle4_phrase_a")
WORLD_B_HIDDEN = cycle_world(4, "cycle4_phrase_b", rename=(4, 2, 0, 3, 1))
WORLD_C_HIDDEN = cycle_world(4, "cycle4_phrase_c", rename=(1, 4, 2, 0, 3))
WORLD_WRONG_HIDDEN = cycle_world(5, "cycle5_wrong_phrase")
WORLD_HET_HIDDEN = heterogeneous_world("heterogeneous_phrase")

WORLD_A = build_world(WORLD_A_HIDDEN, world_id="cycle4_phrase_a")
WORLD_B = build_world(WORLD_B_HIDDEN, world_id="cycle4_phrase_b")
WORLD_C = build_world(WORLD_C_HIDDEN, world_id="cycle4_phrase_c")
WORLD_WRONG = build_world(WORLD_WRONG_HIDDEN, world_id="cycle5_wrong_phrase")
WORLD_HET = build_world(WORLD_HET_HIDDEN, world_id="heterogeneous_phrase")

WORLD_INCOMPLETE = PhraseWorld(
    action_count=WORLD_A.action_count,
    observation_count=WORLD_A.observation_count,
    histories=WORLD_A.histories,
    max_phrase_length=WORLD_A.max_phrase_length,
    outcomes=dict(WORLD_A.outcomes),
    complete=False,
    world_id="cycle4_incomplete_phrase_authority",
)


# ---------------------------------------------------------------------------
# Explicit generated-phrase non-canonicity challenge.
# Only atomic actions are primitive. Both length-2 phrases (0,0) and (1,1)
# are shortest complete codes on training consequence. Qualification keeps
# only (1,1).
# ---------------------------------------------------------------------------

AMBIG_PHRASES = generate_phrases(2, 2, concat_enabled=True)

AMBIG_TRAIN_OUTCOMES = {
    (0,): ((0,), (0,)),
    (1,): ((0,), (0,)),
    (0,0): ((0,0), (1,1)),
    (0,1): ((0,0), (0,0)),
    (1,0): ((0,0), (0,0)),
    (1,1): ((0,1), (1,0)),
}

AMBIG_QUAL_OUTCOMES = {
    (0,): ((0,), (0,), (0,)),
    (1,): ((0,), (0,), (0,)),
    (0,0): ((0,0), (1,1), (0,0)),
    (0,1): ((0,0), (0,0), (0,0)),
    (1,0): ((0,0), (0,0), (0,0)),
    (1,1): ((0,1), (1,0), (1,1)),
}

AMBIG_TRAIN = PhraseWorld(
    action_count=2,
    observation_count=2,
    histories=(tuple(), ((0,0),)),
    max_phrase_length=2,
    outcomes=AMBIG_TRAIN_OUTCOMES,
    complete=True,
    world_id="ambiguous_generated_phrase_train",
)

AMBIG_QUAL = PhraseWorld(
    action_count=2,
    observation_count=2,
    histories=(tuple(), ((0,0),), ((1,0),)),
    max_phrase_length=2,
    outcomes=AMBIG_QUAL_OUTCOMES,
    complete=True,
    world_id="ambiguous_generated_phrase_qualification",
)
