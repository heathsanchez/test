from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class OpaqueWorld:
    tag: str
    n: int
    generators: dict[str, tuple[int, ...]]

def compose_map(f,g):
    return tuple(g[f[i]] for i in range(len(f)))

def unit_map(n):
    return tuple(range(n))

def execute(world: OpaqueWorld, word: tuple[str, ...]):
    out=unit_map(world.n)
    for t in word:
        out=compose_map(out,world.generators[t])
    return out

def source_world():
    return OpaqueWorld('blind_source',4,{'p':(1,2,3,0),'q':(0,3,2,1)})

def transfer_world():
    return OpaqueWorld('blind_transfer',3,{'u':(1,2,0),'v':(1,0,2)})

def noninvertible_control():
    return OpaqueWorld('blind_control',3,{'m':(1,2,0),'n':(0,1,1)})
