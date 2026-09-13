from __future__ import annotations

from basis import Row, World

N=8

STATE_PERMS=(
    (0,1,2,3,4,5,6,7),
    (3,6,1,7,0,4,2,5),
    (5,2,7,1,6,0,4,3),
)

KINDS=(
    "reversible_one_class",
    "collapse_chain_one_class",
    "reversible_two_class",
    "reversible_three_class",
    "reset_three_class",
    "mixed_two_class",
    "coupled_flip_reset",
)

def flip_mask(state:int,mask:int)->int:
    return int(state)^int(mask)

def reset_mask(state:int,mask:int)->int:
    return int(state)&(~int(mask))

def collapse_half(state:int)->int:
    return int(state)//2

def rotate_second(state:int,amount:int=1)->int:
    a=int(state)//4
    b=int(state)%4
    return 4*a + ((b+int(amount))%4)

def reset_second_zero(state:int)->int:
    a=int(state)//4
    return 4*a

def action_spec(kind:str):
    if kind=="reversible_one_class":
        return (
            (0,"flip",4,0),
            (1,"flip",2,0),
            (2,"flip",1,0),
        )
    if kind=="collapse_chain_one_class":
        return (
            (0,"collapse",None,0),
        )
    if kind=="reversible_two_class":
        return (
            (0,"flip",4,0),
            (1,"flip",2,1),
        )
    if kind=="reversible_three_class":
        return (
            (0,"flip",4,0),
            (1,"flip",2,1),
            (2,"flip",1,2),
        )
    if kind=="reset_three_class":
        return (
            (0,"reset",4,0),
            (1,"reset",2,1),
            (2,"reset",1,2),
        )
    if kind=="mixed_two_class":
        return (
            (0,"flip",4,0),
            (1,"rotate_second",1,1),
            (2,"reset_second",None,1),
        )
    if kind=="coupled_flip_reset":
        return (
            (0,"flip",4,0),
            (1,"reset",4,1),
        )
    raise ValueError(kind)

def old_after(state:int,mode:str,param):
    if mode=="flip":
        return flip_mask(state,int(param))
    if mode=="reset":
        return reset_mask(state,int(param))
    if mode=="collapse":
        return collapse_half(state)
    if mode=="rotate_second":
        return rotate_second(state,int(param))
    if mode=="reset_second":
        return reset_second_zero(state)
    raise ValueError(mode)

def make_world(kind:str,variant:int=0,*,relabel=False,incomplete=False)->World:
    p=STATE_PERMS[int(variant)]
    spec=action_spec(kind)
    rows=[]
    for old_state in range(N):
        for action,mode,param,label in spec:
            old_next=old_after(old_state,mode,param)
            y=int(label)
            if relabel:
                y=61+31*y
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
INCOMPLETE=make_world("reset_three_class",0,incomplete=True)
