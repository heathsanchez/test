"""V12b independent, prospectively frozen weighted-target corpus.

Created after detecting the V12 selector-filter defect, BEFORE patching the
selector. Original V12 protected results are retrospective for selector audit.
This corpus, not V12a, controls prospective promotion after repair.
"""
from dataclasses import dataclass
@dataclass(frozen=True)
class World:
    name:str
    n:int
    feasible:object
    weights:tuple
    score:object
    boundary:str

def elems(mask,n):
    return [i for i in range(n) if mask>>i&1]
def additive(mask,w):
    return sum(w[i] for i in elems(mask,len(w)))

def quota_ok(mask,groups,quota):
    return all(sum(groups[i]==g for i in elems(mask,len(groups)))<=limit
               for g,limit in quota.items())

def occupancy_ok(mask,intervals,cap):
    points=sorted(set(x for a,b in intervals for x in (a,b)))
    return all(sum(intervals[i][0]<=t<intervals[i][1] for i in elems(mask,len(intervals)))<=cap for t in points)

def disjoint(mask,resources):
    used=0
    for i in elems(mask,len(resources)):
        if used&resources[i]:return False
        used|=resources[i]
    return True

def capacity_ok(mask,w,cap):
    return sum(w[i] for i in elems(mask,len(w)))<=cap

def matchable(mask,adj,right):
    occupied=[-1]*right
    def augment(i,seen):
        for j in adj[i]:
            if j in seen:continue
            seen.add(j)
            if occupied[j]==-1 or augment(occupied[j],seen):
                occupied[j]=i
                return True
        return False
    return all(augment(i,set()) for i in elems(mask,len(adj)))

def forest(mask,edges,vertices):
    roots=list(range(vertices))
    def root(v):
        while roots[v]!=v:v=roots[v]
        return v
    for i in elems(mask,len(edges)):
        a,b=edges[i];a,b=root(a),root(b)
        if a==b:return False
        roots[a]=b
    return True

def frozen_worlds():
    groups=(0,0,1,1,2,2,3,3,3)
    quota={0:1,1:1,2:2,3:1}
    periods=((0,6),(0,2),(2,4),(4,6),(1,3),(3,5),(5,7),(6,8),(7,9))
    resources=(0b111111,0b000001,0b000010,0b000100,0b001000,0b010000,0b100000,0b001100,0b100001)
    costs=(8,5,4,2,3,6,2,1,3)
    neighbours=((0,1),(1,2),(2,3),(0,3),(3,4),(0,4),(1,4),(2,4))
    links=((0,1),(1,2),(2,0),(2,3),(3,4),(4,5),(5,3),(5,6),(6,4))
    specs=[
       ('weighted_partition_quota',9,lambda m:quota_ok(m,groups,quota),(13,2,8,9,3,2,12,4,5)),
       ('weighted_overlapping_intervals',9,lambda m:occupancy_ok(m,periods,2),(12,7,3,6,5,10,4,8,9)),
       ('weighted_hypergraph_packing',9,lambda m:disjoint(m,resources),(18,4,3,4,6,7,8,5,9)),
       ('weighted_single_capacity',9,lambda m:capacity_ok(m,costs,12),(13,11,9,4,6,10,5,2,7)),
       ('weighted_transversal',8,lambda m:matchable(m,neighbours,5),(2,7,3,9,10,4,6,12)),
       ('weighted_forest',9,lambda m:forest(m,links,7),(1,10,7,3,9,8,2,11,6)),
    ]
    valid=[World(name,n,f,w,lambda m,w=w:additive(m,w),'NONNEGATIVE_MODULAR') for name,n,f,w in specs]
    nonmod_w=(4,5,6,7,8,9,3,2)
    invalid_bonus=World('negative_nonmodular_bonus',8,
        lambda m:m.bit_count()<=4,nonmod_w,
        lambda m,w=nonmod_w:additive(m,w)+(19 if m&5==5 else 0),
        'NONMODULAR')
    neg_w=(1,2,3,-4,6,7,8,5)
    invalid_negative=World('negative_negative_coefficient',8,
        lambda m:m.bit_count()<=4,neg_w,
        lambda m,w=neg_w:additive(m,w),
        'NEGATIVE_WEIGHT')
    invalid_nonhered=World('negative_nonhereditary',8,
        lambda m:m.bit_count()%2==0,(1,2,3,4,5,6,7,8),
        lambda m:additive(m,(1,2,3,4,5,6,7,8)),
        'NONHEREDITARY')
    return valid+[invalid_bonus,invalid_negative,invalid_nonhered]
