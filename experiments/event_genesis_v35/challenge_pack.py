from __future__ import annotations
from dataclasses import dataclass
from itertools import product

from basis import Row, World

@dataclass(frozen=True)
class Case:
    axis: str
    world: World

AXES=("constant","first","parity","xor","pair4","triple8","conditional","distant")

PERMS=(
    (0,1,2,3,4,5),
    (3,4,1,5,2,0),
    (5,2,0,4,1,3),
)

MOTIF=(1,1,1,0,0,0)

def encode_payload(bits: tuple[int,...]) -> tuple[int,...]:
    raw=list(MOTIF)
    for b in bits:
        raw.extend((0,1) if int(b)==0 else (1,0))
    return tuple(raw)

def orbit(boundary: tuple[int,...]) -> set[tuple[int,...]]:
    n=len(boundary)
    out=set()
    for r in range(n):
        x=boundary[r:]+boundary[:r]
        out.add(x)
        out.add(tuple(reversed(x)))
    return out

def consequence(axis: str, bits: tuple[int,...]) -> int:
    x0,x1,x2,x3,x4,x5=bits
    if axis=="constant": return 0
    if axis=="first": return x0
    if axis=="parity": return sum(bits)%2
    if axis=="xor": return x0^x1
    if axis=="pair4": return 2*x0+x1
    if axis=="triple8": return 4*x0+2*x1+x2
    if axis=="conditional": return x0 if x4==0 else x1
    if axis=="distant": return 2*x0+x5
    raise ValueError(axis)

def relabel(axis: str, y: int) -> int:
    if axis=="constant": return 7
    if axis in {"first","parity","xor","conditional"}: return 1-int(y)
    if axis in {"pair4","distant"}: return 3-int(y)
    if axis=="triple8": return (3*int(y)+1)%8
    raise ValueError(axis)

def make_world(axis: str, variant: int, *, relabelled=False, incomplete=False) -> World:
    perm=PERMS[int(variant)]
    rows=[]
    for semantic in product((0,1),repeat=6):
        y=consequence(axis,semantic)
        if relabelled: y=relabel(axis,y)
        packed=tuple(semantic[i] for i in perm)
        presentations=sorted(orbit(encode_payload(packed)))
        if incomplete and semantic==(0,0,0,0,0,0):
            presentations=presentations[:-1]
        for boundary in presentations:
            rows.append(Row(tuple(boundary),None if incomplete else int(y)))
    return World(
        f"{axis}_v{variant}" + ("_rel" if relabelled else "") + ("_inc" if incomplete else ""),
        tuple(rows),
        not incomplete,
    )

VARIANTS={
    v:tuple(Case(axis,make_world(axis,v)) for axis in AXES)
    for v in range(3)
}
RELABELLED=tuple(Case(axis,make_world(axis,0,relabelled=True)) for axis in AXES)
INCOMPLETE=make_world("first",0,incomplete=True)
