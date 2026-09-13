#!/usr/bin/env python3
"""Frozen V10 coordinate-free finite influence-relation substrate."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, FrozenSet, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class BasisConfig:
    compose: bool = True

    def data(self):
        return {"COMPOSE": self.compose}


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


@dataclass(frozen=True)
class InfluenceRelation:
    size: int
    rows: Tuple[FrozenSet[int], ...]

    def __post_init__(self):
        if len(self.rows) != self.size:
            raise ValueError("row count mismatch")
        for row in self.rows:
            if any(j < 0 or j >= self.size for j in row):
                raise ValueError("edge outside channel carrier")

    def data(self):
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
    rows = []
    for i in range(first.size):
        targets = set()
        for mid in first.rows[i]:
            targets.update(second.rows[mid])
        rows.append(frozenset(targets))
    return InfluenceRelation(first.size, tuple(rows))


def identity_relation(n: int) -> InfluenceRelation:
    return InfluenceRelation(
        int(n),
        tuple(frozenset({i}) for i in range(int(n))),
    )


@dataclass(frozen=True)
class ComponentCarrier:
    carrier_id: str
    classes: Tuple[Tuple[int, ...], ...]

    @property
    def size(self) -> int:
        return len(self.classes)

    def data(self):
        return {
            "carrier_id": self.carrier_id,
            "size": self.size,
            "classes": [list(c) for c in self.classes],
        }


def component_carrier(classes: Sequence[Sequence[int]]) -> ComponentCarrier:
    cs = tuple(tuple(sorted(int(x) for x in c)) for c in classes)
    cid = "blk_" + digest_json([list(c) for c in cs])[:16]
    return ComponentCarrier(cid, cs)
