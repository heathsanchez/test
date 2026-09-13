from __future__ import annotations

from basis import Row, World

N=8

STATE_PERMS=(
    (0,1,2,3,4,5,6,7),
    (3,6,1,7,0,4,2,5),
    (5,2,7,1,6,0,4,3),
)

KINDS=("one_class","two_class","three_class","two_by_four","coupled_order8")

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

def d8_mul(x,y):
    k,b=x
    l,c=y
    return ((k + ((-1)**b)*l) % 4,(b+c)%2)

D8_ELEMS=tuple((k,b) for k in range(4) for b in range(2))
D8_INDEX={g:i for i,g in enumerate(D8_ELEMS)}

def left_action(generator,state:int)->int:
    return D8_INDEX[d8_mul(generator,D8_ELEMS[int(state)])]

def action_spec(kind:str):
    if kind=="one_class":
        return (
            (0,"bit",0,0),(1,"bit",0,0),
            (2,"bit",1,0),(3,"bit",1,0),
            (4,"bit",2,0),(5,"bit",2,0),
        )
    if kind=="two_class":
        return (
            (0,"bit",0,0),(1,"bit",0,0),
            (2,"bit",1,1),(3,"bit",1,1),
        )
    if kind=="three_class":
        return (
            (0,"bit",0,0),(1,"bit",0,0),
            (2,"bit",1,1),(3,"bit",1,1),
            (4,"bit",2,2),(5,"bit",2,2),
        )
    if kind=="two_by_four":
        return (
            (0,"two4",None,0),(1,"two4",None,0),
            (2,"two4",None,1),(3,"two4",None,1),
        )
    if kind=="coupled_order8":
        return (
            (0,"d8",(1,0),0),
            (1,"d8",(0,1),1),
        )
    raise ValueError(kind)

def old_after(kind:str,state:int,action:int,mode,param)->int:
    if mode=="bit":
        return flip_bit(state,int(param))
    if mode=="two4":
        return step_two_by_four(state,action)
    if mode=="d8":
        return left_action(param,state)
    raise ValueError(mode)

def make_world(kind:str,variant:int=0,*,relabel=False,incomplete=False)->World:
    p=STATE_PERMS[int(variant)]
    spec=action_spec(kind)
    rows=[]
    for old_state in range(N):
        for action,mode,param,label in spec:
            old_next=old_after(kind,old_state,action,mode,param)
            y=int(label)
            if relabel:
                y=53+23*y
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
INCOMPLETE=make_world("two_class",0,incomplete=True)
