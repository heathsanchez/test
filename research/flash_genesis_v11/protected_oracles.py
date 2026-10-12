"""Prospective FLASH Genesis V11 protected family source, frozen before learner code.

The source learner MUST NOT import this module. Application receives only
is_independent(mask) and n; protected result is independently brute-forced.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Family:
    name:str
    n:int
    independent:object
    category:str

def subset(mask,n):
    return (i for i in range(n) if (mask>>i)&1)

def no_conflicts(mask,pairs):
    return all(not(mask>>i&1 and mask>>j&1) for i,j in pairs)

def costs_within(mask,weights,caps):
    return all(sum(weights[i][k] for i in subset(mask,len(weights)))<=cap
               for k,cap in enumerate(caps))

def disjoint_resources(mask,items):
    taken=0
    for i in subset(mask,len(items)):
        if taken&items[i]:return False
        taken|=items[i]
    return True

def no_forbidden(mask,patterns):
    return all(mask&pat!=pat for pat in patterns)

def forest(mask,edges,vertices):
    parent=list(range(vertices))
    def root(x):
        while parent[x]!=x:x=parent[x]
        return x
    for i in subset(mask,len(edges)):
        a,b=edges[i];u,v=root(a),root(b)
        if u==v:return False
        parent[u]=v
    return True

def protected_families():
    star=[(0,i) for i in range(1,5)]+[(4,5),(5,6),(6,7),(7,8)]
    weights=[(5,5),(2,1),(1,2),(2,2),(1,1),(2,1),(1,2),(1,1),(2,1)]
    intervals=[(0,12),(0,2),(2,4),(4,6),(6,8),(8,10),(10,12),(1,3),(7,9)]
    clashes=[(i,j) for i in range(9) for j in range(i+1,9)
             if intervals[i][0]<intervals[j][1] and intervals[j][0]<intervals[i][1]]
    items=[0b111111,0b000001,0b000010,0b000100,0b001000,0b010000,0b100000,0b000011,0b001100]
    patterns=[(1<<0)|(1<<i) for i in range(1,5)]
    patterns+= [(1<<4)|(1<<5)|(1<<6),(1<<6)|(1<<7)|(1<<8)]
    edges=[(0,1),(1,2),(2,3),(0,2),(3,4),(4,5),(5,6),(3,6),(0,6)]
    return [
        Family("protected_conflict_star",9,lambda m:no_conflicts(m,star),"hereditary_nonmatroid"),
        Family("protected_two_resource",9,lambda m:costs_within(m,weights,(6,6)),"hereditary_nonmatroid"),
        Family("protected_interval_schedule",9,lambda m:no_conflicts(m,clashes),"hereditary_nonmatroid"),
        Family("protected_set_packing",9,lambda m:disjoint_resources(m,items),"hereditary_nonmatroid"),
        Family("protected_forbidden_hyperedges",9,lambda m:no_forbidden(m,patterns),"hereditary_nonmatroid"),
        Family("continuity_uniform_matroid",9,lambda m:m.bit_count()<=4,"matroid"),
        Family("continuity_graphic_matroid",9,lambda m:forest(m,edges,7),"matroid"),
        Family("negative_even_parity",8,lambda m:m.bit_count()%2==0,"nonhereditary"),
        Family("negative_empty_infeasible",8,lambda m:m!=0 and m.bit_count()<=2,"nonhereditary"),
    ]

def frozen_changed_objectives():
    """Third-generation goal changed from cardinality to total utility.
    These fixtures must not influence V11 source learning.
    """
    star=[(0,i) for i in range(1,5)]+[(4,5),(5,6),(6,7),(7,8)]
    return [
        ("future_weighted_conflict",9,
         lambda m:no_conflicts(m,star),
         (1,1,1,1,1,1,1,1,15)),
        ("future_weighted_capacity",9,
         lambda m:costs_within(m,[(5,5),(2,1),(1,2),(2,2),(1,1),(2,1),(1,2),(1,1),(2,1)],(6,6)),
         (15,3,2,7,5,2,4,3,2)),
    ]
