"""V12 PROTECTED weighted environments, frozen before any V12 learner code.

Sources are synthetic mathematical oracles with no claimed physical semantics.
Protected verifier must check source-derived policy SHA before importing this file.
"""
from dataclasses import dataclass
from itertools import combinations

@dataclass(frozen=True)
class WeightedFamily:
    name:str
    n:int
    independent:object
    weights:tuple
    score:object
    applicability:str

def bits(mask,n):
    return (i for i in range(n) if mask>>i&1)

def score_additive(mask,w):
    return sum(w[i] for i in bits(mask,len(w)))

def no_conflict(mask,pairs):
    return all(not(mask>>a&1 and mask>>b&1) for a,b in pairs)

def cap_feasible(mask,weights,limits):
    return all(sum(weights[i][k] for i in bits(mask,len(weights)))<=limit for k,limit in enumerate(limits))

def disjoint(mask,resources):
    occupied=0
    for i in bits(mask,len(resources)):
        if occupied&resources[i]:return False
        occupied|=resources[i]
    return True

def forest(mask,edges,vertices):
    parent=list(range(vertices))
    def find(x):
        while parent[x]!=x:x=parent[x]
        return x
    for i in bits(mask,len(edges)):
        u,v=edges[i];a,b=find(u),find(v)
        if a==b:return False
        parent[a]=b
    return True

def families():
    intervals=[(0,12),(0,2),(2,4),(4,6),(6,8),(8,10),(10,12),(1,3),(9,11)]
    overlaps=[(i,j) for i in range(9) for j in range(i+1,9)
        if intervals[i][0]<intervals[j][1] and intervals[j][0]<intervals[i][1]]
    resource_items=[0b111111,0b000001,0b000010,0b000100,0b001000,0b010000,0b100000,0b000011,0b110000]
    capacity=[(6,5),(3,2),(2,3),(1,2),(2,1),(1,1),(2,2),(3,1),(1,3)]
    conflict=[(0,i) for i in range(1,5)]+[(4,5),(5,6),(6,7),(7,8),(1,8)]
    edges=[(0,1),(1,2),(2,0),(2,3),(3,4),(4,2),(4,5),(5,6),(6,4)]
    forbidden=[(1<<0)|(1<<i) for i in range(1,5)]
    forbidden += [(1<<3)|(1<<4)|(1<<5),(1<<6)|(1<<7)|(1<<8)]
    specs=[
      ('weighted_intervals',9,lambda m:no_conflict(m,overlaps),(14,2,8,3,6,8,4,5,7)),
      ('weighted_set_packing',9,lambda m:disjoint(m,resource_items),(12,5,2,7,3,4,8,2,2)),
      ('weighted_two_capacity',9,lambda m:cap_feasible(m,capacity,(8,8)),(14,2,4,8,3,4,9,3,5)),
      ('weighted_conflict',9,lambda m:no_conflict(m,conflict),(13,1,2,3,3,2,3,5,12)),
      ('weighted_graphic',9,lambda m:forest(m,edges,7),(1,5,8,9,2,10,3,4,12)),
      ('weighted_uniform',9,lambda m:m.bit_count()<=3,(1,7,2,15,8,3,10,4,6)),
      ('weighted_forbidden',9,lambda m:all(m&f!=f for f in forbidden),(15,2,3,5,6,3,12,4,7)),
    ]
    valid=[WeightedFamily(name,n,p,w,lambda m,w=w:score_additive(m,w),'POSITIVE_MODULAR') for name,n,p,w in specs]
    nonmod_weights=(1,2,3,4,5,6,7,8)
    bad_nonmod=WeightedFamily('negative_pair_synergy',8,
       lambda m:m.bit_count()<=4,
       nonmod_weights,
       lambda m,w=nonmod_weights:score_additive(m,w)+(20 if ((m&3)==3) else 0),
       'NONMODULAR')
    negative_w=(3,2,-5,6,1,4,2,7)
    bad_negative=WeightedFamily('negative_weight_scope',8,
       lambda m:m.bit_count()<=4,
       negative_w,
       lambda m,w=negative_w:score_additive(m,w),'NEGATIVE_WEIGHT')
    return valid+[bad_nonmod,bad_negative]
