#!/usr/bin/env python3
"""Frozen V6 lower meta-language and generic carrier materializer."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Iterable, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# Anonymous finite carrier materializer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Carrier:
    carrier_id: str
    size: int

    def values(self) -> Tuple[Any, ...]:
        return tuple((self.carrier_id, i) for i in range(self.size))

    def data(self) -> Any:
        return {"carrier_id": self.carrier_id, "size": self.size}


def carrier_id(size: int) -> str:
    raw = json.dumps({"finite_carrier_size": int(size)}, sort_keys=True).encode()
    return "c_" + hashlib.sha256(raw).hexdigest()[:16]


def materialize_carrier(size: int) -> Carrier:
    if type(size) is not int or size <= 0:
        raise ValueError("carrier size must be positive int")
    return Carrier(carrier_id(size), size)


# ---------------------------------------------------------------------------
# Searchable meta-programs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MetaExpr:
    op: str
    args: Tuple["MetaExpr", ...] = ()

    @property
    def cost(self) -> int:
        return 1 + sum(a.cost for a in self.args)

    def to_data(self) -> Any:
        return {"op": self.op, "args": [a.to_data() for a in self.args]}

    def serial(self) -> str:
        return json.dumps(self.to_data(), sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return hashlib.sha256(self.serial().encode()).hexdigest()


def CURRENT() -> MetaExpr:
    return MetaExpr("current")


def DELTA() -> MetaExpr:
    return MetaExpr("delta")


def ONE() -> MetaExpr:
    return MetaExpr("one")


def SUCC(e: MetaExpr) -> MetaExpr:
    return MetaExpr("succ", (e,))


def ADD(a: MetaExpr, b: MetaExpr) -> MetaExpr:
    return MetaExpr("add", (a, b))


def eval_meta(e: MetaExpr, current: int, delta: int) -> int:
    if e.op == "current":
        return int(current)
    if e.op == "delta":
        return int(delta)
    if e.op == "one":
        return 1
    if e.op == "succ":
        return eval_meta(e.args[0], current, delta) + 1
    if e.op == "add":
        return (
            eval_meta(e.args[0], current, delta)
            + eval_meta(e.args[1], current, delta)
        )
    raise ValueError(e.op)


CALIBRATION_CURRENT = tuple(range(1, 13))
CALIBRATION_DELTA = tuple(range(1, 9))


def behavior_key(e: MetaExpr) -> str:
    rows = [
        eval_meta(e, c, d)
        for c in CALIBRATION_CURRENT
        for d in CALIBRATION_DELTA
    ]
    return json.dumps(rows, separators=(",", ":"))


class MetaSynthesizer:
    """Exact-cost enumeration quotient-collapsed by frozen calibration behavior."""
    def __init__(self, max_cost: int):
        self.max_cost = int(max_cost)
        self.levels: Dict[int, Dict[str, MetaExpr]] = {}
        self.best_cost: Dict[str, int] = {}
        self._build()

    def _admit(self, cost: int, e: MetaExpr) -> None:
        if e.cost != cost:
            return
        k = behavior_key(e)
        if k in self.best_cost:
            return
        self.best_cost[k] = cost
        self.levels.setdefault(cost, {})[k] = e

    def exact(self, cost: int) -> Tuple[MetaExpr, ...]:
        d = self.levels.get(cost, {})
        return tuple(d[k] for k in sorted(d))

    def _build(self) -> None:
        if self.max_cost >= 1:
            self._admit(1, CURRENT())
            self._admit(1, DELTA())
            self._admit(1, ONE())

        for cost in range(2, self.max_cost + 1):
            for a in self.exact(cost - 1):
                self._admit(cost, SUCC(a))

            for ca in range(1, cost - 1):
                cb = cost - 1 - ca
                if cb < 1:
                    continue
                for a in self.exact(ca):
                    for b in self.exact(cb):
                        self._admit(cost, ADD(a, b))

    def programs(self) -> Tuple[MetaExpr, ...]:
        out: List[MetaExpr] = []
        for c in range(1, self.max_cost + 1):
            out.extend(self.exact(c))
        return tuple(out)
