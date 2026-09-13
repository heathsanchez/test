from __future__ import annotations
from itertools import product

from basis import Row, World

N=5
EDGES=tuple((i,j) for i in range(N) for j in range(i+1,N))
EDGE_INDEX={e:k for k,e in enumerate(EDGES)}

def mask_from_edges(items):
    m=0
    for i,j in items:
        a,b=sorted((int(i),int(j)))
        m |= 1<<EDGE_INDEX[(a,b)]
    return m

LATENT={
    "empty":mask_from_edges([]),
    "single":mask_from_edges([(0,1)]),
    "matching":mask_from_edges([(0,1),(2,3)]),
    "path2":mask_from_edges([(0,1),(1,2)]),
    "path3":mask_from_edges([(0,1),(1,2),(2,3)]),
    "star":mask_from_edges([(0,1),(0,2),(0,3),(0,4)]),
    "cycle5":mask_from_edges([(0,1),(1,2),(2,3),(3,4),(4,0)]),
}

PERMS=(
    (0,1,2,3,4),
    (2,4,1,0,3),
    (4,2,0,3,1),
)

EXPECTED_EDGES={
    "empty":0,
    "single":1,
    "matching":2,
    "path2":2,
    "path3":3,
    "star":4,
    "cycle5":5,
}

def permute_mask(mask,p):
    out=0
    for k,(i,j) in enumerate(EDGES):
        if (int(mask)>>k)&1:
            a,b=sorted((int(p[i]),int(p[j])))
            out |= 1<<EDGE_INDEX[(a,b)]
    return out

def adjacency(mask):
    a=[[] for _ in range(N)]
    for k,(i,j) in enumerate(EDGES):
        if (int(mask)>>k)&1:
            a[i].append(j); a[j].append(i)
    return tuple(tuple(sorted(x)) for x in a)

def signature(values,mask):
    a=adjacency(mask)
    rows=[]
    for i,ns in enumerate(a):
        rows.append((int(values[i]),len(ns),sum(int(values[j]) for j in ns)))
    return tuple(sorted(rows))

def make_world(name,variant=0,*,relabel=False,incomplete=False):
    hidden=permute_mask(LATENT[name],PERMS[int(variant)])
    sigs=[]
    raw=[]
    for values in product((0,1),repeat=N):
        s=signature(tuple(values),hidden)
        sigs.append(s)
        raw.append(tuple(values))
    ids={}
    labels=[]
    for s in sigs:
        if s not in ids:
            ids[s]=len(ids)
        y=ids[s]
        if relabel:
            y=7*y+11
        labels.append(y)
    rows=tuple(
        Row(values,None if incomplete else int(y))
        for values,y in zip(raw,labels)
    )
    return World(f"{name}_v{variant}"+("_rel" if relabel else ""),rows,not incomplete)

WORLDS={(name,v):make_world(name,v) for name in LATENT for v in range(len(PERMS))}
RELABELLED={name:make_world(name,0,relabel=True) for name in LATENT}
INCOMPLETE=make_world("single",0,incomplete=True)
