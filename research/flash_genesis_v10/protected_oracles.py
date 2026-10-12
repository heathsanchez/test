"""Frozen protected independence-oracle families for FLASH Genesis V10.
No candidate repair policy, target-rank labels, or synthesis implementation.
These functions are supplied source semantics, not discovered physical affordances.
"""
from dataclasses import dataclass
from itertools import combinations

@dataclass(frozen=True)
class System:
    name: str
    n: int
    independent: object

def bits(mask, n):
    return [i for i in range(n) if mask >> i & 1]

def gf_rank(vectors, prime):
    m=[list(v) for v in vectors]
    if not m: return 0
    pivots=0
    for col in range(len(m[0])):
        pos=next((r for r in range(pivots,len(m)) if m[r][col]%prime),None)
        if pos is None:continue
        m[pivots],m[pos]=m[pos],m[pivots]
        inv=pow(m[pivots][col]%prime,-1,prime)
        m[pivots]=[(v*inv)%prime for v in m[pivots]]
        for r in range(len(m)):
            if r==pivots:continue
            factor=m[r][col]%prime
            m[r]=[(a-factor*b)%prime for a,b in zip(m[r],m[pivots])]
        pivots+=1
        if pivots==len(m):break
    return pivots

def forest_ok(edges, mask, nv):
    parent=list(range(nv))
    def find(x):
        while parent[x]!=x:
            x=parent[x]
        return x
    for i in bits(mask,len(edges)):
        a,b=edges[i];ra,rb=find(a),find(b)
        if ra==rb:return False
        parent[ra]=rb
    return True

def transversal_ok(neighbours,mask,nright):
    chosen=bits(mask,len(neighbours))
    occupied=[-1]*nright
    def augment(u,seen):
        for v in neighbours[u]:
            if seen[v]:continue
            seen[v]=True
            if occupied[v]<0 or augment(occupied[v],seen):
                occupied[v]=u
                return True
        return False
    return all(augment(u,[False]*nright) for u in chosen)

def systems():
    e4=list(combinations(range(4),2))
    colors=[0,1,0,2,1,3,2,3]
    vec3=[(1,0,0),(0,1,0),(1,1,0),(0,0,1),
          (1,0,1),(0,1,1),(1,1,1)]
    neighbors=[(0,1),(1,2),(2,3),(0,3),(1,3,4),(0,2,4),(3,4)]
    mixed_edges=[(0,1),(1,2),(0,2),(2,3)]
    weights=[3,2,2,1,1,1]
    return [
        System('graphic_k4',len(e4),lambda mask:forest_ok(e4,mask,4)),
        System('uniform_u3_8',8,lambda mask:mask.bit_count()<=3),
        System('partition_colors',8,lambda mask:len({colors[i] for i in bits(mask,8)})==mask.bit_count()),
        System('linear_gf3',len(vec3),lambda mask:gf_rank([vec3[i] for i in bits(mask,len(vec3))],3)==mask.bit_count()),
        System('transversal_matching',len(neighbors),lambda mask:transversal_ok(neighbors,mask,5)),
        System('graphic_plus_uniform',8,lambda mask:forest_ok(mixed_edges,mask&15,4) and (mask>>4).bit_count()<=2),
        System('negative_nonmatroid_knapsack',len(weights),lambda mask:sum(weights[i] for i in bits(mask,len(weights)))<=4)
    ]
