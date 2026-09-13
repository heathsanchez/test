#!/usr/bin/env python3
"""Frozen typed generative basis B2.

The frozen object is deliberately below any one task language.  It provides
type constructors, operator atoms, generic language formation, typed
evaluation, and complete finite behavioral quotient synthesis up to a declared
cost bound.

A language is data: (input_type, output_type, admitted Boolean operators).
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple


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


def type_universe(max_depth: int) -> Tuple[Ty, ...]:
    if max_depth < 0:
        return tuple()
    by_depth: List[set[Ty]] = [set() for _ in range(max_depth + 1)]
    by_depth[0].add(BOOL)
    all_seen = {BOOL}
    for d in range(1, max_depth + 1):
        prior = sorted(all_seen, key=str)
        for a in prior:
            for b in prior:
                t = PROD(a, b)
                # exact constructor depth
                if 1 + max(type_depth(a), type_depth(b)) == d:
                    by_depth[d].add(t)
                    all_seen.add(t)
    return tuple(sorted(all_seen, key=lambda t: (type_depth(t), t.size(), str(t))))


def type_depth(ty: Ty) -> int:
    if not ty.args:
        return 0
    return 1 + max(type_depth(a) for a in ty.args)


BOOL_OPS = frozenset({"not", "and", "or", "xor", "if"})


@dataclass(frozen=True)
class Language:
    input_ty: Ty
    output_ty: Ty
    ops: frozenset[str]

    def __post_init__(self) -> None:
        bad = set(self.ops) - set(BOOL_OPS)
        if bad:
            raise ValueError(f"unknown ops: {sorted(bad)}")

    def data(self) -> Any:
        return {
            "input": self.input_ty.data(),
            "output": self.output_ty.data(),
            "ops": sorted(self.ops),
        }

    def digest(self) -> str:
        raw = json.dumps(self.data(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def complexity(self) -> int:
        return self.input_ty.size() + self.output_ty.size() + len(self.ops)


@dataclass(frozen=True)
class Expr:
    op: str
    ty: Ty
    args: Tuple["Expr", ...] = ()
    data: Any = None

    @property
    def cost(self) -> int:
        return 1 + sum(a.cost for a in self.args)

    def serial(self) -> str:
        return json.dumps(self.to_data(), sort_keys=True, separators=(",", ":"))

    def to_data(self) -> Any:
        return {
            "op": self.op,
            "ty": self.ty.data(),
            "args": [a.to_data() for a in self.args],
            "data": self.data,
        }


@dataclass(frozen=True)
class Program:
    language: Language
    body: Expr

    def __post_init__(self) -> None:
        if self.body.ty != self.language.output_ty:
            raise TypeError("body/output mismatch")

    @property
    def cost(self) -> int:
        return self.body.cost

    def run(self, x: Any) -> Any:
        check(self.language.input_ty, x)
        out = eval_expr(self.body, x)
        check(self.language.output_ty, out)
        return out

    def behavior(self) -> Tuple[Any, ...]:
        return tuple(canon_value(self.run(x)) for x in values(self.language.input_ty))

    def behavior_key(self) -> str:
        return json.dumps(self.behavior(), sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        payload = {
            "language": self.language.data(),
            "body": self.body.to_data(),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def canon_value(x: Any) -> Any:
    if isinstance(x, tuple):
        return [canon_value(y) for y in x]
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


def Var(input_ty: Ty) -> Expr:
    return Expr("var", input_ty)


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
    if op not in {"and", "or", "xor"} or a.ty != BOOL or b.ty != BOOL:
        raise TypeError(op)
    return Expr(op, BOOL, (a, b))


def If(c: Expr, a: Expr, b: Expr) -> Expr:
    if c.ty != BOOL or a.ty != b.ty:
        raise TypeError("if")
    return Expr("if", a.ty, (c, a, b))


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
    if e.op == "xor":
        return bool(eval_expr(e.args[0], inp) ^ eval_expr(e.args[1], inp))
    if e.op == "if":
        return eval_expr(e.args[1], inp) if eval_expr(e.args[0], inp) else eval_expr(e.args[2], inp)
    raise ValueError(e.op)


def expr_behavior(expr: Expr, input_ty: Ty) -> str:
    rows = [canon_value(eval_expr(expr, x)) for x in values(input_ty)]
    return json.dumps(rows, sort_keys=True, separators=(",", ":"))


class Synthesizer:
    """Minimal-cost, behavior-quotiented synthesizer for one constructed language.

    Structural product operations (pair/fst/snd) belong to the frozen basis.
    Boolean semantic atoms are selected by Language.ops.
    """

    def __init__(self, language: Language, max_cost: int):
        self.lang = language
        self.max_cost = int(max_cost)
        self.levels: Dict[int, Dict[Ty, Dict[str, Expr]]] = {}
        self.best_cost: Dict[Tuple[Ty, str], int] = {}
        self._build()

    def _admit(self, cost: int, e: Expr) -> None:
        if e.cost != cost:
            return
        k = expr_behavior(e, self.lang.input_ty)
        bk = (e.ty, k)
        if bk in self.best_cost:
            return
        self.best_cost[bk] = cost
        self.levels.setdefault(cost, {}).setdefault(e.ty, {})[k] = e

    def _exprs(self, cost: int, ty: Ty) -> Tuple[Expr, ...]:
        d = self.levels.get(cost, {}).get(ty, {})
        return tuple(d[k] for k in sorted(d))

    def _known_types(self) -> Tuple[Ty, ...]:
        ts = {self.lang.input_ty, self.lang.output_ty, BOOL}
        def add_parts(t: Ty) -> None:
            ts.add(t)
            for a in t.args:
                add_parts(a)
        add_parts(self.lang.input_ty)
        add_parts(self.lang.output_ty)
        # Products of relevant component types may be required for output construction.
        base = list(ts)
        for a in base:
            for b in base:
                p = PROD(a, b)
                if p.size() <= max(self.lang.input_ty.size(), self.lang.output_ty.size(), 3):
                    ts.add(p)
        return tuple(sorted(ts, key=lambda t: (t.size(), str(t))))

    def _build(self) -> None:
        # Cost 1 atoms.
        self._admit(1, Var(self.lang.input_ty))
        self._admit(1, B(False))
        self._admit(1, B(True))

        tys = self._known_types()

        for cost in range(2, self.max_cost + 1):
            # Structural projections.
            for source_ty in tys:
                if source_ty.tag != "Prod":
                    continue
                for src in self._exprs(cost - 1, source_ty):
                    self._admit(cost, Fst(src))
                    self._admit(cost, Snd(src))

            # NOT.
            if "not" in self.lang.ops:
                for a in self._exprs(cost - 1, BOOL):
                    self._admit(cost, Not(a))

            # Binary Boolean ops and structural pair.
            for ca in range(1, cost - 1):
                cb = cost - 1 - ca
                if cb < 1:
                    continue

                for op in ("and", "or", "xor"):
                    if op not in self.lang.ops:
                        continue
                    for a in self._exprs(ca, BOOL):
                        for b in self._exprs(cb, BOOL):
                            self._admit(cost, Bin(op, a, b))

                for ta in tys:
                    for tb in tys:
                        target = PROD(ta, tb)
                        if target not in tys:
                            continue
                        for a in self._exprs(ca, ta):
                            for b in self._exprs(cb, tb):
                                self._admit(cost, Pair(a, b))

            # IF.
            if "if" in self.lang.ops:
                for cc in range(1, cost - 2):
                    for ca in range(1, cost - 1 - cc):
                        cb = cost - 1 - cc - ca
                        if cb < 1:
                            continue
                        for t in tys:
                            for c in self._exprs(cc, BOOL):
                                for a in self._exprs(ca, t):
                                    for b in self._exprs(cb, t):
                                        self._admit(cost, If(c, a, b))

    def programs(self) -> Tuple[Program, ...]:
        out: List[Program] = []
        for cost in range(1, self.max_cost + 1):
            for e in self._exprs(cost, self.lang.output_ty):
                out.append(Program(self.lang, e))
        return tuple(out)


def language_distance(a: Language, b: Language) -> int:
    return (
        (0 if a.input_ty == b.input_ty else 1)
        + (0 if a.output_ty == b.output_ty else 1)
        + len(a.ops.symmetric_difference(b.ops))
    )


def enumerate_languages(
    current: Language,
    max_type_depth: int,
    max_edit_cost: int,
) -> Tuple[Language, ...]:
    tys = type_universe(max_type_depth)
    ops = sorted(BOOL_OPS)
    out: List[Language] = []
    # All subsets are finite: 2^5 = 32.
    for input_ty in tys:
        for output_ty in tys:
            for mask in range(1 << len(ops)):
                chosen = frozenset(ops[i] for i in range(len(ops)) if mask & (1 << i))
                lang = Language(input_ty, output_ty, chosen)
                if language_distance(current, lang) <= max_edit_cost:
                    out.append(lang)
    out.sort(key=lambda l: (language_distance(current, l), l.complexity(), l.digest()))
    return tuple(out)
