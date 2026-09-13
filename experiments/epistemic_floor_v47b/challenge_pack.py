from __future__ import annotations
from itertools import product

from basis import Sample, World

ALPHABET_SIZE=2
CONSEQUENCE_ALPHABET_SIZE=2
PREFIX_DEPTH=3
MAX_FUTURE_DEPTH=2
TOTAL_DEPTH=PREFIX_DEPTH+MAX_FUTURE_DEPTH

TOKEN_PERMS=((0,1),(1,0))

KINDS=(
    "parity_open",
    "parity_repeated_open",
    "parity_closed",
    "future_open",
    "future_closed",
    "branching_open",
    "constant_closed",
)

def words():
    out=[()]
    for depth in range(1,TOTAL_DEPTH+1):
        out.extend(product(range(ALPHABET_SIZE),repeat=depth))
    return tuple(out)

UNIVERSE=words()

def consequence(base_kind:str,history:tuple[int,...])->int:
    if base_kind=="constant":
        return 0
    if base_kind=="parity":
        state=0
        for token in history:
            if token==0:
                state ^= 1
        return state
    if base_kind=="future":
        state=0
        for token in history:
            state ^= (2 if token==0 else 1)
        return 1 if state==3 else 0
    raise ValueError(base_kind)

def permute_history(history,perm):
    return tuple(int(perm[token]) for token in history)

def make_samples(base_kind:str,variant:int=0,repeats:int=1,relabel=False):
    perm=TOKEN_PERMS[int(variant)]
    rows=[]
    for h in UNIVERSE:
        y=consequence(base_kind,h)
        if relabel:
            y=1-y
        observed=permute_history(h,perm)
        for _ in range(int(repeats)):
            rows.append(Sample(observed,int(y)))
    return tuple(rows)

def all_closed(variant:int=0):
    perm=TOKEN_PERMS[int(variant)]
    return tuple(permute_history(h,perm) for h in UNIVERSE)

def make_world(kind:str,variant:int=0,*,relabel=False,packet_complete=True)->World:
    if kind=="parity_open":
        base="parity"; repeats=1; closed=()
    elif kind=="parity_repeated_open":
        base="parity"; repeats=29; closed=()
    elif kind=="parity_closed":
        base="parity"; repeats=1; closed=all_closed(variant)
    elif kind=="future_open":
        base="future"; repeats=1; closed=()
    elif kind=="future_closed":
        base="future"; repeats=1; closed=all_closed(variant)
    elif kind=="branching_open":
        base="parity"; repeats=1; closed=()
    elif kind=="constant_closed":
        base="constant"; repeats=1; closed=all_closed(variant)
    else:
        raise ValueError(kind)

    samples=list(make_samples(base,variant,repeats,relabel))

    if kind=="branching_open":
        # Both binary consequences are positively witnessed at the empty history.
        samples.append(Sample((),0))
        samples.append(Sample((),1))

    return World(
        world_id=f"{kind}_v{variant}" + ("_rel" if relabel else ""),
        alphabet_size=ALPHABET_SIZE,
        consequence_alphabet_size=CONSEQUENCE_ALPHABET_SIZE,
        prefix_depth=PREFIX_DEPTH,
        max_future_depth=MAX_FUTURE_DEPTH,
        samples=tuple(samples),
        closed_histories=tuple(closed),
        packet_complete=packet_complete,
    )

def constant_single_open(index:int,variant:int=0,relabel=False)->World:
    perm=TOKEN_PERMS[int(variant)]
    target=permute_history(UNIVERSE[int(index)],perm)
    closed=tuple(h for h in all_closed(variant) if h!=target)
    return World(
        world_id=f"constant_single_open_{index}_v{variant}",
        alphabet_size=ALPHABET_SIZE,
        consequence_alphabet_size=CONSEQUENCE_ALPHABET_SIZE,
        prefix_depth=PREFIX_DEPTH,
        max_future_depth=MAX_FUTURE_DEPTH,
        samples=make_samples("constant",variant,1,relabel),
        closed_histories=closed,
        packet_complete=True,
    )

WORLDS={(kind,v):make_world(kind,v) for kind in KINDS for v in range(2)}
RELABELLED={kind:make_world(kind,0,relabel=True) for kind in KINDS}
INCOMPLETE=make_world("parity_closed",0,packet_complete=False)
