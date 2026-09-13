#!/usr/bin/env python3
"""Frozen V3 basis: typed finite programs + anonymous promoted macro atoms.

There is deliberately NO XOR primitive.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


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


def canon(x: Any) -> Any:
    if isinstance(x, tuple):
        return [canon(y) for y in x]
    return x


def check(ty: Ty, x: Any) -> None:
    if ty == BOOL:
        if type(x) is not bool:
            raise TypeError((ty, x))
        return
    if ty.tag == "Prod":
        if not isinstance(x, tuple) or len(x) != 2:
            raise TypeError((ty, x))
        check(ty.args[0], x[0])
        check(ty.args[1], x[1])
        return
    raise TypeError(ty)


PRIMITIVE_OPS = frozenset({"not", "and", "or", "if"})


@dataclass(frozen=True)
class MacroAtom:
    macro_id: str
    input_ty: Ty
    output_ty: Ty
    table: Tuple[Any, ...]
    provenance: Tuple[str, ...]
    source_program_digests: Tuple[str, ...]
    full_replay: bool
    warrant_digests: Tuple[str, ...]

    def data(self) -> Any:
        return {
            "macro_id": self.macro_id,
            "input": self.input_ty.data(),
            "output": self.output_ty.data(),
            "table": [canon(x) for x in self.table],
            "provenance": list(self.provenance),
            "source_program_digests": list(self.source_program_digests),
            "full_replay": self.full_replay,
            "warrant_digests": list(self.warrant_digests),
        }


@dataclass(frozen=True)
class Expr:
    op: str
    ty: Ty
    args: Tuple["Expr", ...] = ()
    data: Any = None

    @property
    def cost(self) -> int:
        return 1 + sum(a.cost for a in self.args)

    def to_data(self) -> Any:
        d = self.data
        if isinstance(d, MacroAtom):
            d = {"macro_id": d.macro_id}
        return {
            "op": self.op,
            "ty": self.ty.data(),
            "args": [a.to_data() for a in self.args],
            "data": d,
        }

    def serial(self) -> str:
        return json.dumps(self.to_data(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class Program:
    input_ty: Ty
    output_ty: Ty
    body: Expr

    def __post_init__(self) -> None:
        if self.body.ty != self.output_ty:
            raise TypeError("program output mismatch")

    @property
    def cost(self) -> int:
        return self.body.cost

    def run(self, x: Any) -> Any:
        check(self.input_ty, x)
        out = eval_expr(self.body, x)
        check(self.output_ty, out)
        return out

    def behavior(self) -> Tuple[Any, ...]:
        return tuple(self.run(x) for x in values(self.input_ty))

    def behavior_key(self) -> str:
        return json.dumps([canon(x) for x in self.behavior()], sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        payload = {
            "input": self.input_ty.data(),
            "output": self.output_ty.data(),
            "body": self.body.to_data(),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def Var(ty: Ty) -> Expr:
    return Expr("var", ty)


def B(v: bool) -> Expr:
    return Expr("bool", BOOL, data=bool(v))


def Fst(e: Expr) -> Expr:
    if e.ty.tag != "Prod":
        raise TypeError("fst")
    return Expr("fst", e.ty.args[0], (e,))


def Snd(e: Expr) -> Expr:
    if e.ty.tag != "Prod":
        raise TypeError("snd")
    return Expr("snd", e.ty.args[1], (e,))


def Pair(a: Expr, b: Expr) -> Expr:
    return Expr("pair", PROD(a.ty, b.ty), (a, b))


def Not(a: Expr) -> Expr:
    if a.ty != BOOL:
        raise TypeError("not")
    return Expr("not", BOOL, (a,))


def Bin(op: str, a: Expr, b: Expr) -> Expr:
    if op not in {"and", "or"}:
        raise ValueError(op)
    if a.ty != BOOL or b.ty != BOOL:
        raise TypeError(op)
    return Expr(op, BOOL, (a, b))


def If(c: Expr, a: Expr, b: Expr) -> Expr:
    if c.ty != BOOL or a.ty != b.ty:
        raise TypeError("if")
    return Expr("if", a.ty, (c, a, b))


def MacroCall(atom: MacroAtom, arg: Expr) -> Expr:
    if arg.ty != atom.input_ty:
        raise TypeError("macro input mismatch")
    return Expr("macro", atom.output_ty, (arg,), data=atom)


def eval_expr(e: Expr, inp: Any) -> Any:
    if e.op == "var":
        return inp
    if e.op == "bool":
        return bool(e.data)
    if e.op == "fst":
        return eval_expr(e.args[0], inp)[0]
    if e.op == "snd":
        return eval_expr(e.args[0], inp)[1]
    if e.op == "pair":
        return (eval_expr(e.args[0], inp), eval_expr(e.args[1], inp))
    if e.op == "not":
        return not eval_expr(e.args[0], inp)
    if e.op == "and":
        return bool(eval_expr(e.args[0], inp) and eval_expr(e.args[1], inp))
    if e.op == "or":
        return bool(eval_expr(e.args[0], inp) or eval_expr(e.args[1], inp))
    if e.op == "if":
        return eval_expr(e.args[1], inp) if eval_expr(e.args[0], inp) else eval_expr(e.args[2], inp)
    if e.op == "macro":
        atom = e.data
        if not isinstance(atom, MacroAtom):
            raise TypeError("malformed macro")
        arg = eval_expr(e.args[0], inp)
        xs = values(atom.input_ty)
        for i, x in enumerate(xs):
            if x == arg:
                return atom.table[i]
        raise ValueError("macro input outside finite domain")
    raise ValueError(e.op)


def expr_behavior(e: Expr, input_ty: Ty) -> str:
    return json.dumps(
        [canon(eval_expr(e, x)) for x in values(input_ty)],
        sort_keys=True,
        separators=(",", ":"),
    )


def relevant_types(input_ty: Ty, output_ty: Ty) -> Tuple[Ty, ...]:
    out = {BOOL, input_ty, output_ty}
    def add(t: Ty) -> None:
        out.add(t)
        for a in t.args:
            add(a)
    add(input_ty)
    add(output_ty)
    # Pair construction is useful for finite-state/output tasks.
    base = list(out)
    for a in base:
        for b in base:
            p = PROD(a, b)
            if p.size() <= max(input_ty.size(), output_ty.size(), 3):
                out.add(p)
    return tuple(sorted(out, key=lambda t: (t.size(), str(t))))


class Synthesizer:
    """Exact bounded AST-cost synthesis, quotienting each type by behavior."""
    def __init__(
        self,
        input_ty: Ty,
        output_ty: Ty,
        max_cost: int,
        vocabulary: Sequence[MacroAtom] = (),
    ):
        self.input_ty = input_ty
        self.output_ty = output_ty
        self.max_cost = int(max_cost)
        self.vocabulary = tuple(vocabulary)
        self.levels: Dict[int, Dict[Ty, Dict[str, Expr]]] = {}
        self.best_cost: Dict[Tuple[Ty, str], int] = {}
        self._build()

    def _admit(self, cost: int, e: Expr) -> None:
        if e.cost != cost:
            return
        k = expr_behavior(e, self.input_ty)
        bk = (e.ty, k)
        if bk in self.best_cost:
            return
        self.best_cost[bk] = cost
        self.levels.setdefault(cost, {}).setdefault(e.ty, {})[k] = e

    def _exprs(self, cost: int, ty: Ty) -> Tuple[Expr, ...]:
        d = self.levels.get(cost, {}).get(ty, {})
        return tuple(d[k] for k in sorted(d))

    def _all_known(self, ty: Ty, max_cost: int) -> Tuple[Expr, ...]:
        xs: List[Expr] = []
        for c in range(1, max_cost + 1):
            xs.extend(self._exprs(c, ty))
        return tuple(xs)

    def _build(self) -> None:
        tys = relevant_types(self.input_ty, self.output_ty)

        self._admit(1, Var(self.input_ty))
        self._admit(1, B(False))
        self._admit(1, B(True))

        for cost in range(2, self.max_cost + 1):
            # Structural projections.
            for t in tys:
                if t.tag != "Prod":
                    continue
                for src in self._exprs(cost - 1, t):
                    self._admit(cost, Fst(src))
                    self._admit(cost, Snd(src))

            # Primitive NOT.
            for a in self._exprs(cost - 1, BOOL):
                self._admit(cost, Not(a))

            # Generic promoted macros.
            for atom in self.vocabulary:
                for arg in self._exprs(cost - 1, atom.input_ty):
                    self._admit(cost, MacroCall(atom, arg))

            # Binary primitives and pair.
            for ca in range(1, cost - 1):
                cb = cost - 1 - ca
                if cb < 1:
                    continue
                for a in self._exprs(ca, BOOL):
                    for b in self._exprs(cb, BOOL):
                        self._admit(cost, Bin("and", a, b))
                        self._admit(cost, Bin("or", a, b))
                for ta in tys:
                    for tb in tys:
                        target = PROD(ta, tb)
                        if target not in tys:
                            continue
                        for a in self._exprs(ca, ta):
                            for b in self._exprs(cb, tb):
                                self._admit(cost, Pair(a, b))

            # IF over any known type.
            for cc in range(1, cost - 2):
                for ca in range(1, cost - 1 - cc):
                    cb = cost - 1 - cc - ca
                    if cb < 1:
                        continue
                    for c in self._exprs(cc, BOOL):
                        for t in tys:
                            for a in self._exprs(ca, t):
                                for b in self._exprs(cb, t):
                                    self._admit(cost, If(c, a, b))

    def programs(self) -> Tuple[Program, ...]:
        out: List[Program] = []
        for c in range(1, self.max_cost + 1):
            for e in self._exprs(c, self.output_ty):
                out.append(Program(self.input_ty, self.output_ty, e))
        return tuple(out)

    def minimum_program_for_behavior(self, table: Sequence[Any]) -> Optional[Program]:
        target = json.dumps([canon(x) for x in table], sort_keys=True, separators=(",", ":"))
        for p in self.programs():
            if p.behavior_key() == target:
                return p
        return None


def macro_id(input_ty: Ty, output_ty: Ty, table: Sequence[Any]) -> str:
    payload = {
        "input": input_ty.data(),
        "output": output_ty.data(),
        "table": [canon(x) for x in table],
    }
    h = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return "m_" + h[:16]


def contains_macro(e: Expr, macro_id_value: Optional[str] = None) -> bool:
    if e.op == "macro":
        atom = e.data
        return macro_id_value is None or (
            isinstance(atom, MacroAtom) and atom.macro_id == macro_id_value
        )
    return any(contains_macro(a, macro_id_value) for a in e.args)
