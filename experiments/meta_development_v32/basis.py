from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Tuple

Value = Any
Vector = Tuple[Value, ...]

@dataclass(frozen=True)
class Row:
    banks: Tuple[Tuple[int, ...], ...]
    consequence: int | None

@dataclass(frozen=True)
class World:
    world_id: str
    rows: Tuple[Row, ...]
    complete: bool = True
    probes: Tuple[Row, ...] = ()

@dataclass(frozen=True)
class Expr:
    op: str
    args: Tuple[Any, ...] = ()

    def data(self) -> Any:
        out=[]
        for a in self.args:
            if isinstance(a, Expr): out.append(a.data())
            elif isinstance(a, tuple): out.append(list(a))
            else: out.append(a)
        return [self.op, *out]

    def token_count(self) -> int:
        return 1 + sum(a.token_count() for a in self.args if isinstance(a, Expr))

    def depth(self) -> int:
        ds=[a.depth() for a in self.args if isinstance(a, Expr)]
        return 1 + (max(ds) if ds else 0)

    def bank_pattern(self) -> Tuple[int, ...]:
        out=[]
        def walk(e: Expr):
            if e.op == 'READ':
                out.append(int(e.args[0]))
            for z in e.args:
                if isinstance(z, Expr): walk(z)
        walk(self)
        return tuple(out)


def read_exprs(world: World) -> Tuple[Expr, ...]:
    if not world.rows:
        return ()
    widths=tuple(len(b) for b in world.rows[0].banks)
    return tuple(Expr('READ',(b,i)) for b,w in enumerate(widths) for i in range(w))


def eval_expr(expr: Expr, row: Row) -> Value:
    op=expr.op
    if op == 'CONST': return 0
    if op == 'READ':
        b,i=expr.args
        return row.banks[int(b)][int(i)]
    if op == 'PAIR':
        a,b=expr.args
        return (eval_expr(a,row),eval_expr(b,row))
    if op == 'TUPLE3':
        a,b,c=expr.args
        return (eval_expr(a,row),eval_expr(b,row),eval_expr(c,row))
    if op == 'APPLY':
        tt,a,b=expr.args
        x=int(eval_expr(a,row)); y=int(eval_expr(b,row))
        if x not in (0,1) or y not in (0,1):
            return ('INVALID_BOOL',x,y)
        idx=(x<<1)|y
        return (int(tt)>>idx)&1
    if op == 'SWITCH':
        sel,a,b=expr.args
        s=int(eval_expr(sel,row))
        if s not in (0,1): return ('INVALID_SELECTOR',s)
        return eval_expr(a if s==0 else b,row)
    raise ValueError(op)


def vector(expr: Expr, rows: Iterable[Row]) -> Vector:
    return tuple(eval_expr(expr,r) for r in rows)


def canonical_partition(values: Iterable[Value]) -> Tuple[int, ...]:
    ids={}
    out=[]
    for v in values:
        if v not in ids: ids[v]=len(ids)
        out.append(ids[v])
    return tuple(out)


def consequence_partition(world: World) -> Tuple[int, ...]:
    if not world.complete or any(r.consequence is None for r in world.rows):
        raise ValueError('incomplete consequence authority')
    return canonical_partition(r.consequence for r in world.rows)


def exact_quotient(expr: Expr, world: World) -> bool:
    return canonical_partition(vector(expr,world.rows)) == consequence_partition(world)


def fit_predictor(expr: Expr, world: World) -> dict[Value,int] | None:
    m={}
    for r in world.rows:
        if r.consequence is None: return None
        k=eval_expr(expr,r)
        y=int(r.consequence)
        if k in m and m[k] != y: return None
        m[k]=y
    return m


def predict(expr: Expr, model: dict[Value,int], row: Row) -> int | None:
    return model.get(eval_expr(expr,row))


def family(expr: Expr) -> str:
    if expr.op in {'CONST','READ','PAIR','TUPLE3','SWITCH'}:
        return expr.op
    if expr.op == 'APPLY':
        # An APPLY whose child is itself APPLY is the compositional family.
        if any(isinstance(a,Expr) and a.op=='APPLY' for a in expr.args):
            return 'NESTED'
        return 'APPLY'
    return expr.op


def route_of(expr: Expr, stage: int) -> dict[str,Any]:
    return {
        'stage': int(stage),
        'family': family(expr),
        'bank_pattern': list(expr.bank_pattern()),
    }
