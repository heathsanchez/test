#!/usr/bin/env python3
"""Frozen V8 finite relation substrate.

Object-level semantic seed:
    BIT

Candidate proto-semantic primitives:
    RELATION
    COMPOSE

There is deliberately no PRODUCT carrier constructor and no QUOTIENT
carrier constructor.  Carrier growth happens only through verified
relational reification in the developmental kernel.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from typing import Any, Dict, FrozenSet, Iterable, Iterator, List, Optional, Sequence, Tuple


PRIMITIVES = ("RELATION", "COMPOSE")


@dataclass(frozen=True)
class BasisConfig:
    relation: bool
    compose: bool

    @classmethod
    def from_names(cls, names: Iterable[str]) -> "BasisConfig":
        s = set(names)
        return cls(
            relation="RELATION" in s,
            compose="COMPOSE" in s,
        )

    def names(self) -> Tuple[str, ...]:
        out: List[str] = []
        if self.relation:
            out.append("RELATION")
        if self.compose:
            out.append("COMPOSE")
        return tuple(out)

    def data(self) -> Any:
        return list(self.names())


def all_basis_subsets() -> Tuple[BasisConfig, ...]:
    out: List[BasisConfig] = []
    for mask in range(1 << len(PRIMITIVES)):
        names = [
            PRIMITIVES[i]
            for i in range(len(PRIMITIVES))
            if mask & (1 << i)
        ]
        out.append(BasisConfig.from_names(names))
    out.sort(key=lambda b: (len(b.names()), b.names()))
    return tuple(out)


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
    provenance: Tuple[str, ...] = ()

    @property
    def size(self) -> int:
        return len(self.elements)

    def data(self) -> Any:
        return {
            "carrier_id": self.carrier_id,
            "size": self.size,
            "elements": [canon(x) for x in self.elements],
            "provenance": list(self.provenance),
        }


BIT = Carrier(
    carrier_id="bit",
    elements=(False, True),
    provenance=("seed_binary_distinction",),
)


@dataclass(frozen=True)
class Relation:
    domain: Carrier
    codomain: Carrier
    edges: FrozenSet[Tuple[int, int]]
    provenance: Tuple[str, ...] = ()
    atom_id: Optional[str] = None

    def __post_init__(self) -> None:
        for i, j in self.edges:
            if not (0 <= i < self.domain.size and 0 <= j < self.codomain.size):
                raise ValueError("relation edge outside typed carrier")

    @property
    def direct_cost(self) -> int:
        # Extensional incidence table: one constructor plus one bit per cell.
        return 1 + self.domain.size * self.codomain.size

    def contains_indices(self, i: int, j: int) -> bool:
        return (int(i), int(j)) in self.edges

    def pairs(self) -> Tuple[Tuple[Any, Any], ...]:
        return tuple(
            (self.domain.elements[i], self.codomain.elements[j])
            for i, j in sorted(self.edges)
        )

    def behavior_key(self) -> str:
        return json.dumps(
            [[i, j] for i, j in sorted(self.edges)],
            separators=(",", ":"),
        )

    def digest(self) -> str:
        return digest_json({
            "domain": self.domain.carrier_id,
            "codomain": self.codomain.carrier_id,
            "edges": [[i, j] for i, j in sorted(self.edges)],
        })

    def data(self) -> Any:
        return {
            "domain": self.domain.carrier_id,
            "codomain": self.codomain.carrier_id,
            "edges": [[i, j] for i, j in sorted(self.edges)],
            "provenance": list(self.provenance),
            "atom_id": self.atom_id,
        }

    def is_total_relation(self) -> bool:
        return len(self.edges) == self.domain.size * self.codomain.size

    def is_function(self) -> bool:
        for i in range(self.domain.size):
            js = [j for ii, j in self.edges if ii == i]
            if len(js) != 1:
                return False
        return True

    def function_outputs(self) -> Tuple[int, ...]:
        if not self.is_function():
            raise ValueError("relation is not a total function")
        out = []
        for i in range(self.domain.size):
            out.append(next(j for ii, j in self.edges if ii == i))
        return tuple(out)

    def run(self, x: Any) -> Any:
        if not self.is_function():
            raise ValueError("relation is not executable as a function")
        try:
            i = self.domain.elements.index(x)
        except ValueError:
            raise ValueError("input outside domain")
        j = self.function_outputs()[i]
        return self.codomain.elements[j]


def relation_from_function_outputs(
    domain: Carrier,
    codomain: Carrier,
    outputs: Sequence[int],
    provenance: Sequence[str] = ("RELATION",),
    atom_id: Optional[str] = None,
) -> Relation:
    outs = tuple(int(x) for x in outputs)
    if len(outs) != domain.size:
        raise ValueError("wrong function table length")
    edges = frozenset((i, j) for i, j in enumerate(outs))
    return Relation(
        domain,
        codomain,
        edges,
        tuple(provenance),
        atom_id=atom_id,
    )


def total_relation(a: Carrier, b: Carrier) -> Relation:
    return Relation(
        a,
        b,
        frozenset(
            (i, j)
            for i in range(a.size)
            for j in range(b.size)
        ),
        provenance=("RELATION", "TOTAL"),
    )


def enumerate_relations(
    domain: Carrier,
    codomain: Carrier,
) -> Iterator[Relation]:
    cells = [
        (i, j)
        for i in range(domain.size)
        for j in range(codomain.size)
    ]
    for mask in range(1 << len(cells)):
        edges = frozenset(
            cells[k]
            for k in range(len(cells))
            if mask & (1 << k)
        )
        yield Relation(
            domain,
            codomain,
            edges,
            provenance=("RELATION",),
        )


def enumerate_functions(
    domain: Carrier,
    codomain: Carrier,
) -> Iterator[Relation]:
    for outputs in itertools.product(
        range(codomain.size),
        repeat=domain.size,
    ):
        yield relation_from_function_outputs(
            domain,
            codomain,
            outputs,
        )


def compose_relations(first: Relation, second: Relation) -> Relation:
    if first.codomain.carrier_id != second.domain.carrier_id:
        raise TypeError("typed relational composition mismatch")

    edges = set()
    by_mid: Dict[int, List[int]] = {}
    for j, k in second.edges:
        by_mid.setdefault(j, []).append(k)

    for i, j in first.edges:
        for k in by_mid.get(j, []):
            edges.add((i, k))

    return Relation(
        first.domain,
        second.codomain,
        frozenset(edges),
        provenance=(
            "COMPOSE",
            first.atom_id or first.digest(),
            second.atom_id or second.digest(),
        ),
    )


def relation_atom_id(r: Relation) -> str:
    return "r_" + r.digest()[:16]


def is_equivalence_relation(r: Relation) -> bool:
    if r.domain.carrier_id != r.codomain.carrier_id:
        return False
    n = r.domain.size

    for i in range(n):
        if (i, i) not in r.edges:
            return False

    for i, j in r.edges:
        if (j, i) not in r.edges:
            return False

    for i, j in r.edges:
        for jj, k in r.edges:
            if j == jj and (i, k) not in r.edges:
                return False

    return True


def equivalence_classes(r: Relation) -> Tuple[Tuple[int, ...], ...]:
    if not is_equivalence_relation(r):
        raise ValueError("relation is not an equivalence relation")

    unseen = set(range(r.domain.size))
    classes: List[Tuple[int, ...]] = []
    while unseen:
        i = min(unseen)
        cls = tuple(
            j for j in range(r.domain.size)
            if (i, j) in r.edges
        )
        classes.append(cls)
        unseen.difference_update(cls)
    return tuple(classes)
