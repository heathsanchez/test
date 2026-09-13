#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable,Iterator,Tuple

Partition=Tuple[Tuple[int,...],...]

@dataclass(frozen=True)
class InstrumentWorld:
 state_count:int
 instrument_names:Tuple[str,...]
 outcomes:Tuple[Tuple[int,...],...]
 post_states:Tuple[Tuple[int,...],...]
 future_signatures:Tuple[Tuple[int,...],...]
 complete:bool=True
 world_id:str=""
 def __post_init__(self):
  if len(self.instrument_names)!=len(self.outcomes) or len(self.instrument_names)!=len(self.post_states):raise ValueError("instrument mismatch")
  if len(self.future_signatures)!=self.state_count:raise ValueError("future mismatch")
  for row in self.outcomes+self.post_states:
   if len(row)!=self.state_count:raise ValueError("state width mismatch")

def canonical_partition(blocks:Iterable[Iterable[int]])->Partition:
 out=[tuple(sorted(int(x) for x in b)) for b in blocks]
 out=[b for b in out if b]; out.sort(key=lambda b:(b[0],len(b),b)); return tuple(out)

def all_partitions(n:int)->Iterator[Partition]:
 blocks=[]
 def rec(i):
  if i==n:yield canonical_partition(blocks);return
  for j in range(len(blocks)):
   blocks[j].append(i);yield from rec(i+1);blocks[j].pop()
  blocks.append([i]);yield from rec(i+1);blocks.pop()
 yield from rec(0)

def sufficient(p:Partition,sigs)->bool:
 return all(len({tuple(sigs[x]) for x in b})==1 for b in p)

def refines(finer:Partition,coarser:Partition)->bool:
 return all(any(set(b)<=set(c) for c in coarser) for b in finer)

def incomparable(a:Partition,b:Partition)->bool:
 return not refines(a,b) and not refines(b,a)

def block_sizes(p):return tuple(sorted(len(b) for b in p))
