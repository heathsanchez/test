from __future__ import annotations

from basis import Row, World
from kernel import Kernel

N=8

STATE_PERMS=(
    (0,1,2,3,4,5,6,7),
    (3,6,1,7,0,4,2,5),
    (5,2,7,1,6,0,4,3),
)

KINDS=("one_class","two_class","three_class","two_by_four")

def flip_bit(state:int,coord:int)->int:
    return int(state) ^ (1<<(2-int(coord)))

def step_two_by_four(state:int,action:int)->int:
    a=int(state)//4
    b=int(state)%4
    if action in (0,1):
        a ^= 1
    elif action==2:
        b=(b+1)%4
    elif action==3:
        b=(b+2)%4
    else:
        raise ValueError(action)
    return 4*a+b

def action_spec(kind:str):
    if kind=="one_class":
        return (
            (0,0,0),(1,0,0),
            (2,1,0),(3,1,0),
            (4,2,0),(5,2,0),
        )
    if kind=="two_class":
        return (
            (0,0,0),(1,0,0),
            (2,1,1),(3,1,1),
        )
    if kind=="three_class":
        return (
            (0,0,0),(1,0,0),
            (2,1,1),(3,1,1),
            (4,2,2),(5,2,2),
        )
    if kind=="two_by_four":
        return (
            (0,None,0),(1,None,0),
            (2,None,1),(3,None,1),
        )
    raise ValueError(kind)

def old_after(kind:str,state:int,action:int,coord):
    if kind in ("one_class","two_class","three_class"):
        return flip_bit(state,int(coord))
    if kind=="two_by_four":
        return step_two_by_four(state,action)
    raise ValueError(kind)

def make_world(kind:str,variant:int=0,*,relabel=False,incomplete=False)->World:
    p=STATE_PERMS[int(variant)]
    spec=action_spec(kind)
    rows=[]
    for old_state in range(N):
        for action,coord,label in spec:
            old_next=old_after(kind,old_state,action,coord)
            y=int(label)
            if relabel:
                y=41+19*y
            rows.append(Row(
                state=int(p[old_state]),
                action=int(action),
                after=int(p[old_next]),
                consequence=None if incomplete else y,
            ))
    return World(
        world_id=f"{kind}_v{variant}" + ("_rel" if relabel else ""),
        state_count=N,
        action_count=len(spec),
        rows=tuple(rows),
        complete=not incomplete,
    )

def partition_from_function(fn):
    groups={}
    for s in range(N):
        groups.setdefault(fn(s),[]).append(s)
    return tuple(sorted(tuple(v) for _,v in sorted(groups.items())))

THREE_EXPECTED=(
    partition_from_function(lambda s:(s>>2)&1),
    partition_from_function(lambda s:(s>>1)&1),
    partition_from_function(lambda s:s&1),
)

TWO_BY_FOUR_EXPECTED=(
    partition_from_function(lambda s:s//4),
    partition_from_function(lambda s:s%4),
)

def transform_partition(partition,p):
    return tuple(sorted(
        tuple(sorted(int(p[s]) for s in block))
        for block in partition
    ))

def transformed_expected(kind,variant):
    p=STATE_PERMS[int(variant)]
    base=THREE_EXPECTED if kind=="three_class" else TWO_BY_FOUR_EXPECTED
    return tuple(transform_partition(part,p) for part in base)

WORLDS={(kind,v):make_world(kind,v) for kind in KINDS for v in range(3)}
RELABELLED={kind:make_world(kind,0,relabel=True) for kind in KINDS}
INCOMPLETE=make_world("two_class",0,incomplete=True)
