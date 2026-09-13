#!/usr/bin/env python3
"""Frozen V19 raw temporal measurement substrate."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple

Accessor = Tuple[int,int]
Frame = Tuple[int,...]
Window = Tuple[Frame,...]
BinaryCounts = Tuple[int,int]

def digest_json(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",",":"), default=str).encode()).hexdigest()

@dataclass(frozen=True)
class TemporalWorld:
    channel_count: int
    max_lag: int
    windows: Tuple[Window,...]
    future_tests: Tuple[Tuple[int,...],...]
    counts: Tuple[Tuple[BinaryCounts,...],...]
    complete: bool
    world_id: str = ""

    def __post_init__(self):
        if len(self.windows) != len(self.counts):
            raise ValueError("window/count mismatch")
        for w in self.windows:
            if len(w) < self.max_lag + 1:
                raise ValueError("window too short")
            for frame in w:
                if len(frame) != self.channel_count:
                    raise ValueError("frame width mismatch")
        for row in self.counts:
            if len(row) != len(self.future_tests):
                raise ValueError("test count mismatch")

    def value(self, i:int, a:Accessor) -> int:
        lag,ch=a
        return self.windows[i][lag][ch]

    def accessor_cost(self,a:Accessor)->int:
        return 1 + int(a[0])

    def interface_key(self):
        return (self.channel_count,self.max_lag,self.future_tests)

def generated_accessors(world:TemporalWorld, depth:int):
    d=min(int(depth),world.max_lag)
    return tuple((lag,ch) for lag in range(d+1) for ch in range(world.channel_count))

def partition(world:TemporalWorld, accessors:Iterable[Accessor]):
    aa=tuple(sorted(set(accessors)))
    groups: Dict[Tuple[int,...],list[int]]={}
    for i in range(len(world.windows)):
        key=tuple(world.value(i,a) for a in aa)
        groups.setdefault(key,[]).append(i)
    out=[tuple(v) for v in groups.values()]
    out.sort(key=lambda c:(len(c),c))
    return tuple(out)

def readout_digest(world:TemporalWorld, accessors:Iterable[Accessor]):
    aa=tuple(sorted(set(accessors)))
    return digest_json({"interface":[world.channel_count,world.max_lag,[list(t) for t in world.future_tests]],"accessors":[list(a) for a in aa]})
