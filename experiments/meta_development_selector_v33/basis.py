from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from typing import Iterable, Tuple
Bit = int
Record = Tuple[Tuple[Bit, ...], ...]
@dataclass(frozen=True)
class World:
    world_id: str
    records: Tuple[Record, ...]
    targets: Tuple[int, ...]
    complete: bool = True
    current_signature: Tuple[int, ...] | None = None
    @property
    def channel_count(self): return len(self.records[0][0]) if self.records else 0
    @property
    def max_offset(self): return len(self.records[0]) - 1 if self.records else 0
    def validate(self):
        if not self.complete or not self.records or len(self.records) != len(self.targets): return False
        c=self.channel_count; d=self.max_offset+1
        return all(len(r)==d and all(len(s)==c for s in r) for r in self.records)
class Expr:
    def eval(self, record): raise NotImplementedError
    def atoms(self): raise NotImplementedError
    def ops(self): raise NotImplementedError
    def depth(self): raise NotImplementedError
    def lag_sum(self): raise NotImplementedError
    def data(self): raise NotImplementedError
@dataclass(frozen=True)
class Const(Expr):
    value: Bit
    def eval(self, record): return int(self.value)&1
    def atoms(self): return 0
    def ops(self): return 0
    def depth(self): return 0
    def lag_sum(self): return 0
    def data(self): return ["K",int(self.value)]
@dataclass(frozen=True)
class Atom(Expr):
    offset:int
    channel:int
    def eval(self, record): return int(record[self.offset][self.channel])&1
    def atoms(self): return 1
    def ops(self): return 0
    def depth(self): return 0
    def lag_sum(self): return int(self.offset)
    def data(self): return ["A",int(self.offset),int(self.channel)]
@dataclass(frozen=True)
class Bin(Expr):
    op:int
    left:Expr
    right:Expr
    def eval(self,record):
        a=self.left.eval(record); b=self.right.eval(record); return (int(self.op)>>((a<<1)|b))&1
    def atoms(self): return self.left.atoms()+self.right.atoms()
    def ops(self): return 1+self.left.ops()+self.right.ops()
    def depth(self): return 1+max(self.left.depth(),self.right.depth())
    def lag_sum(self): return self.left.lag_sum()+self.right.lag_sum()
    def data(self): return ["B",int(self.op),self.left.data(),self.right.data()]
def signature(expr,records): return tuple(expr.eval(r) for r in records)
def sufficient(sig,targets):
    seen={}
    for s,y in zip(sig,targets):
        if s in seen and seen[s]!=y:return False
        seen[s]=y
    return True
def mapping_for(sig,targets):
    if not sufficient(sig,targets):return None
    out={}
    for s,y in zip(sig,targets):out[s]=y
    return tuple(sorted(out.items()))
def predict_with(expr,mapping,record): return dict(mapping).get(expr.eval(record),None)
def expr_cost(expr,sig): return (len(set(sig)),expr.atoms(),expr.ops(),expr.depth(),expr.lag_sum())
def canonical_skeleton(expr):
    env={}; next_id=[0]
    def go(e):
        if isinstance(e,Const):return ("K",e.value)
        if isinstance(e,Atom):
            key=(e.offset,e.channel)
            if key not in env:env[key]=next_id[0]; next_id[0]+=1
            return ("A",e.offset,env[key])
        return ("B",e.op,go(e.left),go(e.right))
    return go(expr)
def skeleton_var_count(sk):
    vals=[]
    def walk(x):
        if isinstance(x,tuple):
            if x and x[0]=="A":vals.append(int(x[2]))
            for z in x[1:]:walk(z)
    walk(sk); return max(vals)+1 if vals else 0
