from __future__ import annotations
from dataclasses import dataclass
from itertools import product

from basis import Row, World

@dataclass(frozen=True)
class Case:
    axis: str
    world: World

AXES=(
    "constant","early_event","delayed_event","xor_relation","pair4_relation",
    "triple8_relation","contextual","interventional","distant_pair","contraction",
)

PERMS=(
    (0,1,2,3,4,5,6),
    (3,4,1,6,2,0,5),
    (5,6,0,3,2,4,1),
)

def consequence(axis: str, bits: tuple[int,...]) -> int:
    x0,x1,x2,h,c,a,b=bits
    if axis=="constant": return 0
    if axis=="early_event": return x0
    if axis=="delayed_event": return h
    if axis=="xor_relation": return x0 ^ x1
    if axis=="pair4_relation": return 2*x0+x1
    if axis=="triple8_relation": return 4*x0+2*x1+x2
    if axis=="contextual": return x0 if c==0 else x1
    if axis=="interventional": return x0 if a==0 else x1
    if axis=="distant_pair": return 2*x0+b
    if axis=="contraction": return x0
    raise ValueError(axis)

def relabel(axis: str, y: int) -> int:
    if axis=="constant": return 7
    if axis in {"early_event","delayed_event","xor_relation","contextual","interventional","contraction"}:
        return 1-int(y)
    if axis in {"pair4_relation","distant_pair"}:
        return 3-int(y)
    if axis=="triple8_relation":
        return (3*int(y)+1)%8
    raise ValueError(axis)

def make_world(axis: str, variant: int, *, labels_relabelled: bool=False, incomplete: bool=False) -> World:
    perm=PERMS[int(variant)]
    rows=[]
    for bits in product((0,1),repeat=7):
        y=consequence(axis,bits)
        if labels_relabelled:
            y=relabel(axis,y)
        stream=tuple(int(bits[i]) for i in perm)
        rows.append(Row(stream,None if incomplete else int(y)))
    if variant==1:
        rows=list(reversed(rows))
    elif variant==2:
        rows=rows[37:]+rows[:37]
    return World(f"{axis}_v{variant}" + ("_rel" if labels_relabelled else ""),tuple(rows),not incomplete)

VARIANTS={
    i:tuple(Case(axis,make_world(axis,i)) for axis in AXES)
    for i in range(3)
}
RELABELLED=tuple(Case(axis,make_world(axis,0,labels_relabelled=True)) for axis in AXES)
INCOMPLETE=make_world("early_event",0,incomplete=True)
