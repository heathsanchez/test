from __future__ import annotations

from basis import Row, World
from kernel import Kernel

N=8

THREE_ASSIGNMENT=tuple(
    ((s>>2)&1,(s>>1)&1,s&1)
    for s in range(N)
)
TWO_BY_FOUR_ASSIGNMENT=tuple(
    (s//4,s%4)
    for s in range(N)
)

HIDDEN_THREE=Kernel.factorization_from_assignment(THREE_ASSIGNMENT,(2,2,2))
HIDDEN_TWO_BY_FOUR=Kernel.factorization_from_assignment(TWO_BY_FOUR_ASSIGNMENT,(2,4))

STATE_PERMS=(
    (0,1,2,3,4,5,6,7),
    (3,6,1,7,0,4,2,5),
    (5,2,7,1,6,0,4,3),
)

KINDS=("one_target","two_target","three_target","two_by_four")

def toggle_hidden_binary(state:int,coord:int)->int:
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
    if kind=="one_target":
        return (
            (0,0),(1,0),
        )
    if kind=="two_target":
        return (
            (0,0),(1,0),(2,1),(3,1),
        )
    if kind=="three_target":
        return (
            (0,0),(1,0),(2,1),(3,1),(4,2),(5,2),
        )
    if kind=="two_by_four":
        return (
            (0,0),(1,0),(2,1),(3,1),
        )
    raise ValueError(kind)

def old_after(kind:str,state:int,action:int)->int:
    if kind in ("one_target","two_target","three_target"):
        target=dict(action_spec(kind))[int(action)]
        return toggle_hidden_binary(state,target)
    if kind=="two_by_four":
        return step_two_by_four(state,action)
    raise ValueError(kind)

def hidden_factorization(kind:str,variant:int=0):
    base=HIDDEN_TWO_BY_FOUR if kind=="two_by_four" else HIDDEN_THREE
    return Kernel.transform_factorization(base,STATE_PERMS[int(variant)])

def make_world(kind:str,variant:int=0,*,relabel=False,incomplete=False)->World:
    p=STATE_PERMS[int(variant)]
    spec=action_spec(kind)
    rows=[]
    for old_state in range(N):
        for action,target_class in spec:
            old_next=old_after(kind,old_state,action)
            y=int(target_class)
            if relabel:
                y=29+17*y
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

WORLDS={(kind,v):make_world(kind,v) for kind in KINDS for v in range(3)}
RELABELLED={kind:make_world(kind,0,relabel=True) for kind in KINDS}
INCOMPLETE=make_world("two_target",0,incomplete=True)
