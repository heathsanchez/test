#!/usr/bin/env python3
"""Frozen V13 atomic-action phrase substrate.

Multi-action tests are not primitives. They are generated from atomic actions by
CONCAT inside the frozen grammar.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


Action = int
Observation = int
History = Tuple[Tuple[Action, Observation], ...]
Phrase = Tuple[Action, ...]
Outcome = Tuple[Observation, ...]


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def generate_phrases(
    action_count: int,
    max_length: int,
    concat_enabled: bool = True,
) -> Tuple[Phrase, ...]:
    atoms = tuple((a,) for a in range(int(action_count)))
    if not concat_enabled or int(max_length) <= 1:
        return atoms
    out = list(atoms)
    level = atoms
    for _length in range(2, int(max_length) + 1):
        next_level = []
        for prefix in level:
            for a in range(int(action_count)):
                next_level.append(prefix + (a,))
        out.extend(next_level)
        level = tuple(next_level)
    return tuple(out)


@dataclass(frozen=True)
class PhraseWorld:
    action_count: int
    observation_count: int
    histories: Tuple[History, ...]
    max_phrase_length: int
    outcomes: Mapping[Phrase, Tuple[Outcome, ...]]
    complete: bool
    world_id: str = ""

    def __post_init__(self) -> None:
        if self.action_count <= 0 or self.observation_count <= 0:
            raise ValueError("alphabets must be nonempty")
        if self.max_phrase_length <= 0:
            raise ValueError("phrase bound must be positive")
        if self.complete:
            expected = set(
                generate_phrases(
                    self.action_count,
                    self.max_phrase_length,
                    concat_enabled=True,
                )
            )
            if set(self.outcomes.keys()) != expected:
                raise ValueError("complete world must contain every generated phrase")
        for phrase, row in self.outcomes.items():
            if not phrase:
                raise ValueError("empty phrase not a test")
            if len(phrase) > self.max_phrase_length:
                raise ValueError("phrase exceeds bound")
            if len(row) != len(self.histories):
                raise ValueError("outcome/history mismatch")
            for a in phrase:
                if not (0 <= int(a) < self.action_count):
                    raise ValueError("action outside alphabet")
            for out in row:
                if len(out) != len(phrase):
                    raise ValueError("outcome length must match phrase length")
                for o in out:
                    if not (0 <= int(o) < self.observation_count):
                        raise ValueError("observation outside alphabet")

    def outcome(self, history_index: int, phrase: Phrase) -> Outcome:
        return self.outcomes[tuple(phrase)][int(history_index)]

    def interface_key(self) -> Tuple[int, int, int]:
        return (
            int(self.action_count),
            int(self.observation_count),
            int(self.max_phrase_length),
        )

    def data(self) -> Any:
        return {
            "world_id": self.world_id,
            "action_count": self.action_count,
            "observation_count": self.observation_count,
            "history_count": len(self.histories),
            "max_phrase_length": self.max_phrase_length,
            "complete": self.complete,
        }


def phrase_signature(
    world: PhraseWorld,
    history_index: int,
    phrases: Iterable[Phrase],
) -> Tuple[Outcome, ...]:
    ps = tuple(sorted(set(tuple(p) for p in phrases)))
    return tuple(world.outcome(history_index, p) for p in ps)


def partition(
    world: PhraseWorld,
    phrases: Iterable[Phrase],
) -> Tuple[Tuple[int, ...], ...]:
    groups: Dict[Tuple[Outcome, ...], list[int]] = {}
    ps = tuple(sorted(set(tuple(p) for p in phrases)))
    for i in range(len(world.histories)):
        key = phrase_signature(world, i, ps)
        groups.setdefault(key, []).append(i)
    classes = [tuple(v) for v in groups.values()]
    classes.sort(key=lambda c: (len(c), c))
    return tuple(classes)


def full_partition(world: PhraseWorld) -> Tuple[Tuple[int, ...], ...]:
    return partition(
        world,
        generate_phrases(
            world.action_count,
            world.max_phrase_length,
            concat_enabled=True,
        ),
    )


def same_partition(
    left: Sequence[Sequence[int]],
    right: Sequence[Sequence[int]],
) -> bool:
    norm = lambda xs: sorted(tuple(sorted(int(x) for x in c)) for c in xs)
    return norm(left) == norm(right)


def phrase_set_cost(phrases: Iterable[Phrase]) -> Tuple[int, int]:
    ps = tuple(sorted(set(tuple(p) for p in phrases)))
    return (len(ps), sum(len(p) for p in ps))


def phrase_digest(
    world: PhraseWorld,
    phrase: Phrase,
) -> str:
    return digest_json({
        "interface": list(world.interface_key()),
        "expansion": list(phrase),
    })
