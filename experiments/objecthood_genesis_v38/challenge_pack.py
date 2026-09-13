from __future__ import annotations
from itertools import permutations, product

from basis import Row, World
from kernel import Kernel

N=4
ALPHABET=(0,1,2)

P_BAL=((0,1),(2,3))
P_UNBAL=((0,),(1,2,3))
P_THREE=((0,),(1,),(2,3))
P_FOUR=((0,),(1,),(2,),(3,))

def orbit(base,group):
    return tuple(sorted({
        tuple(base[p[i]] for i in range(len(base)))
        for p in group
    }))

ID1=((0,),)
ID2=((0,1),)
ID3=((0,1,2),)
CYCLE3=((0,1,2),(1,2,0),(2,0,1))

HIDDEN={
    "constant":("VOID",None,()),
    "bag":("BAG",None,()),
    "balanced_objects":("OBJECTS",P_BAL,()),
    "unbalanced_objects":("OBJECTS",P_UNBAL,()),
    "three_objects":("OBJECTS",P_THREE,(orbit((0,),ID1),)),
    "four_ordered_triple":("OBJECTS",P_FOUR,(orbit((0,1,2),ID3),)),
    "four_cyclic_triple":("OBJECTS",P_FOUR,(orbit((0,1,2),CYCLE3),)),
    "four_two_pairs":("OBJECTS",P_FOUR,(orbit((0,1),ID2),orbit((2,3),ID2))),
}

EXPECTED_METRIC={
    "constant":(0,0,0,0,0),
    "bag":(0,1,0,0,0),
    "balanced_objects":(2,0,0,0,0),
    "unbalanced_objects":(2,0,0,0,0),
    "three_objects":(3,0,1,1,1),
    "four_ordered_triple":(4,0,1,3,1),
    "four_cyclic_triple":(4,0,1,3,3),
    "four_two_pairs":(4,0,2,4,2),
}

MARK_PERMS=(
    (0,1,2,3),
    (2,0,3,1),
    (3,2,0,1),
)

def map_hidden(kind,partition,structure,p):
    if kind!="OBJECTS":
        return kind,partition,structure
    mp,ms=Kernel.map_partition_structure(partition,structure,p)
    return kind,mp,ms

def signature(values,kind,partition,structure):
    if kind=="VOID":
        return ()
    if kind=="BAG":
        return tuple(sorted(int(v) for v in values))
    return Kernel.object_signature(tuple(int(v) for v in values),partition,structure)

def make_world(name,variant=0,*,relabel=False,incomplete=False):
    kind,partition,structure=HIDDEN[name]
    kind,partition,structure=map_hidden(kind,partition,structure,MARK_PERMS[int(variant)])

    rows=[]
    signatures=[]
    values_rows=list(product(ALPHABET,repeat=N))
    for values in values_rows:
        signatures.append(signature(tuple(values),kind,partition,structure))

    ids={}
    labels=[]
    for sig in signatures:
        if sig not in ids:
            ids[sig]=len(ids)
        y=ids[sig]
        if relabel:
            y=19+11*int(y)
        labels.append(y)

    for values,y in zip(values_rows,labels):
        rows.append(Row(tuple(values),None if incomplete else int(y)))

    return World(
        f"{name}_v{variant}" + ("_rel" if relabel else ""),
        tuple(rows),
        not incomplete,
    )

WORLDS={(name,v):make_world(name,v) for name in HIDDEN for v in range(3)}
RELABELLED={name:make_world(name,0,relabel=True) for name in HIDDEN}
INCOMPLETE=make_world("balanced_objects",0,incomplete=True)
