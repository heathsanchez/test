#!/usr/bin/env python3
from __future__ import annotations

from basis import RelationalWorld


def undirected_cycle(n:int):
    R=[[0]*n for _ in range(n)]
    for i in range(n):
        for j in ((i-1)%n,(i+1)%n):
            R[i][j]=1
    return tuple(tuple(row) for row in R)


def relabel_relation(R,perm):
    n=len(R)
    inv=[0]*n
    for i,j in enumerate(perm):
        inv[j]=i
    out=[[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            out[i][j]=R[inv[i]][inv[j]]
    return tuple(tuple(row) for row in out)


CYCLE6=undirected_cycle(6)

WORLD_A=RelationalWorld(
    n=6,
    relations=(CYCLE6,),
    consequences=((0,),)*6,
    complete=True,
    world_id="anonymous_relational_a",
)

WORLD_B=RelationalWorld(
    n=6,
    relations=(CYCLE6,),
    consequences=((0,),)*6,
    complete=True,
    world_id="anonymous_relational_b",
)

PERM=(2,5,1,4,0,3)
WORLD_RELABEL=RelationalWorld(
    n=6,
    relations=(relabel_relation(CYCLE6,PERM),),
    consequences=((0,),)*6,
    complete=True,
    world_id="hidden_relabeling",
)

# Directed chain: same carrier/interface, generally identity only.
CHAIN=tuple(
    tuple(1 if j==i+1 else 0 for j in range(6))
    for i in range(6)
)
WORLD_WRONG=RelationalWorld(
    n=6,
    relations=(CHAIN,),
    consequences=((0,),)*6,
    complete=True,
    world_id="asymmetric_chain",
)

# Two disjoint anonymous 3-cliques: different nontrivial automorphism structure.
R2=[[0]*6 for _ in range(6)]
for block in ((0,1,2),(3,4,5)):
    for i in block:
        for j in block:
            if i!=j:
                R2[i][j]=1
WORLD_HET=RelationalWorld(
    n=6,
    relations=(tuple(tuple(row) for row in R2),),
    consequences=((0,),)*6,
    complete=True,
    world_id="two_anonymous_components",
)

# Same structural relation as WORLD_A, but consequence distinguishes one point.
WORLD_MARKED=RelationalWorld(
    n=6,
    relations=(CYCLE6,),
    consequences=((1,), (0,), (0,), (0,), (0,), (0,)),
    complete=True,
    world_id="consequence_breaks_structure",
)

WORLD_INCOMPLETE=RelationalWorld(
    n=6,
    relations=(CYCLE6,),
    consequences=((0,),)*6,
    complete=False,
    world_id="incomplete_authority",
)
