#!/usr/bin/env python3
"""Frozen V16 raw multichannel predictive representation substrate."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


Value = int
RawFrame = Tuple[Value, ...]
RawWindow = Tuple[RawFrame, ...]
FutureOutcome = Tuple[int, ...]
Accessor = Tuple[int, int]  # (lag, channel)


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


@dataclass(frozen=True)
class MultichannelWorld:
    channel_count: int
    max_lag: int
    windows: Tuple[RawWindow, ...]
    future_tests: Tuple[Tuple[int, ...], ...]
    outcomes: Tuple[Tuple[FutureOutcome, ...], ...]
    complete: bool
    world_id: str = ""

    def __post_init__(self) -> None:
        if self.channel_count <= 0:
            raise ValueError("channel_count must be positive")
        if self.max_lag < 0:
            raise ValueError("max_lag must be nonnegative")
        if len(self.windows) != len(self.outcomes):
            raise ValueError("window/outcome count mismatch")

        required_depth = self.max_lag + 1
        for w in self.windows:
            if len(w) < required_depth:
                raise ValueError("window shorter than declared max_lag")
            for frame in w:
                if len(frame) != self.channel_count:
                    raise ValueError("frame width mismatch")

        for row in self.outcomes:
            if len(row) != len(self.future_tests):
                raise ValueError("future-test outcome width mismatch")

    def interface_key(self) -> Tuple[int, int, Tuple[Tuple[int, ...], ...]]:
        return (
            self.channel_count,
            self.max_lag,
            self.future_tests,
        )

    def accessor_value(self, history_index: int, accessor: Accessor) -> Value:
        lag, channel = accessor
        return self.windows[int(history_index)][int(lag)][int(channel)]

    def accessor_cost(self, accessor: Accessor) -> int:
        lag, _channel = accessor
        return 1 + int(lag)

    def data(self) -> Any:
        return {
            "world_id": self.world_id,
            "channel_count": self.channel_count,
            "max_lag": self.max_lag,
            "history_count": len(self.windows),
            "future_test_count": len(self.future_tests),
            "complete": self.complete,
        }


def generated_accessors(
    world: MultichannelWorld,
    authorized_lag: int,
) -> Tuple[Accessor, ...]:
    d = min(int(authorized_lag), world.max_lag)
    return tuple(
        (lag, channel)
        for lag in range(d + 1)
        for channel in range(world.channel_count)
    )


def readout_signature(
    world: MultichannelWorld,
    history_index: int,
    accessors: Iterable[Accessor],
) -> Tuple[Value, ...]:
    aa = tuple(sorted(set((int(l), int(c)) for l, c in accessors)))
    return tuple(world.accessor_value(history_index, a) for a in aa)


def partition(
    world: MultichannelWorld,
    accessors: Iterable[Accessor],
) -> Tuple[Tuple[int, ...], ...]:
    aa = tuple(sorted(set((int(l), int(c)) for l, c in accessors)))
    groups: Dict[Tuple[Value, ...], list[int]] = {}
    for i in range(len(world.windows)):
        key = readout_signature(world, i, aa)
        groups.setdefault(key, []).append(i)
    classes = [tuple(v) for v in groups.values()]
    classes.sort(key=lambda c: (len(c), c))
    return tuple(classes)


def future_partition(world: MultichannelWorld) -> Tuple[Tuple[int, ...], ...]:
    groups: Dict[Tuple[FutureOutcome, ...], list[int]] = {}
    for i, row in enumerate(world.outcomes):
        groups.setdefault(tuple(row), []).append(i)
    classes = [tuple(v) for v in groups.values()]
    classes.sort(key=lambda c: (len(c), c))
    return tuple(classes)


def same_partition(
    left: Sequence[Sequence[int]],
    right: Sequence[Sequence[int]],
) -> bool:
    norm = lambda xs: sorted(tuple(sorted(int(x) for x in c)) for c in xs)
    return norm(left) == norm(right)


def readout_cost(
    world: MultichannelWorld,
    accessors: Iterable[Accessor],
) -> Tuple[int, int]:
    aa = tuple(sorted(set((int(l), int(c)) for l, c in accessors)))
    return (
        len(aa),
        sum(world.accessor_cost(a) for a in aa),
    )


def readout_digest(
    world: MultichannelWorld,
    accessors: Iterable[Accessor],
) -> str:
    aa = tuple(sorted(set((int(l), int(c)) for l, c in accessors)))
    return digest_json({
        "interface": [
            world.channel_count,
            world.max_lag,
            [list(t) for t in world.future_tests],
        ],
        "accessors": [list(a) for a in aa],
    })
