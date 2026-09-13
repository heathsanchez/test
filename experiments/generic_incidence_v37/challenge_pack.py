from __future__ import annotations
from itertools import permutations, product

from basis import Row, World
from kernel import Kernel

N=4
ALPHABET=(0,1,2)

def orbit(base,group):
    return tuple(sorted({
        tuple(base[p[i]] for i in range(len(base)))
        for p in group
    }))

ID1=((0,),)
ID2=((0,1),)
SWAP2=((0,1),(1,0))
ID3=((0,1,2),)
CYCLE3=((0,1,2),(1,2,0),(2,0,1))
FULL3=tuple(permutations(range(3)))

HIDDEN={
    "zero":(),
    "one_place":(
        orbit((0,),ID1),
    ),
    "oriented_pair":(
        orbit((0,1),ID2),
    ),
    "symmetric_pair":(
        orbit((0,1),SWAP2),
    ),
    "ordered_triple":(
        orbit((0,1,2),ID3),
    ),
    "cyclic_triple":(
        orbit((0,1,2),CYCLE3),
    ),
    "symmetric_triple":(
        orbit((0,1,2),FULL3),
    ),
    "two_symmetric_pairs":(
        orbit((0,1),SWAP2),
        orbit((2,3),SWAP2),
    ),
}

EXPECTED_METRIC={
    "zero":(0,0,0),
    "one_place":(1,1,1),
    "oriented_pair":(1,2,1),
    "symmetric_pair":(1,2,2),
    "ordered_triple":(1,3,1),
    "cyclic_triple":(1,3,3),
    "symmetric_triple":(1,3,6),
    "two_symmetric_pairs":(2,4,4),
}

SITE_PERMS=(
    (0,1,2,3),
    (2,0,3,1),
    (3,2,0,1),
)

def map_structure(structure,p):
    return tuple(sorted(
        tuple(sorted(tuple(p[i] for i in word) for word in unit))
        for unit in structure
    ))

def labels_for(structure):
    signatures=[]
    rows=[]
    for values in product(ALPHABET,repeat=N):
        rows.append(tuple(values))
        signatures.append(Kernel.structure_signature(tuple(values),structure))
    ids={}
    labels=[]
    for sig in signatures:
        if sig not in ids:
            ids[sig]=len(ids)
        labels.append(ids[sig])
    return rows,labels

def make_world(name,variant=0,*,relabel=False,incomplete=False):
    structure=map_structure(HIDDEN[name],SITE_PERMS[int(variant)])
    rows,labels=labels_for(structure)
    out=[]
    for values,y in zip(rows,labels):
        if relabel:
            y=13+7*int(y)
        out.append(Row(tuple(values),None if incomplete else int(y)))
    return World(f"{name}_v{variant}"+("_rel" if relabel else ""),tuple(out),not incomplete)

WORLDS={(name,v):make_world(name,v) for name in HIDDEN for v in range(3)}
RELABELLED={name:make_world(name,0,relabel=True) for name in HIDDEN}
INCOMPLETE=make_world("oriented_pair",0,incomplete=True)
