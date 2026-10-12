"""FLASH V14 independently frozen protected consumer tasks.
All semantics are finite and locally independently checkable. Do not inspect
these tasks inside the producer or modify a rule per protected family.
"""
from dataclasses import dataclass
from itertools import combinations

@dataclass(frozen=True)
class World:
    name: str
    family: str
    n: int
    feasible: object
    weights: tuple
    score: object
    declared: str

def selected(mask,n):
    return [i for i in range(n) if mask>>i&1]

def modular(mask,weights):
    return sum(weights[i] for i in selected(mask,len(weights)))

def graph_independent(mask,conflicts):
    return all((mask&(1<<a)==0) or (mask&(1<<b)==0) for a,b in conflicts)

def capacity(mask,uses,limits):
    return all(sum(uses[i][j] for i in selected(mask,len(uses)))<=limit
               for j,limit in enumerate(limits))

def disjoint(mask,resources):
    used=0
    for j in selected(mask,len(resources)):
        if used&resources[j]:return False
        used|=resources[j]
    return True

def intervals_independent(mask,segments):
    for i,j in combinations(selected(mask,len(segments)),2):
        a,b=segments[i];c,d=segments[j]
        if a<d and c<b:return False
    return True

def forest(mask,edges,vertices):
    roots=list(range(vertices))
    def root(u):
        while roots[u]!=u:u=roots[u]
        return u
    for idx in selected(mask,len(edges)):
        x,y=edges[idx];x,y=root(x),root(y)
        if x==y:return False
        roots[x]=y
    return True

def tasks():
    conflicts=[(0,i) for i in (1,2,3,4)]+[(2,5),(5,6),(6,7),(7,8),(1,8)]
    uses=[(6,4),(1,3),(3,1),(2,2),(1,2),(2,1),(4,1),(1,1),(1,1)]
    slots=[(0,9),(0,2),(2,4),(4,6),(6,8),(8,10),(1,3),(3,5),(5,7)]
    sets=[0b111111,0b000001,0b000010,0b000100,0b001000,0b010000,0b100000,0b000011,0b100100]
    edges=[(0,1),(1,2),(2,0),(2,3),(3,4),(4,2),(4,5),(5,6),(6,4)]
    positive=[
      World('graph_conflict_A','graph',9,lambda m:graph_independent(m,conflicts),
            (15,2,2,2,3,7,5,6,8),lambda m:modular(m,(15,2,2,2,3,7,5,6,8)),'MODULAR_POSITIVE_HEREDITARY'),
      World('resource_capacity_A','resources',9,lambda m:capacity(m,uses,(7,7)),
            (17,3,4,6,5,7,3,2,1),lambda m:modular(m,(17,3,4,6,5,7,3,2,1)),'MODULAR_POSITIVE_HEREDITARY'),
      World('intervals_weighted_A','intervals',9,lambda m:intervals_independent(m,slots),
            (12,3,7,6,8,11,4,3,5),lambda m:modular(m,(12,3,7,6,8,11,4,3,5)),'MODULAR_POSITIVE_HEREDITARY'),
      World('packing_disjoint_A','packing',9,lambda m:disjoint(m,sets),
            (13,2,3,6,4,8,5,7,5),lambda m:modular(m,(13,2,3,6,4,8,5,7,5)),'MODULAR_POSITIVE_HEREDITARY'),
      World('matroid_graphic_A','matroid',9,lambda m:forest(m,edges,7),
            (3,6,1,7,10,5,4,8,9),lambda m:modular(m,(3,6,1,7,10,5,4,8,9)),'MODULAR_POSITIVE_HEREDITARY')
    ]
    false_nonmod=World('nonmodular_pair_gain','negative',8,
        lambda m:m.bit_count()<=4,(1,2,3,4,5,6,7,8),
        lambda m:modular(m,(1,2,3,4,5,6,7,8))+(19 if m&3==3 else 0),'NONMODULAR')
    neg=(1,2,3,-4,5,6,7,8)
    false_negative=World('negative_weight','negative',8,
        lambda m:m.bit_count()<=4,neg,lambda m:modular(m,neg),'NEGATIVE')
    false_nonhered=World('parity_nonhereditary','negative',8,
        lambda m:m.bit_count()%2==0,(1,2,3,4,5,6,7,8),
        lambda m:modular(m,(1,2,3,4,5,6,7,8)),'NONHEREDITARY')
    return positive+[false_nonmod,false_negative,false_nonhered]
