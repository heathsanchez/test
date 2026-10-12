"""Pre-learner finite opaque source-oracle fixtures for FLASH V15.
Only calls to independent(mask) are exposed to the source compiler.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class SourceFamily:
    name: str
    n: int
    independent: object
    hereditary_claim: bool

def bits(m,n):
    return [i for i in range(n) if m>>i&1]

def graph_ok(m,edges):
    return all(not (m>>a&1 and m>>b&1) for a,b in edges)

def no_overlap(m,sets):
    seen=0
    for i in bits(m,len(sets)):
        if seen&sets[i]:return False
        seen|=sets[i]
    return True

def cap_ok(m,ws,limit):
    return sum(ws[i] for i in bits(m,len(ws)))<=limit

def forbidden_ok(m,patterns):
    return all((m&p)!=p for p in patterns)

def families():
    edges=[(0,1),(0,2),(0,3),(3,4),(4,5),(2,5)]
    sets=[0b111,0b001,0b010,0b100,0b110,0b011]
    patterns=[0b00101,0b01011,0b11000,0b10010]
    weights=[4,3,2,2,1,3]
    return [
        SourceFamily("graph_conflicts",6,lambda m:graph_ok(m,edges),True),
        SourceFamily("disjoint_resources",6,lambda m:no_overlap(m,sets),True),
        SourceFamily("capacity_nonnegative",6,lambda m:cap_ok(m,weights,6),True),
        SourceFamily("declared_forbidden_hyperedges",5,lambda m:forbidden_ok(m,patterns),True),
        SourceFamily("negative_even_cardinality",5,lambda m:m.bit_count()%2==0,False),
        SourceFamily("negative_nonempty",5,lambda m:m!=0 and m.bit_count()<=2,False),
    ]
