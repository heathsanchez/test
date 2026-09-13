#!/usr/bin/env python3
"""Frozen V7 proto-semantic candidate basis.

The candidate universe is deliberately small:
    BIT seed, PRODUCT, QUOTIENT, RELATION, COMPOSE.

Compilation/reification and external verification are handled by the
developmental kernel, not counted as proto-semantic primitives.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


PRIMITIVES = ("PRODUCT", "QUOTIENT", "RELATION", "COMPOSE")


@dataclass(frozen=True)
class BasisConfig:
    product: bool
    quotient: bool
    relation: bool
    compose: bool

    @classmethod
    def from_names(cls, names: Iterable[str]) -> "BasisConfig":
        s = set(names)
        return cls(
            product="PRODUCT" in s,
            quotient="QUOTIENT" in s,
            relation="RELATION" in s,
            compose="COMPOSE" in s,
        )

    def names(self) -> Tuple[str, ...]:
        out = []
        if self.product:
            out.append("PRODUCT")
        if self.quotient:
            out.append("QUOTIENT")
        if self.relation:
            out.append("RELATION")
        if self.compose:
            out.append("COMPOSE")
        return tuple(out)

    def data(self) -> Any:
        return list(self.names())


def all_basis_subsets() -> Tuple[BasisConfig, ...]:
    out = []
    for mask in range(1 << len(PRIMITIVES)):
        names = [
            PRIMITIVES[i]
            for i in range(len(PRIMITIVES))
            if mask & (1 << i)
        ]
        out.append(BasisConfig.from_names(names))
    out.sort(key=lambda b: (len(b.names()), b.names()))
    return tuple(out)


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


def canon(x: Any) -> Any:
    if isinstance(x, tuple):
        return [canon(y) for y in x]
    return x


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


BIT = Carrier(
    carrier_id="bit",
    elements=(False, True),
    provenance=("seed_binary_distinction",),
)


def product_carrier(a: Carrier, b: Carrier) -> Carrier:
    elems = tuple((x, y) for x in a.elements for y in b.elements)
    cid = "p_" + digest_json({
        "a": a.carrier_id,
        "b": b.carrier_id,
        "elements": [canon(x) for x in elems],
    })[:16]
    return Carrier(
        cid,
        elems,
        provenance=("PRODUCT", a.carrier_id, b.carrier_id),
    )


@dataclass(frozen=True)
class QuotientResult:
    source: Carrier
    quotient: Carrier
    class_of: Tuple[int, ...]

    def data(self) -> Any:
        return {
            "source": self.source.data(),
            "quotient": self.quotient.data(),
            "class_of": list(self.class_of),
        }


def canonical_quotient(source: Carrier, classes: int) -> QuotientResult:
    """Canonical surjective quotient onto a declared number of classes.

    The partition is generic rather than semantically canonical. External
    authority decides whether the resulting distinction regime is warranted.
    """
    classes = int(classes)
    if not (1 <= classes <= source.size):
        raise ValueError("invalid quotient class count")

    if classes == 1:
        class_of = tuple(0 for _ in source.elements)
    else:
        class_of = tuple(
            i if i < classes - 1 else classes - 1
            for i in range(source.size)
        )

    q_elems = tuple(("q", source.carrier_id, i) for i in range(classes))
    qid = "q_" + digest_json({
        "source": source.carrier_id,
        "class_of": list(class_of),
    })[:16]
    q = Carrier(
        qid,
        q_elems,
        provenance=("QUOTIENT", source.carrier_id, str(classes)),
    )
    return QuotientResult(source, q, class_of)


@dataclass(frozen=True)
class FunctionalRelation:
    domain: Carrier
    codomain: Carrier
    outputs: Tuple[int, ...]
    provenance: Tuple[str, ...] = ()
    atom_id: Optional[str] = None

    def __post_init__(self) -> None:
        if len(self.outputs) != self.domain.size:
            raise ValueError("function table length mismatch")
        if any(type(i) is not int or not (0 <= i < self.codomain.size) for i in self.outputs):
            raise ValueError("invalid codomain index")

    @property
    def direct_cost(self) -> int:
        return 1 + self.domain.size

    def run(self, x: Any) -> Any:
        try:
            i = self.domain.elements.index(x)
        except ValueError:
            raise ValueError("input outside relation domain")
        return self.codomain.elements[self.outputs[i]]

    def behavior_key(self) -> str:
        return json.dumps(list(self.outputs), separators=(",", ":"))

    def digest(self) -> str:
        return digest_json({
            "domain": self.domain.carrier_id,
            "codomain": self.codomain.carrier_id,
            "outputs": list(self.outputs),
        })

    def data(self) -> Any:
        return {
            "domain": self.domain.carrier_id,
            "codomain": self.codomain.carrier_id,
            "outputs": list(self.outputs),
            "provenance": list(self.provenance),
            "atom_id": self.atom_id,
        }


def enumerate_functional_relations(
    domain: Carrier,
    codomain: Carrier,
) -> Iterator[FunctionalRelation]:
    for outputs in itertools.product(range(codomain.size), repeat=domain.size):
        yield FunctionalRelation(
            domain,
            codomain,
            tuple(int(i) for i in outputs),
            provenance=("RELATION",),
        )


def compose_relations(
    first: FunctionalRelation,
    second: FunctionalRelation,
) -> FunctionalRelation:
    if first.codomain.carrier_id != second.domain.carrier_id:
        raise TypeError("relation composition type mismatch")
    outputs = tuple(second.outputs[i] for i in first.outputs)
    return FunctionalRelation(
        first.domain,
        second.codomain,
        outputs,
        provenance=(
            "COMPOSE",
            first.atom_id or first.digest(),
            second.atom_id or second.digest(),
        ),
    )


def relation_atom_id(r: FunctionalRelation) -> str:
    return "r_" + r.digest()[:16]


@dataclass(frozen=True)
class CarrierRecipe:
    op: str
    args: Tuple["CarrierRecipe", ...] = ()
    quotient_classes: Optional[int] = None
    recipe_atom_id: Optional[str] = None

    @property
    def cost(self) -> int:
        return 1 + sum(a.cost for a in self.args)

    def to_data(self) -> Any:
        return {
            "op": self.op,
            "args": [a.to_data() for a in self.args],
            "quotient_classes": self.quotient_classes,
            "recipe_atom_id": self.recipe_atom_id,
        }

    def serial(self) -> str:
        return json.dumps(self.to_data(), sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return hashlib.sha256(self.serial().encode()).hexdigest()


def RBASE() -> CarrierRecipe:
    return CarrierRecipe("base")


def RBIT() -> CarrierRecipe:
    return CarrierRecipe("bit")


def RPROD(a: CarrierRecipe, b: CarrierRecipe) -> CarrierRecipe:
    return CarrierRecipe("product", (a, b))


def RQUOT(a: CarrierRecipe, classes: int) -> CarrierRecipe:
    return CarrierRecipe("quotient", (a,), quotient_classes=int(classes))


def RATOM(atom_id: str) -> CarrierRecipe:
    return CarrierRecipe("recipe_atom", recipe_atom_id=atom_id)
