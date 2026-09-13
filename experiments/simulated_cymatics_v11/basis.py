#!/usr/bin/env python3
"""Frozen V11 exact anonymous vibration substrate.

No coordinates, spectral quantities, geometry labels, or wave equation are
represented here.  The substrate contains only anonymous channels, exact
finite-valued frames, binary influence relations, equality, and relational
composition.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, FrozenSet, Iterable, List, Mapping, Sequence, Tuple


@dataclass(frozen=True)
class BasisConfig:
    compose: bool = True
    temporal_replay: bool = True

    def data(self) -> Any:
        return {
            "COMPOSE": self.compose,
            "TEMPORAL_REPLAY": self.temporal_replay,
        }


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


@dataclass(frozen=True)
class InfluenceRelation:
    size: int
    rows: Tuple[FrozenSet[int], ...]

    def __post_init__(self) -> None:
        if len(self.rows) != self.size:
            raise ValueError("row count mismatch")
        for row in self.rows:
            if any(type(j) is not int or not (0 <= j < self.size) for j in row):
                raise ValueError("edge outside channel carrier")

    def data(self) -> Any:
        return {
            "size": self.size,
            "rows": [sorted(r) for r in self.rows],
        }

    def digest(self) -> str:
        return digest_json(self.data())

    def out_degrees(self) -> Tuple[int, ...]:
        return tuple(len(r) for r in self.rows)

    def in_degrees(self) -> Tuple[int, ...]:
        return tuple(
            sum(j in self.rows[i] for i in range(self.size))
            for j in range(self.size)
        )


def compose_relations(
    first: InfluenceRelation,
    second: InfluenceRelation,
) -> InfluenceRelation:
    if first.size != second.size:
        raise TypeError("carrier mismatch")
    rows: List[FrozenSet[int]] = []
    for i in range(first.size):
        targets = set()
        for mid in first.rows[i]:
            targets.update(second.rows[mid])
        rows.append(frozenset(targets))
    return InfluenceRelation(first.size, tuple(rows))


@dataclass(frozen=True)
class FrameTrace:
    channel_count: int
    frames: Tuple[Tuple[int, ...], ...]
    baseline: int

    def __post_init__(self) -> None:
        if len(self.frames) < 2:
            raise ValueError("at least two frames required")
        for frame in self.frames:
            if len(frame) != self.channel_count:
                raise ValueError("frame width mismatch")

    def data(self) -> Any:
        return {
            "channel_count": self.channel_count,
            "frame_count": len(self.frames),
            "baseline": self.baseline,
            "frames": [list(f) for f in self.frames],
        }

    def digest(self) -> str:
        return digest_json(self.data())


def induced_relation(
    relation: InfluenceRelation,
    subset: Iterable[int],
) -> InfluenceRelation:
    kept = tuple(sorted(set(int(x) for x in subset)))
    index = {old: new for new, old in enumerate(kept)}
    rows: List[FrozenSet[int]] = []
    for old_i in kept:
        rows.append(
            frozenset(
                index[old_j]
                for old_j in relation.rows[old_i]
                if old_j in index
            )
        )
    return InfluenceRelation(len(kept), tuple(rows))
