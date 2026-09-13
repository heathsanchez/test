from __future__ import annotations
from itertools import product
from basis import World

RECORDS=tuple((((a,b,c),(d,e,f))) for a,b,c,d,e,f in product((0,1),repeat=6))
def bit(r,o,c):return int(r[o][c])
def op(code,a,b):return (int(code)>>((int(a)<<1)|int(b)))&1
def world(name,fn,*,complete=True,current=None):
    ys=tuple(int(fn(r))&1 for r in RECORDS)
    cur=tuple(int(current(r)) for r in RECORDS) if current else None
    return World(name,RECORDS,ys,complete,cur)

TRAIN_PAIR_A=world('t31',lambda r:op(8,bit(r,0,0),bit(r,0,1)))
TRAIN_PAIR_B=world('t32',lambda r:op(14,bit(r,0,1),bit(r,0,2)))
TRAIN_LAG_A=world('t33',lambda r:bit(r,1,0))
TRAIN_LAG_B=world('t34',lambda r:1^bit(r,1,2))
TRAIN_MIX_A=world('t35',lambda r:op(8,bit(r,0,0),bit(r,1,1)))
TRAIN_MIX_B=world('t36',lambda r:op(14,bit(r,0,2),bit(r,1,0)))

HIDDEN={
 'no_growth':world('h40',lambda r:1),
 'present_refinement':world('h41',lambda r:1^bit(r,0,1)),
 'historical_access':world('h42',lambda r:bit(r,1,2)),
 'heldout_pair_xor':world('h43',lambda r:op(6,bit(r,0,0),bit(r,0,2))),
 'heldout_mixed_xor':world('h44',lambda r:op(6,bit(r,0,1),bit(r,1,2))),
 'higher_composition':world('h45',lambda r:bit(r,0,0)^bit(r,0,1)^bit(r,0,2)),
 'context_style':world('h46',lambda r:op(11,bit(r,0,0),bit(r,0,1))),
 'action_style':world('h47',lambda r:op(7,bit(r,0,1),bit(r,0,2))),
 'joint_style':world('h48',lambda r:op(6,bit(r,0,0),bit(r,0,2))),
 'contraction':world('h49',lambda r:op(14,bit(r,0,0),bit(r,0,1)),current=lambda r:2*bit(r,0,0)+bit(r,0,1)),
}
EXPECTED_COST={
 'no_growth':[1,0,0,0,0],
 'present_refinement':[2,1,0,0,0],
 'historical_access':[2,1,0,0,1],
 'heldout_pair_xor':[2,2,1,1,0],
 'heldout_mixed_xor':[2,2,1,1,1],
 'higher_composition':[2,3,2,2,0],
 'context_style':[2,2,1,1,0],
 'action_style':[2,2,1,1,0],
 'joint_style':[2,2,1,1,0],
 'contraction':[2,2,1,1,0],
}

def rec(a,b,c,d,e,f):return ((a,b,c),(d,e,f))
ACTIVE_RECORDS=tuple(rec(a,c,c,d,e,f) for a,c,d,e,f in product((0,1),repeat=5))
ACTIVE=World('h50',ACTIVE_RECORDS,tuple(1^r[0][2] for r in ACTIVE_RECORDS))
ACTIVE_POOL=(rec(0,0,1,0,1,0),rec(1,1,0,1,0,1),rec(0,1,1,1,1,0))
def active_oracle(r):return 1^r[0][2]
INCOMPLETE=World('h99',RECORDS,tuple(0 for _ in RECORDS),False)
