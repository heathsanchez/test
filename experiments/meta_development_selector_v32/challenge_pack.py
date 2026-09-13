from __future__ import annotations
from basis import World
from itertools import product

RECORDS=tuple((((a,b,c),(d,e,f))) for a,b,c,d,e,f in product((0,1),repeat=6))
def bit(r,off,ch):return int(r[off][ch])
def world(name, fn, *, complete=True, current=None):
    ys=tuple(int(fn(r))&1 for r in RECORDS)
    cur=tuple(int(current(r)) for r in RECORDS) if current else None
    return World(name,RECORDS,ys,complete,cur)

TRAIN_PAIR_A=world("w01",lambda r:bit(r,0,0)^bit(r,0,1))
TRAIN_PAIR_B=world("w02",lambda r:bit(r,0,1)^bit(r,0,2))
TRAIN_LAG_A=world("w03",lambda r:bit(r,1,0))
TRAIN_LAG_B=world("w04",lambda r:bit(r,1,2))

HIDDEN={
 "no_growth": world("w10",lambda r:0),
 "present_refinement": world("w11",lambda r:bit(r,0,2)),
 "historical_access": world("w12",lambda r:bit(r,1,1)),
 "pairwise_relation": world("w13",lambda r:bit(r,0,0)^bit(r,0,2)),
 "higher_composition": world("w14",lambda r:bit(r,0,0)^bit(r,0,1)^bit(r,0,2)),
 "context_conditioned": world("w15",lambda r:bit(r,0,0)^bit(r,0,1)),
 "intervention_conditioned": world("w16",lambda r:bit(r,0,1)^bit(r,0,2)),
 "joint_carrier": world("w17",lambda r:1^(bit(r,0,0)^bit(r,0,2))),
 "mixed_trace_relation": world("w18",lambda r:bit(r,0,1)^bit(r,1,2)),
 "contraction": world("w19",lambda r:bit(r,0,0)^bit(r,0,1),current=lambda r:2*bit(r,0,0)+bit(r,0,1)),
}
EXPECTED_COST={
 "no_growth":[1,0,0,0,0],
 "present_refinement":[2,1,0,0,0],
 "historical_access":[2,1,0,0,1],
 "pairwise_relation":[2,2,1,1,0],
 "higher_composition":[2,3,2,2,0],
 "context_conditioned":[2,2,1,1,0],
 "intervention_conditioned":[2,2,1,1,0],
 "joint_carrier":[2,2,1,1,0],
 "mixed_trace_relation":[2,2,1,1,1],
 "contraction":[2,2,1,1,0],
}

def _rec(a,b,c,d,e,f):return ((a,b,c),(d,e,f))
ACTIVE_RECORDS=tuple(_rec(a,a,c,d,e,f) for a,c,d,e,f in product((0,1),repeat=5))
ACTIVE=World("w20",ACTIVE_RECORDS,tuple(r[0][1] for r in ACTIVE_RECORDS))
ACTIVE_POOL=(
 _rec(0,1,0,0,0,0),
 _rec(1,0,1,1,0,1),
 _rec(0,0,1,0,1,0),
)
def active_oracle(r):return r[0][1]
INCOMPLETE=World("w99",RECORDS,tuple(0 for _ in RECORDS),False)
