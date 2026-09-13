from __future__ import annotations

from basis import Row, World

N=8

STATE_PERMS=(
    (0,1,2,3,4,5,6,7),
    (3,6,1,7,0,4,2,5),
    (5,2,7,1,6,0,4,3),
)

KINDS=(
    "deterministic_one_class",
    "partial_one_class",
    "nondeterministic_one_class",
    "nondeterministic_two_class",
    "nondeterministic_three_class",
    "mixed_three_class",
    "coupled_flip_blur",
)

def deterministic_flip(mask:int):
    return tuple(((s^int(mask)),) for s in range(N))

def partial_identity(mask:int):
    return tuple(
        ((s,) if (s & int(mask))==0 else ())
        for s in range(N)
    )

def blur(mask:int):
    return tuple(
        tuple(sorted({s,s^int(mask)}))
        for s in range(N)
    )

RELATIONS={
    "flip4":deterministic_flip(4),
    "flip2":deterministic_flip(2),
    "flip1":deterministic_flip(1),
    "partial4":partial_identity(4),
    "blur4":blur(4),
    "blur2":blur(2),
    "blur1":blur(1),
}

def action_spec(kind:str):
    if kind=="deterministic_one_class":
        return (
            (0,"flip4",0),
            (1,"flip2",0),
            (2,"flip1",0),
        )
    if kind=="partial_one_class":
        return (
            (0,"partial4",0),
        )
    if kind=="nondeterministic_one_class":
        return (
            (0,"blur4",0),
        )
    if kind=="nondeterministic_two_class":
        return (
            (0,"blur4",0),
            (1,"blur2",1),
        )
    if kind=="nondeterministic_three_class":
        return (
            (0,"blur4",0),
            (1,"blur2",1),
            (2,"blur1",2),
        )
    if kind=="mixed_three_class":
        return (
            (0,"flip4",0),
            (1,"blur2",1),
            (2,"blur1",2),
        )
    if kind=="coupled_flip_blur":
        return (
            (0,"flip4",0),
            (1,"blur4",1),
        )
    raise ValueError(kind)

def transform_relation(relation,p):
    out=[None]*N
    for old_state,row in enumerate(relation):
        new_state=int(p[old_state])
        out[new_state]=tuple(sorted(int(p[y]) for y in row))
    return tuple(out)

def make_world(kind:str,variant:int=0,*,relabel=False,incomplete=False)->World:
    p=STATE_PERMS[int(variant)]
    spec=action_spec(kind)
    rows=[]
    for action,name,label in spec:
        relation=transform_relation(RELATIONS[name],p)
        y=int(label)
        if relabel:
            y=71+37*y
        for state,afters in enumerate(relation):
            rows.append(Row(
                state=int(state),
                action=int(action),
                afters=tuple(int(v) for v in afters),
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
INCOMPLETE=make_world("partial_one_class",0,incomplete=True)
