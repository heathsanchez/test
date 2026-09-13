#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

Relation = Tuple[Tuple[int,...], ...]
Signature = Tuple[int,...]
Permutation = Tuple[int,...]

@dataclass(frozen=True)
class RelationalWorld:
    n: int
    relations: Tuple[Relation, ...]
    consequences: Tuple[Signature, ...]
    complete: bool
    world_id: str = ""

    def __post_init__(self):
        if self.n <= 0:
            raise ValueError("n must be positive")
        for R in self.relations:
            if len(R) != self.n or any(len(row) != self.n for row in R):
                raise ValueError("relation shape mismatch")
        if len(self.consequences) != self.n:
            raise ValueError("consequence row mismatch")

    def interface_key(self):
        return (self.n, len(self.relations), len(self.consequences[0]) if self.consequences else 0)

def identity(n:int)->Permutation:
    return tuple(range(n))

def compose(p:Permutation,q:Permutation)->Permutation:
    return tuple(p[q[i]] for i in range(len(p)))

def inverse(p:Permutation)->Permutation:
    out=[0]*len(p)
    for i,j in enumerate(p):
        out[j]=i
    return tuple(out)
