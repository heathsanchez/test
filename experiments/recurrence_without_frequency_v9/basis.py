#!/usr/bin/env python3
"""Frozen V9 finite temporal relation substrate.

There are deliberately no semantic primitives named period, cycle, phase,
frequency, oscillator, clock, or iterate.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class BasisConfig:
    compose: bool = True

    def data(self):
        return {"COMPOSE": self.compose}


def canon(x: Any) -> Any:
    if isinstance(x, tuple):
        return [canon(y) for y in x]
    return x


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


@dataclass(frozen=True)
class Carrier:
    carrier_id: str
    elements: Tuple[Any, ...]

    @property
    def size(self) -> int:
        return len(self.elements)

    def data(self):
        return {
            "carrier_id": self.carrier_id,
            "size": self.size,
            "elements": [canon(x) for x in self.elements],
        }


def finite_carrier(name: str, n: int) -> Carrier:
    if int(n) <= 0:
        raise ValueError("carrier size must be positive")
    return Carrier(
        carrier_id=str(name),
        elements=tuple((str(name), i) for i in range(int(n))),
    )


BIT = Carrier("bit", (False, True))


@dataclass(frozen=True)
class FunctionRelation:
    domain: Carrier
    codomain: Carrier
    outputs: Tuple[int, ...]
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.outputs) != self.domain.size:
            raise ValueError("function table length mismatch")
        if any(
            type(j) is not int or not (0 <= j < self.codomain.size)
            for j in self.outputs
        ):
            raise ValueError("output index outside codomain")

    def run_index(self, i: int) -> int:
        return self.outputs[int(i)]

    def run(self, x: Any) -> Any:
        try:
            i = self.domain.elements.index(x)
        except ValueError:
            raise ValueError("input outside domain")
        return self.codomain.elements[self.outputs[i]]

    def data(self):
        return {
            "domain": self.domain.carrier_id,
            "codomain": self.codomain.carrier_id,
            "outputs": list(self.outputs),
            "provenance": list(self.provenance),
        }

    def digest(self) -> str:
        return digest_json(self.data())

    def is_bijection(self) -> bool:
        return (
            self.domain.size == self.codomain.size
            and sorted(self.outputs) == list(range(self.codomain.size))
        )


def identity_relation(carrier: Carrier) -> FunctionRelation:
    return FunctionRelation(
        carrier,
        carrier,
        tuple(range(carrier.size)),
        provenance=("IDENTITY",),
    )


def compose(
    first: FunctionRelation,
    second: FunctionRelation,
) -> FunctionRelation:
    """second after first."""
    if first.codomain.carrier_id != second.domain.carrier_id:
        raise TypeError("composition type mismatch")
    outputs = tuple(second.outputs[j] for j in first.outputs)
    return FunctionRelation(
        first.domain,
        second.codomain,
        outputs,
        provenance=(
            "COMPOSE",
            first.digest(),
            second.digest(),
        ),
    )


def relation_from_outputs(
    domain: Carrier,
    codomain: Carrier,
    outputs: Sequence[int],
    provenance: Sequence[str] = ("RELATION",),
) -> FunctionRelation:
    return FunctionRelation(
        domain,
        codomain,
        tuple(int(x) for x in outputs),
        tuple(provenance),
    )


def permute_relation(
    relation: FunctionRelation,
    permutation: Sequence[int],
    new_carrier: Carrier,
) -> FunctionRelation:
    """Rename a square transition relation by a carrier permutation."""
    if relation.domain.carrier_id != relation.codomain.carrier_id:
        raise TypeError("only square relation can be renamed")
    n = relation.domain.size
    p = tuple(int(x) for x in permutation)
    if sorted(p) != list(range(n)) or new_carrier.size != n:
        raise ValueError("invalid permutation")
    inv = [0] * n
    for old, new in enumerate(p):
        inv[new] = old

    # new_index -> old_index -> old_next -> new_next
    out = []
    for new_i in range(n):
        old_i = inv[new_i]
        old_j = relation.outputs[old_i]
        out.append(p[old_j])

    return FunctionRelation(
        new_carrier,
        new_carrier,
        tuple(out),
        provenance=("RENAMED", relation.digest()),
    )


def permute_observer(
    observer: FunctionRelation,
    permutation: Sequence[int],
    new_carrier: Carrier,
) -> FunctionRelation:
    n = observer.domain.size
    p = tuple(int(x) for x in permutation)
    if sorted(p) != list(range(n)) or new_carrier.size != n:
        raise ValueError("invalid permutation")
    inv = [0] * n
    for old, new in enumerate(p):
        inv[new] = old
    outputs = tuple(observer.outputs[inv[new_i]] for new_i in range(n))
    return FunctionRelation(
        new_carrier,
        observer.codomain,
        outputs,
        provenance=("RENAMED_OBSERVER", observer.digest()),
    )
