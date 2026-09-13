#!/usr/bin/env python3
"""Frozen V4 basis: parametric type formation + anonymous learned constructors."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Concrete finite types and executable identity programs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Ty:
    tag: str
    args: Tuple["Ty", ...] = ()

    def data(self) -> Any:
        return [self.tag, *[a.data() for a in self.args]]

    def size(self) -> int:
        return 1 + sum(a.size() for a in self.args)

    def __str__(self) -> str:
        if not self.args:
            return self.tag
        return f"{self.tag}(" + ",".join(map(str, self.args)) + ")"


BOOL = Ty("Bool")


def PROD(a: Ty, b: Ty) -> Ty:
    return Ty("Prod", (a, b))


def values(ty: Ty) -> Tuple[Any, ...]:
    if ty == BOOL:
        return (False, True)
    if ty.tag == "Prod":
        a, b = ty.args
        return tuple((x, y) for x in values(a) for y in values(b))
    raise TypeError(ty)


def check_value(ty: Ty, x: Any) -> None:
    if ty == BOOL:
        if type(x) is not bool:
            raise TypeError((ty, x))
        return
    if ty.tag == "Prod":
        if not isinstance(x, tuple) or len(x) != 2:
            raise TypeError((ty, x))
        check_value(ty.args[0], x[0])
        check_value(ty.args[1], x[1])
        return
    raise TypeError(ty)


@dataclass(frozen=True)
class IdentityProgram:
    input_ty: Ty
    output_ty: Ty

    def __post_init__(self) -> None:
        if self.input_ty != self.output_ty:
            raise TypeError("V4 identity program requires equal input/output type")

    def run(self, x: Any) -> Any:
        check_value(self.input_ty, x)
        return x

    def digest(self) -> str:
        payload = {
            "input": self.input_ty.data(),
            "output": self.output_ty.data(),
            "body": "identity",
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


# ---------------------------------------------------------------------------
# Parametric type programs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TypeExpr:
    op: str
    args: Tuple["TypeExpr", ...] = ()
    macro_id: Optional[str] = None

    @property
    def cost(self) -> int:
        return 1 + sum(a.cost for a in self.args)

    def to_data(self) -> Any:
        return {
            "op": self.op,
            "args": [a.to_data() for a in self.args],
            "macro_id": self.macro_id,
        }

    def serial(self) -> str:
        return json.dumps(self.to_data(), sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return hashlib.sha256(self.serial().encode()).hexdigest()


def X() -> TypeExpr:
    return TypeExpr("var")


def TBool() -> TypeExpr:
    return TypeExpr("bool")


def TProd(a: TypeExpr, b: TypeExpr) -> TypeExpr:
    return TypeExpr("prod", (a, b))


def TMacro(macro_id: str, arg: TypeExpr) -> TypeExpr:
    return TypeExpr("macro", (arg,), macro_id=macro_id)


@dataclass(frozen=True)
class TypeMacro:
    macro_id: str
    definition: TypeExpr
    provenance: Tuple[str, ...]
    base_types: Tuple[Ty, ...]
    source_formation_digests: Tuple[str, ...]
    warrant_digests: Tuple[str, ...]
    full_symbolic_replay: bool

    def data(self) -> Any:
        return {
            "macro_id": self.macro_id,
            "definition": self.definition.to_data(),
            "provenance": list(self.provenance),
            "base_types": [t.data() for t in self.base_types],
            "source_formation_digests": list(self.source_formation_digests),
            "warrant_digests": list(self.warrant_digests),
            "full_symbolic_replay": self.full_symbolic_replay,
        }


def contains_macro(e: TypeExpr, macro_id: Optional[str] = None) -> bool:
    if e.op == "macro":
        return macro_id is None or e.macro_id == macro_id
    return any(contains_macro(a, macro_id) for a in e.args)


def substitute(expr: TypeExpr, replacement: TypeExpr) -> TypeExpr:
    if expr.op == "var":
        return replacement
    if expr.op == "bool":
        return expr
    if expr.op == "prod":
        return TProd(
            substitute(expr.args[0], replacement),
            substitute(expr.args[1], replacement),
        )
    if expr.op == "macro":
        return TypeExpr(
            "macro",
            tuple(substitute(a, replacement) for a in expr.args),
            macro_id=expr.macro_id,
        )
    raise ValueError(expr.op)


def expand_macros(expr: TypeExpr, vocabulary: Sequence[TypeMacro]) -> TypeExpr:
    table = {m.macro_id: m for m in vocabulary}
    if expr.op in {"var", "bool"}:
        return expr
    if expr.op == "prod":
        return TProd(
            expand_macros(expr.args[0], vocabulary),
            expand_macros(expr.args[1], vocabulary),
        )
    if expr.op == "macro":
        if expr.macro_id not in table:
            raise KeyError(expr.macro_id)
        atom = table[expr.macro_id]
        arg = expand_macros(expr.args[0], vocabulary)
        instantiated = substitute(atom.definition, arg)
        return expand_macros(instantiated, vocabulary)
    raise ValueError(expr.op)


def eval_type_expr(expr: TypeExpr, base: Ty, vocabulary: Sequence[TypeMacro]) -> Ty:
    expanded = expand_macros(expr, vocabulary)

    def go(e: TypeExpr) -> Ty:
        if e.op == "var":
            return base
        if e.op == "bool":
            return BOOL
        if e.op == "prod":
            return PROD(go(e.args[0]), go(e.args[1]))
        raise ValueError(f"unexpected unexpanded op {e.op}")

    return go(expanded)


def type_macro_id(definition: TypeExpr) -> str:
    payload = {"definition": definition.to_data()}
    h = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return "t_" + h[:16]


class TypeSynthesizer:
    """Exact-cost enumeration of parametric type programs.

    Primitive basis: X, Bool, Product. Learned macros are generic unary
    formation constructors and count as one constructor node plus argument.
    """

    def __init__(self, max_cost: int, vocabulary: Sequence[TypeMacro] = ()):
        self.max_cost = int(max_cost)
        self.vocabulary = tuple(vocabulary)
        self.levels: Dict[int, Dict[str, TypeExpr]] = {}
        self._build()

    def _admit(self, cost: int, e: TypeExpr) -> None:
        if e.cost != cost:
            return
        self.levels.setdefault(cost, {}).setdefault(e.serial(), e)

    def exact(self, cost: int) -> Tuple[TypeExpr, ...]:
        d = self.levels.get(cost, {})
        return tuple(d[k] for k in sorted(d))

    def _build(self) -> None:
        if self.max_cost >= 1:
            self._admit(1, X())
            self._admit(1, TBool())

        for cost in range(2, self.max_cost + 1):
            # Learned unary constructors.
            for m in self.vocabulary:
                for a in self.exact(cost - 1):
                    self._admit(cost, TMacro(m.macro_id, a))

            # Primitive Product.
            for ca in range(1, cost - 1):
                cb = cost - 1 - ca
                if cb < 1:
                    continue
                for a in self.exact(ca):
                    for b in self.exact(cb):
                        self._admit(cost, TProd(a, b))

    def programs(self) -> Tuple[TypeExpr, ...]:
        out: List[TypeExpr] = []
        for c in range(1, self.max_cost + 1):
            out.extend(self.exact(c))
        return tuple(out)
