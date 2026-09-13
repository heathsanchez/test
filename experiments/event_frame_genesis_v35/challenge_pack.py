from __future__ import annotations
from itertools import product
from basis import Row, World

N=6

def rotations(s):
    return tuple(s[i:]+s[:i] for i in range(len(s)))

def anchored_reverse(s):
    return (s[0],)+tuple(reversed(s[1:]))

def representative(s,mode):
    if mode=="FRAMED":
        return s
    if mode=="ANCHORED":
        return min(s,anchored_reverse(s))
    rots=rotations(s)
    if mode=="ORIENTED":
        return min(rots)
    rev=tuple(reversed(s))
    return min(rots+rotations(rev))

def code(bits):
    out=0
    for b in bits:
        out=(out<<1)|int(b)
    return out

def target(name,s):
    if name=="constant":
        return 0
    if name=="unframed1":
        return code(representative(s,"UNFRAMED")[:1])
    if name=="unframed3":
        return code(representative(s,"UNFRAMED")[:3])
    if name=="unframed6":
        return code(representative(s,"UNFRAMED")[:6])
    if name=="oriented4":
        return code(representative(s,"ORIENTED")[:4])
    if name=="anchored2":
        return code(representative(s,"ANCHORED")[:2])
    if name=="anchored3":
        return code(representative(s,"ANCHORED")[:3])
    if name=="framed2":
        return code(s[:2])
    if name=="framed3":
        return code(s[:3])
    raise ValueError(name)

NAMES=(
    "constant","unframed1","unframed3","unframed6",
    "oriented4","anchored2","anchored3","framed2","framed3",
)

EXPECTED={
    "constant":("UNFRAMED",0,0),
    "unframed1":("UNFRAMED",0,1),
    "unframed3":("UNFRAMED",0,3),
    "unframed6":("UNFRAMED",0,6),
    "oriented4":("ORIENTED",1,4),
    "anchored2":("ANCHORED",1,2),
    "anchored3":("ANCHORED",1,3),
    "framed2":("FRAMED",2,2),
    "framed3":("FRAMED",2,3),
}

def relabel(name,y):
    # Deterministic bijections on the actually used label range.
    if name=="constant":
        return 17
    if name in {"unframed1"}:
        return 1-int(y)
    if name in {"anchored2","framed2"}:
        return (3-int(y))
    if name in {"unframed3","anchored3","framed3"}:
        return (5*int(y)+1)%8
    if name=="oriented4":
        return (7*int(y)+3)%16
    if name=="unframed6":
        return (17*int(y)+5)%64
    raise ValueError(name)

def make_world(name,*,labels_relabelled=False,incomplete=False):
    rows=[]
    for s in product((0,1),repeat=N):
        y=target(name,s)
        if labels_relabelled:
            y=relabel(name,y)
        rows.append(Row(tuple(s),None if incomplete else int(y)))
    return World(name+("_rel" if labels_relabelled else ""),tuple(rows),not incomplete)

WORLDS={name:make_world(name) for name in NAMES}
RELABELLED={name:make_world(name,labels_relabelled=True) for name in NAMES}
INCOMPLETE=make_world("framed2",incomplete=True)
