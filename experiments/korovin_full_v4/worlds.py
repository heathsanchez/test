from __future__ import annotations
from dataclasses import dataclass
from itertools import product
import random

@dataclass(frozen=True)
class OpaqueWorld:
    tag: str
    n: int
    generators: dict[str, tuple[int, ...]]

def apply_map(f, x):
    return f[x]

def compose_map(f, g):
    return tuple(g[f[i]] for i in range(len(f)))

def unit_map(n):
    return tuple(range(n))

def execute(world: OpaqueWorld, word: tuple[str, ...]):
    out = unit_map(world.n)
    for t in word:
        out = compose_map(out, world.generators[t])
    return out

def words(tokens, lo, hi):
    if lo == 0:
        yield ()
        lo = 1
    for L in range(lo, hi + 1):
        yield from product(tokens, repeat=L)

def rows(world, lo=0, hi=9):
    return [(w, execute(world, w)) for w in words(tuple(world.generators), lo, hi)]

def conjugate(p, c):
    inv = [0]*len(c)
    for i,x in enumerate(c): inv[x]=i
    return tuple(c[p[inv[i]]] for i in range(len(p)))

def relabel_world(world, seed):
    r = random.Random(seed)
    perm = list(range(world.n))
    r.shuffle(perm)
    names = list(world.generators)
    shuffled = names[:]
    r.shuffle(shuffled)
    renamed = {}
    for old,new in zip(names, shuffled):
        renamed[new] = conjugate(world.generators[old], tuple(perm))
    return OpaqueWorld(f"blind_{seed}", world.n, renamed)

def source_world():
    return OpaqueWorld("blind_source", 4, {
        "p": (1,2,3,0),
        "q": (0,3,2,1),
    })

def transfer_world():
    return OpaqueWorld("blind_transfer", 3, {
        "u": (1,2,0),
        "v": (1,0,2),
    })

def noninvertible_control():
    return OpaqueWorld("blind_control", 3, {
        "m": (1,2,0),
        "n": (0,1,1),
    })

def cyclic_world(k):
    step = tuple((i+1)%k for i in range(k))
    step2 = tuple((i+2)%k for i in range(k))
    return OpaqueWorld(f"blind_cycle_{k}", k, {"z": step, "w": step2})
