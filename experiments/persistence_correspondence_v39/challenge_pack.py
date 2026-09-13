from __future__ import annotations
from itertools import product

from basis import Row, World
from kernel import Kernel

N=3

BASE={
    "no_persistence":(),
    "one_link":((0,1),),
    "two_link":((0,0),(1,1)),
    "full_link":((0,2),(1,0),(2,1)),
}

BEFORE_PERMS=(
    (0,1,2),
    (2,0,1),
    (1,2,0),
)
AFTER_PERMS=(
    (0,1,2),
    (1,2,0),
    (2,0,1),
)

def mapped(name,variant):
    return Kernel.map_matching(
        BASE[name],
        BEFORE_PERMS[int(variant)],
        AFTER_PERMS[int(variant)],
    )

def make_world(name,variant=0,*,active=False,relabel=False,incomplete=False):
    hidden=mapped(name,variant)
    rows=[]
    signatures=[]
    raw=[]

    for values in product((0,1),repeat=2*N):
        before=tuple(values[:N])
        after=tuple(values[N:])

        passive=Row(before,after,-1,-1,0)
        raw.append(passive)
        signatures.append(Kernel.signature(passive,hidden))

        if active:
            for i in range(N):
                for j in range(N):
                    row=Row(before,after,i,j,0)
                    raw.append(row)
                    signatures.append(Kernel.signature(row,hidden))

    ids={}
    labels=[]
    for sig in signatures:
        if sig not in ids:
            ids[sig]=len(ids)
        y=ids[sig]
        if relabel:
            y=23+13*int(y)
        labels.append(y)

    for row,y in zip(raw,labels):
        rows.append(Row(
            row.before,row.after,row.action_before,row.response_after,
            None if incomplete else int(y),
        ))

    suffix="_active" if active else "_passive"
    if relabel:
        suffix+="_rel"
    return World(f"{name}_v{variant}{suffix}",tuple(rows),not incomplete)

PASSIVE={(name,v):make_world(name,v,active=False) for name in BASE for v in range(3)}
ACTIVE_TWO={v:make_world("two_link",v,active=True) for v in range(3)}
RELABELLED={
    "no_persistence":make_world("no_persistence",0,active=False,relabel=True),
    "one_link":make_world("one_link",0,active=False,relabel=True),
    "two_link_passive":make_world("two_link",0,active=False,relabel=True),
    "two_link_active":make_world("two_link",0,active=True,relabel=True),
    "full_link":make_world("full_link",0,active=False,relabel=True),
}
INCOMPLETE=make_world("one_link",0,active=False,incomplete=True)
