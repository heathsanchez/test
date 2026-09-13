#!/usr/bin/env python3
"""Frozen V5 object type algebra and generic finite-carrier meta-substrate."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Ty:
    tag: str
    args: Tuple["Ty", ...] = ()
    atom_id: str = ""
    atom_size: int = 0

    def data(self) -> Any:
        if self.tag == "Atom":
            return ["Atom", self.atom_id, self.atom_size]
        return [self.tag, *[a.data() for a in self.args]]

    def __str__(self) -> str:
        if self.tag == "Atom":
            return f"Atom({self.atom_id},{self.atom_size})"
        if not self.args:
            return self.tag
        return f"{self.tag}(" + ",".join(map(str, self.args)) + ")"


BOOL = Ty("Bool")


def PROD(a: Ty, b: Ty) -> Ty:
    return Ty("Prod", (a, b))


def carrier_id(size: int) -> str:
    payload = json.dumps({"finite_carrier_size": int(size)}, sort_keys=True).encode()
    return "c_" + hashlib.sha256(payload).hexdigest()[:16]


def CARRIER(size: int) -> Ty:
    if int(size) <= 0:
        raise ValueError("carrier size must be positive")
    return Ty("Atom", (), carrier_id(size), int(size))


def cardinality(ty: Ty) -> int:
    if ty == BOOL:
        return 2
    if ty.tag == "Atom":
        return int(ty.atom_size)
    if ty.tag == "Prod":
        return cardinality(ty.args[0]) * cardinality(ty.args[1])
    raise TypeError(ty)


def values(ty: Ty) -> Tuple[Any, ...]:
    if ty == BOOL:
        return (False, True)
    if ty.tag == "Atom":
        return tuple((ty.atom_id, i) for i in range(ty.atom_size))
    if ty.tag == "Prod":
        a, b = ty.args
        return tuple((x, y) for x in values(a) for y in values(b))
    raise TypeError(ty)


def check_value(ty: Ty, value: Any) -> None:
    if ty == BOOL:
        if type(value) is not bool:
            raise TypeError((ty, value))
        return
    if ty.tag == "Atom":
        if (
            not isinstance(value, tuple)
            or len(value) != 2
            or value[0] != ty.atom_id
            or type(value[1]) is not int
            or not (0 <= value[1] < ty.atom_size)
        ):
            raise TypeError((ty, value))
        return
    if ty.tag == "Prod":
        if not isinstance(value, tuple) or len(value) != 2:
            raise TypeError((ty, value))
        check_value(ty.args[0], value[0])
        check_value(ty.args[1], value[1])
        return
    raise TypeError(ty)


def type_cost(ty: Ty) -> int:
    if ty == BOOL or ty.tag == "Atom":
        return 1
    if ty.tag == "Prod":
        return 1 + type_cost(ty.args[0]) + type_cost(ty.args[1])
    raise TypeError(ty)


@dataclass(frozen=True)
class IdentityProgram:
    ty: Ty

    def run(self, value: Any) -> Any:
        check_value(self.ty, value)
        return value

    def digest(self) -> str:
        payload = {"type": self.ty.data(), "body": "identity"}
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass(frozen=True)
class CarrierRecord:
    ty: Ty
    origin: str
    warrant_digest: str
    obstruction_certificate: Dict[str, Any]

    def data(self) -> Any:
        return {
            "type": self.ty.data(),
            "origin": self.origin,
            "warrant_digest": self.warrant_digest,
            "obstruction_certificate": self.obstruction_certificate,
        }


class TypeSynthesizer:
    """Exact bounded object-type enumeration from active ground carriers + Product."""
    def __init__(self, learned_carriers: Sequence[CarrierRecord], max_cost: int):
        self.learned_carriers = tuple(learned_carriers)
        self.max_cost = int(max_cost)
        self.levels: Dict[int, Dict[str, Ty]] = {}
        self._build()

    @staticmethod
    def _key(ty: Ty) -> str:
        return json.dumps(ty.data(), sort_keys=True, separators=(",", ":"))

    def _admit(self, cost: int, ty: Ty) -> None:
        if type_cost(ty) != cost:
            return
        self.levels.setdefault(cost, {}).setdefault(self._key(ty), ty)

    def exact(self, cost: int) -> Tuple[Ty, ...]:
        d = self.levels.get(cost, {})
        return tuple(d[k] for k in sorted(d))

    def _build(self) -> None:
        if self.max_cost >= 1:
            self._admit(1, BOOL)
            for r in self.learned_carriers:
                self._admit(1, r.ty)

        for cost in range(2, self.max_cost + 1):
            for ca in range(1, cost - 1):
                cb = cost - 1 - ca
                if cb < 1:
                    continue
                for a in self.exact(ca):
                    for b in self.exact(cb):
                        self._admit(cost, PROD(a, b))

    def types(self) -> Tuple[Ty, ...]:
        out: List[Ty] = []
        for c in range(1, self.max_cost + 1):
            out.extend(self.exact(c))
        return tuple(out)


def active_ground_cardinalities(
    learned_carriers: Sequence[CarrierRecord],
) -> Tuple[int, ...]:
    return tuple(sorted({2, *[cardinality(r.ty) for r in learned_carriers]}))


def multiplicative_closure_up_to(
    ground_sizes: Sequence[int],
    limit: int,
) -> Tuple[int, ...]:
    if limit <= 0:
        return tuple()
    gs = sorted({int(x) for x in ground_sizes if 1 < int(x) <= limit})
    reachable = set(gs)
    changed = True
    while changed:
        changed = False
        current = sorted(reachable)
        for a in current:
            for b in gs:
                p = a * b
                if p <= limit and p not in reachable:
                    reachable.add(p)
                    changed = True
    return tuple(sorted(reachable))


def can_generate_cardinality(
    target: int,
    learned_carriers: Sequence[CarrierRecord],
) -> bool:
    target = int(target)
    if target <= 1:
        return False
    grounds = active_ground_cardinalities(learned_carriers)
    return target in multiplicative_closure_up_to(grounds, target)


def obstruction_certificate(
    target: int,
    learned_carriers: Sequence[CarrierRecord],
) -> Dict[str, Any]:
    target = int(target)
    grounds = active_ground_cardinalities(learned_carriers)
    closure = multiplicative_closure_up_to(grounds, target)
    possible = target in closure
    return {
        "kind": "multiplicative_cardinality_closure",
        "target": target,
        "active_ground_cardinalities": list(grounds),
        "reachable_cardinalities_leq_target": list(closure),
        "target_reachable": possible,
        "complete": True,
        "reason": (
            "target is generated by active ground cardinalities under Product"
            if possible
            else "target is outside the complete multiplicative closure under Product"
        ),
    }
