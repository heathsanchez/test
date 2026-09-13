from __future__ import annotations
from itertools import product

from basis import Trace, World

ALPHABET_SIZE=3
PREFIX_DEPTH=4
MAX_FUTURE_DEPTH=4
COMPLETE_DEPTH=PREFIX_DEPTH+MAX_FUTURE_DEPTH

TOKEN_PERMS=(
    (0,1,2),
    (1,2,0),
    (2,0,1),
)

KINDS=(
    "constant",
    "parity",
    "future_four",
    "delayed_four",
    "nonminimal_six",
)

HIDDEN_GENERATOR_STATE_COUNT={
    "constant":1,
    "parity":2,
    "future_four":4,
    "delayed_four":4,
    "nonminimal_six":6,
}

EXPECTED_FLOOR_DEPTH={
    "constant":0,
    "parity":0,
    "future_four":1,
    "delayed_four":2,
    "nonminimal_six":1,
}

EXPECTED_STATE_COUNT={
    "constant":1,
    "parity":2,
    "future_four":4,
    "delayed_four":4,
    "nonminimal_six":4,
}

EXPECTED_TOKEN_CLASS_COUNT={
    "constant":1,
    "parity":2,
    "future_four":3,
    "delayed_four":2,
    "nonminimal_six":3,
}

EXPECTED_TOKEN_CLASSES={
    "constant":((0,1,2),),
    "parity":((0,),(1,2)),
    "future_four":((0,),(1,),(2,)),
    "delayed_four":((0,),(1,2)),
    "nonminimal_six":((0,),(1,),(2,)),
}

def words(max_depth:int):
    out=[()]
    for depth in range(1,int(max_depth)+1):
        out.extend(product(range(ALPHABET_SIZE),repeat=depth))
    return tuple(out)

def consequence(kind:str,history:tuple[int,...])->int:
    if kind=="constant":
        return 0

    if kind=="parity":
        trans=(
            (1,0,0),
            (0,1,1),
        )
        outputs=(0,1)
        state=0
        for token in history:
            state=trans[state][token]
        return outputs[state]

    if kind=="future_four":
        # Hidden two-bit state; consequence sees only AND.
        trans=tuple(
            (state^2,state^1,state)
            for state in range(4)
        )
        outputs=(0,0,0,1)
        state=0
        for token in history:
            state=trans[state][token]
        return outputs[state]

    if kind=="delayed_four":
        trans=(
            (1,0,0),
            (2,1,1),
            (3,2,2),
            (3,3,3),
        )
        outputs=(0,0,0,1)
        state=0
        for token in history:
            state=trans[state][token]
        return outputs[state]

    if kind=="nonminimal_six":
        # Six hidden generator states; behavioral equivalence collapses
        # states 2~4 and 3~5, yielding a four-state floor.
        trans=(
            (4,1,0),
            (5,0,1),
            (0,3,4),
            (1,2,5),
            (0,5,2),
            (1,4,3),
        )
        outputs=(0,0,0,1,0,1)
        state=0
        for token in history:
            state=trans[state][token]
        return outputs[state]

    raise ValueError(kind)

def permute_history(history,perm):
    return tuple(int(perm[token]) for token in history)

def transform_token_classes(classes,perm):
    return tuple(sorted(
        (
            tuple(sorted(int(perm[token]) for token in cls))
            for cls in classes
        ),
        key=lambda cls:cls[0],
    ))

def make_world(kind:str,variant:int=0,*,relabel=False,incomplete=False)->World:
    perm=TOKEN_PERMS[int(variant)]
    rows=[]
    all_words=words(COMPLETE_DEPTH)

    # Iterate base histories then rename the opaque encounter alphabet.
    for history in all_words:
        observed=permute_history(history,perm)
        y=consequence(kind,history)
        if relabel:
            y=101+43*int(y)
        rows.append(Trace(
            tokens=observed,
            consequence=None if incomplete and len(history)==COMPLETE_DEPTH else int(y),
        ))

    return World(
        world_id=f"{kind}_v{variant}" + ("_rel" if relabel else ""),
        alphabet_size=ALPHABET_SIZE,
        prefix_depth=PREFIX_DEPTH,
        max_future_depth=MAX_FUTURE_DEPTH,
        traces=tuple(rows),
        complete=not incomplete,
    )

WORLDS={(kind,v):make_world(kind,v) for kind in KINDS for v in range(3)}
RELABELLED={kind:make_world(kind,0,relabel=True) for kind in KINDS}
INCOMPLETE=make_world("parity",0,incomplete=True)
