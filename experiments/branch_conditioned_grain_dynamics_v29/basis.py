#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Iterator, Tuple

Partition = Tuple[Tuple[int,...],...]

@dataclass(frozen=True)
class BranchWorld:
    state_count:int
    histories:Tuple[Tuple[int,...],...]
    future_signatures:Tuple[Tuple[Tuple[int,...],...],...]
    complete:bool=True
    world_id:str=""
    def __post_init__(self):
        if len(self.histories)!=len(self.future_signatures): raise ValueError("history/future mismatch")
        for row in self.future_signatures:
            if len(row)!=self.state_count: raise ValueError("state mismatch")

def canonical_partition(blocks:Iterable[Iterable[int]])->Partition:
    out=[tuple(sorted(int(x) for x in b)) for b in blocks if tuple(b)]
    out.sort(key=lambda b:(b[0],len(b),b))
    return tuple(out)

def all_partitions(n:int)->Iterator[Partition]:
    blocks=[]
    def rec(i):
        if i==n:
            yield canonical_partition(blocks); return
        for j in range(len(blocks)):
            blocks[j].append(i); yield from rec(i+1); blocks[j].pop()
        blocks.append([i]); yield from rec(i+1); blocks.pop()
    yield from rec(0)

def sufficient(p:Partition,sigs:Tuple[Tuple[int,...],...])->bool:
    return all(len({tuple(sigs[x]) for x in b})==1 for b in p)

def partition_from_signatures(sigs)->Partition:
    groups={}
    for i,s in enumerate(sigs): groups.setdefault(tuple(s),[]).append(i)
    return canonical_partition(groups.values())

def refines(finer:Partition,coarser:Partition)->bool:
    return all(any(set(b)<=set(c) for c in coarser) for b in finer)

def incomparable(a:Partition,b:Partition)->bool:
    return not refines(a,b) and not refines(b,a)

def block_sizes(p:Partition):
    return tuple(sorted(len(b) for b in p))
