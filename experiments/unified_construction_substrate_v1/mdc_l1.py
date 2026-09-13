#!/usr/bin/env python3
"""
MDC-L1: a deliberately small finite typed construction substrate.

Design goals
------------
* One AST and one evaluator for ordinary task programs and meta-programs.
* First-class typed Code values.
* Exact finite enumeration by syntactic cost for declared bounded searches.
* Canonical serialization/digests for independent replay and freeze checks.
* No challenge-specific repair names.

This is a V1 substrate. It is intentionally not a general-purpose language.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Ty:
    tag: str
    args: Tuple[Any, ...] = ()

    def to_data(self) -> Any:
        def enc(x: Any) -> Any:
            if isinstance(x, Ty):
                return x.to_data()
            if isinstance(x, tuple):
                return [enc(y) for y in x]
            return x
        return [self.tag, *[enc(x) for x in self.args]]

    def __str__(self) -> str:
        if not self.args:
            return self.tag
        return f"{self.tag}[" + ",".join(map(str, self.args)) + "]"


BOOL = Ty("Bool")


def FIN(n: int) -> Ty:
    if n <= 0:
        raise ValueError("Fin bound must be positive")
    return Ty("Fin", (int(n),))


def TUP(*items: Ty) -> Ty:
    return Ty("Tuple", tuple(items))


def CODE(inputs: Sequence[Ty], output: Ty) -> Ty:
    return Ty("Code", (tuple(inputs), output))


def _code_sig(ty: Ty) -> Tuple[Tuple[Ty, ...], Ty]:
    if ty.tag != "Code":
        raise TypeError(f"expected Code type, got {ty}")
    ins, out = ty.args
    return tuple(ins), out


# ---------------------------------------------------------------------------
# Expressions and programs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Expr:
    op: str
    ty: Ty
    args: Tuple["Expr", ...] = ()
    data: Any = None

    def to_data(self) -> Any:
        def enc(x: Any) -> Any:
            if isinstance(x, Ty):
                return x.to_data()
            if isinstance(x, Program):
                return x.to_data()
            if isinstance(x, tuple):
                return [enc(y) for y in x]
            if isinstance(x, list):
                return [enc(y) for y in x]
            if isinstance(x, dict):
                return {str(k): enc(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
            return x
        return {
            "op": self.op,
            "ty": self.ty.to_data(),
            "args": [a.to_data() for a in self.args],
            "data": enc(self.data),
        }

    @property
    def cost(self) -> int:
        # Every AST constructor costs one, including code constructors.
        return 1 + sum(a.cost for a in self.args)


@dataclass(frozen=True)
class Program:
    inputs: Tuple[Ty, ...]
    output: Ty
    body: Expr

    def __post_init__(self) -> None:
        if self.body.ty != self.output:
            raise TypeError("program body/output type mismatch")

    @property
    def ty(self) -> Ty:
        return CODE(self.inputs, self.output)

    @property
    def cost(self) -> int:
        return self.body.cost

    def to_data(self) -> Any:
        return {
            "inputs": [t.to_data() for t in self.inputs],
            "output": self.output.to_data(),
            "body": self.body.to_data(),
        }

    def digest(self) -> str:
        raw = json.dumps(self.to_data(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def run(self, *values: Any) -> Any:
        if len(values) != len(self.inputs):
            raise ValueError("wrong arity")
        for ty, value in zip(self.inputs, values):
            check_value(ty, value)
        out = eval_expr(self.body, tuple(values))
        check_value(self.output, out)
        return out


def expr_key(e: Expr) -> str:
    return json.dumps(e.to_data(), sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Runtime type checking
# ---------------------------------------------------------------------------

def check_value(ty: Ty, value: Any) -> None:
    if ty == BOOL:
        if type(value) is not bool:
            raise TypeError(f"expected Bool, got {value!r}")
        return
    if ty.tag == "Fin":
        n = int(ty.args[0])
        if type(value) is not int or not (0 <= value < n):
            raise TypeError(f"expected Fin({n}), got {value!r}")
        return
    if ty.tag == "Tuple":
        if not isinstance(value, tuple) or len(value) != len(ty.args):
            raise TypeError(f"expected {ty}, got {value!r}")
        for t, v in zip(ty.args, value):
            check_value(t, v)
        return
    if ty.tag == "Code":
        if not isinstance(value, Program):
            raise TypeError(f"expected {ty}, got {value!r}")
        ins, out = _code_sig(ty)
        if value.inputs != ins or value.output != out:
            raise TypeError(f"code signature mismatch: expected {ty}, got {value.ty}")
        return
    raise TypeError(f"unknown type {ty}")


# ---------------------------------------------------------------------------
# Smart constructors
# ---------------------------------------------------------------------------

def Var(i: int, ty: Ty) -> Expr:
    return Expr("var", ty, data=int(i))


def ConstBool(v: bool) -> Expr:
    return Expr("const", BOOL, data=bool(v))


def ConstFin(n: int, v: int) -> Expr:
    ty = FIN(n)
    check_value(ty, v)
    return Expr("const", ty, data=int(v))


def Not(x: Expr) -> Expr:
    if x.ty != BOOL:
        raise TypeError("Not expects Bool")
    return Expr("not", BOOL, (x,))


def Bin(op: str, a: Expr, b: Expr) -> Expr:
    if op not in {"and", "or", "xor"} or a.ty != BOOL or b.ty != BOOL:
        raise TypeError("Bool binary op type error")
    return Expr(op, BOOL, (a, b))


def Eq(a: Expr, b: Expr) -> Expr:
    if a.ty != b.ty:
        raise TypeError("Eq operands must have same type")
    return Expr("eq", BOOL, (a, b))


def If(c: Expr, a: Expr, b: Expr) -> Expr:
    if c.ty != BOOL or a.ty != b.ty:
        raise TypeError("If type error")
    return Expr("if", a.ty, (c, a, b))


def TupleExpr(*xs: Expr) -> Expr:
    return Expr("tuple", TUP(*(x.ty for x in xs)), tuple(xs))


def Get(t: Expr, i: int) -> Expr:
    if t.ty.tag != "Tuple":
        raise TypeError("Get expects Tuple")
    if not (0 <= i < len(t.ty.args)):
        raise IndexError(i)
    return Expr("get", t.ty.args[i], (t,), data=int(i))


def Quote(program: Program) -> Expr:
    return Expr("quote", program.ty, data=program)


def CodeConst(code_ty: Ty, value: Any) -> Expr:
    ins, out = _code_sig(code_ty)
    if out == BOOL:
        if type(value) is not bool:
            raise TypeError("Bool code constant expects bool")
        return Expr("code_const", code_ty, data=bool(value))
    if out.tag == "Fin":
        check_value(out, value)
        return Expr("code_const", code_ty, data=int(value))
    raise TypeError("CodeConst supports Bool/Fin outputs in MDC-L1")


def CodeProject(code_ty: Ty, input_index: int) -> Expr:
    ins, out = _code_sig(code_ty)
    if not (0 <= input_index < len(ins)):
        raise IndexError(input_index)
    if ins[input_index] != out:
        raise TypeError("projection output must match selected input type")
    return Expr("code_project", code_ty, data=int(input_index))


def CodeNot(x: Expr) -> Expr:
    ins, out = _code_sig(x.ty)
    if out != BOOL:
        raise TypeError("CodeNot expects Code[...,Bool]")
    return Expr("code_not", x.ty, (x,))


def CodeBin(op: str, a: Expr, b: Expr) -> Expr:
    if op not in {"and", "or", "xor"} or a.ty != b.ty:
        raise TypeError("CodeBin signature mismatch")
    _, out = _code_sig(a.ty)
    if out != BOOL:
        raise TypeError("CodeBin expects Bool-output code")
    return Expr(f"code_{op}", a.ty, (a, b))


def CodeIf(c: Expr, a: Expr, b: Expr) -> Expr:
    if c.ty != a.ty or a.ty != b.ty:
        raise TypeError("CodeIf signature mismatch")
    _, out = _code_sig(a.ty)
    if out != BOOL:
        raise TypeError("CodeIf V1 supports Bool-output code")
    return Expr("code_if", a.ty, (c, a, b))


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _rebind(expr: Expr, old_inputs: Tuple[Ty, ...], new_vars: Tuple[Expr, ...]) -> Expr:
    """Substitute program input variables with expressions.

    Used by code constructors.  The source expression is already typed; the
    substitution is purely structural and preserves its output type.
    """
    if expr.op == "var":
        i = int(expr.data)
        if not (0 <= i < len(old_inputs)):
            raise IndexError(i)
        replacement = new_vars[i]
        if replacement.ty != old_inputs[i]:
            raise TypeError("rebind type mismatch")
        return replacement
    return Expr(
        expr.op,
        expr.ty,
        tuple(_rebind(a, old_inputs, new_vars) for a in expr.args),
        expr.data,
    )


def _combine_code(op: str, ps: Sequence[Program]) -> Program:
    if not ps:
        raise ValueError("need code operands")
    inputs = ps[0].inputs
    if any(p.inputs != inputs for p in ps):
        raise TypeError("code input signature mismatch")
    vars_ = tuple(Var(i, t) for i, t in enumerate(inputs))
    bodies = tuple(_rebind(p.body, p.inputs, vars_) for p in ps)
    if op == "not":
        body = Not(bodies[0])
    elif op in {"and", "or", "xor"}:
        body = Bin(op, bodies[0], bodies[1])
    elif op == "if":
        body = If(bodies[0], bodies[1], bodies[2])
    else:
        raise ValueError(op)
    return Program(inputs, body.ty, body)


def eval_expr(e: Expr, env: Tuple[Any, ...]) -> Any:
    op = e.op
    if op == "var":
        i = int(e.data)
        if not (0 <= i < len(env)):
            raise IndexError(i)
        v = env[i]
        check_value(e.ty, v)
        return v
    if op == "const":
        check_value(e.ty, e.data)
        return e.data
    if op == "not":
        return not eval_expr(e.args[0], env)
    if op == "and":
        return bool(eval_expr(e.args[0], env) and eval_expr(e.args[1], env))
    if op == "or":
        return bool(eval_expr(e.args[0], env) or eval_expr(e.args[1], env))
    if op == "xor":
        return bool(eval_expr(e.args[0], env) ^ eval_expr(e.args[1], env))
    if op == "eq":
        return eval_expr(e.args[0], env) == eval_expr(e.args[1], env)
    if op == "if":
        return eval_expr(e.args[1], env) if eval_expr(e.args[0], env) else eval_expr(e.args[2], env)
    if op == "tuple":
        return tuple(eval_expr(a, env) for a in e.args)
    if op == "get":
        return eval_expr(e.args[0], env)[int(e.data)]
    if op == "quote":
        p = e.data
        if not isinstance(p, Program):
            raise TypeError("malformed quote")
        check_value(e.ty, p)
        return p
    if op == "code_const":
        ins, out = _code_sig(e.ty)
        if out == BOOL:
            body = ConstBool(bool(e.data))
        elif out.tag == "Fin":
            body = ConstFin(int(out.args[0]), int(e.data))
        else:
            raise TypeError(out)
        return Program(ins, out, body)
    if op == "code_project":
        ins, out = _code_sig(e.ty)
        i = int(e.data)
        if ins[i] != out:
            raise TypeError("malformed code_project")
        return Program(ins, out, Var(i, out))
    if op == "code_not":
        return _combine_code("not", [eval_expr(e.args[0], env)])
    if op in {"code_and", "code_or", "code_xor"}:
        return _combine_code(op[5:], [eval_expr(a, env) for a in e.args])
    if op == "code_if":
        return _combine_code("if", [eval_expr(a, env) for a in e.args])
    raise ValueError(f"unknown op {op}")


# ---------------------------------------------------------------------------
# Exact finite enumeration by cost
# ---------------------------------------------------------------------------

def _dedup(exprs: Iterable[Expr]) -> Tuple[Expr, ...]:
    out: Dict[str, Expr] = {}
    for e in exprs:
        out.setdefault(expr_key(e), e)
    return tuple(out[k] for k in sorted(out))


class Enumerator:
    """Finite exact-cost enumerator for MDC-L1.

    Completeness statements are only valid relative to:
      * the declared environment types,
      * target type,
      * grammar below,
      * and maximum cost.
    """

    def __init__(self, env_types: Sequence[Ty]):
        self.env_types = tuple(env_types)

    @lru_cache(maxsize=None)
    def exact(self, target: Ty, cost: int) -> Tuple[Expr, ...]:
        if cost <= 0:
            return tuple()
        xs: List[Expr] = []

        # Atomic expressions.
        if cost == 1:
            for i, ty in enumerate(self.env_types):
                if ty == target:
                    xs.append(Var(i, ty))

            if target == BOOL:
                xs.extend([ConstBool(False), ConstBool(True)])
            elif target.tag == "Fin":
                n = int(target.args[0])
                xs.extend(ConstFin(n, i) for i in range(n))
            elif target.tag == "Code":
                ins, out = _code_sig(target)
                if out == BOOL:
                    xs.extend([CodeConst(target, False), CodeConst(target, True)])
                elif out.tag == "Fin":
                    n = int(out.args[0])
                    xs.extend(CodeConst(target, i) for i in range(n))
                for i, t in enumerate(ins):
                    if t == out:
                        xs.append(CodeProject(target, i))
            return _dedup(xs)

        # Bool target grammar.
        if target == BOOL:
            for a in self.exact(BOOL, cost - 1):
                xs.append(Not(a))

            # Binary Bool ops: 1 + ca + cb = cost
            for ca in range(1, cost - 1):
                cb = cost - 1 - ca
                if cb < 1:
                    continue
                for a in self.exact(BOOL, ca):
                    for b in self.exact(BOOL, cb):
                        xs.extend([Bin("and", a, b), Bin("or", a, b), Bin("xor", a, b)])

            # Equality over each environment type gives useful finite predicates.
            for ty in sorted(set(self.env_types), key=str):
                for ca in range(1, cost - 1):
                    cb = cost - 1 - ca
                    if cb < 1:
                        continue
                    for a in self.exact(ty, ca):
                        for b in self.exact(ty, cb):
                            xs.append(Eq(a, b))

            # if c then a else b
            for cc in range(1, cost - 2):
                for ca in range(1, cost - 1 - cc):
                    cb = cost - 1 - cc - ca
                    if cb < 1:
                        continue
                    for c in self.exact(BOOL, cc):
                        for a in self.exact(BOOL, ca):
                            for b in self.exact(BOOL, cb):
                                xs.append(If(c, a, b))

        # Tuple target grammar.
        if target.tag == "Tuple":
            parts = tuple(target.args)
            # V1 enumerates 2-tuples exactly; larger tuples can be nested.
            if len(parts) == 2:
                for ca in range(1, cost - 1):
                    cb = cost - 1 - ca
                    if cb < 1:
                        continue
                    for a in self.exact(parts[0], ca):
                        for b in self.exact(parts[1], cb):
                            xs.append(TupleExpr(a, b))

        # First-class Code target grammar.
        if target.tag == "Code":
            ins, out = _code_sig(target)
            if out == BOOL:
                # CodeNot
                for a in self.exact(target, cost - 1):
                    xs.append(CodeNot(a))

                # Pointwise code Boolean ops.
                for ca in range(1, cost - 1):
                    cb = cost - 1 - ca
                    if cb < 1:
                        continue
                    for a in self.exact(target, ca):
                        for b in self.exact(target, cb):
                            xs.extend([
                                CodeBin("and", a, b),
                                CodeBin("or", a, b),
                                CodeBin("xor", a, b),
                            ])

                # Pointwise code if.
                for cc in range(1, cost - 2):
                    for ca in range(1, cost - 1 - cc):
                        cb = cost - 1 - cc - ca
                        if cb < 1:
                            continue
                        for c in self.exact(target, cc):
                            for a in self.exact(target, ca):
                                for b in self.exact(target, cb):
                                    xs.append(CodeIf(c, a, b))

        return _dedup(xs)

    def upto(self, target: Ty, max_cost: int) -> Iterator[Tuple[int, Expr]]:
        for cost in range(1, max_cost + 1):
            for e in self.exact(target, cost):
                yield cost, e


# ---------------------------------------------------------------------------
# Finite observational quotient
# ---------------------------------------------------------------------------

def observational_key(program: Program, domain: Sequence[Tuple[Any, ...]]) -> str:
    rows = []
    for inp in domain:
        if len(inp) != len(program.inputs):
            raise ValueError("domain row arity mismatch")
        out = program.run(*inp)
        if isinstance(out, Program):
            rows.append(["Code", out.digest()])
        else:
            rows.append(out)
    return json.dumps(rows, sort_keys=True, separators=(",", ":"))


def quotient_programs(
    programs: Iterable[Program],
    domain: Sequence[Tuple[Any, ...]],
) -> Tuple[Program, ...]:
    reps: Dict[str, Program] = {}
    for p in programs:
        k = observational_key(p, domain)
        old = reps.get(k)
        if old is None or (p.cost, p.digest()) < (old.cost, old.digest()):
            reps[k] = p
    return tuple(reps[k] for k in sorted(reps))


# ---------------------------------------------------------------------------
# Helpers for program synthesis
# ---------------------------------------------------------------------------

def synthesize(
    inputs: Sequence[Ty],
    output: Ty,
    max_cost: int,
) -> Iterator[Tuple[int, Program]]:
    enum = Enumerator(inputs)
    for cost, body in enum.upto(output, max_cost):
        yield cost, Program(tuple(inputs), output, body)


def synthesize_meta(
    meta_inputs: Sequence[Ty],
    target_code_type: Ty,
    max_cost: int,
) -> Iterator[Tuple[int, Program]]:
    """Enumerate programs whose *output is code*.

    Example: with meta_inputs=[Code[(Bool,Bool),Bool]] and the same target
    Code type, the resulting programs include identity, pointwise NOT,
    pointwise XOR with projections/constants, etc.  These are edits or
    edit-generators represented by the same Program/Expr object as ordinary
    task programs.
    """
    if target_code_type.tag != "Code":
        raise TypeError("target_code_type must be Code")
    enum = Enumerator(meta_inputs)
    for cost, body in enum.upto(target_code_type, max_cost):
        yield cost, Program(tuple(meta_inputs), target_code_type, body)
