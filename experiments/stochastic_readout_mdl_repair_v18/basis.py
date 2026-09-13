#!/usr/bin/env python3
"""Frozen V17 stochastic raw-readout substrate."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


Accessor = int
Context = Tuple[int, ...]
BinaryCounts = Tuple[int, int]


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


@dataclass(frozen=True)
class StochasticWorld:
    channel_count: int
    contexts: Tuple[Context, ...]
    future_tests: Tuple[Tuple[int, ...], ...]
    counts: Tuple[Tuple[BinaryCounts, ...], ...]
    complete: bool
    world_id: str = ""

    def __post_init__(self) -> None:
        if self.channel_count <= 0:
            raise ValueError("channel_count must be positive")
        if len(self.contexts) != len(self.counts):
            raise ValueError("context/count row mismatch")
        for x in self.contexts:
            if len(x) != self.channel_count:
                raise ValueError("context width mismatch")
        for row in self.counts:
            if len(row) != len(self.future_tests):
                raise ValueError("future-test width mismatch")
            for n0,n1 in row:
                if min(int(n0), int(n1)) < 0:
                    raise ValueError("counts must be nonnegative")

    def accessor_value(self, context_index: int, accessor: Accessor) -> int:
        return self.contexts[int(context_index)][int(accessor)]

    def interface_key(self) -> Tuple[int, Tuple[Tuple[int, ...], ...]]:
        return (self.channel_count, self.future_tests)

    def data(self) -> Any:
        return {
            "world_id": self.world_id,
            "channel_count": self.channel_count,
            "context_count": len(self.contexts),
            "future_test_count": len(self.future_tests),
            "complete": self.complete,
        }


def partition(
    world: StochasticWorld,
    accessors: Iterable[Accessor],
) -> Tuple[Tuple[int, ...], ...]:
    aa = tuple(sorted(set(int(a) for a in accessors)))
    groups: Dict[Tuple[int, ...], list[int]] = {}
    for i in range(len(world.contexts)):
        key = tuple(world.accessor_value(i,a) for a in aa)
        groups.setdefault(key, []).append(i)
    classes = [tuple(v) for v in groups.values()]
    classes.sort(key=lambda c: (len(c), c))
    return tuple(classes)


def readout_digest(
    world: StochasticWorld,
    accessors: Iterable[Accessor],
) -> str:
    aa = tuple(sorted(set(int(a) for a in accessors)))
    return digest_json({
        "interface": [
            world.channel_count,
            [list(t) for t in world.future_tests],
        ],
        "accessors": list(aa),
    })
