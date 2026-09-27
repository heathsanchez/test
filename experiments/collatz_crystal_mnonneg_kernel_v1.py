#!/usr/bin/env python3
"""Crystal exact M>=0 viability-kernel probe on source-product transitions.

This is deliberately a bounded falsifier/discovery object.  Nodes are exact
canonical source-product states reached from actual odd sources; an internal
edge is retained only while the exact joint margin M=2^j(Y-R) is nonnegative.
Descent (Y<R), terminal coefficient crossing, and n=1 are exits.

The compiler begins from the coarsest protected future and admits exact
separators only if they change that future partition. Empty bounded kernel is
not a universal Collatz theorem; a surviving cycle is an exact residual.
"""
from __future__ import annotations
import json
from collections import defaultdict
from collatz_live_origin_bridge_v1 import language_counts
from collatz_crystal_future_quotient_v1 import compile_with_separators

BITS=18; DEPTH=96
qmin,_,_=language_counts(DEPTH)

def step(s):
 n,j,q,R,Y=s
 bit=Y&1
 lift=(bit-Y)&1
 Rp=R+lift*(1<<j)
 z=Y+(3**q)*lift
 Yp=(3*z+1)//2 if bit else z//2
 return (n,j+1,q+bit,Rp,Yp)

occ=[]; bykey={}; edges=defaultdict(set); exits=set()
for n in range(1,1<<BITS,2):
 s=(n,0,0,0,0)
 # canonical stateAt recurrence; source residue becomes n mod 2^j.
 for _ in range(DEPTH):
  t=step(s); nn,j,q,R,Y=t
  # Exact protected exit: trivial source, actual canonical descent, or
  # coefficient crossing. We retain only M>=0/no-exit continuations.
  crossing=q<qmin[j]
  descent=(R>0 and Y<R)
  terminal=(n==1)
  key=(n,j,q,R,Y)
  tkey=(nn,j,q,R,Y)
  if crossing or descent or terminal:
   exits.add(key)
   break
  edges[key].add(tkey)
  s=t

keys=set(edges)|{t for vs in edges.values() for t in vs}|exits
for i,k in enumerate(sorted(keys)):
 n,j,q,R,Y=k
 bykey[k]=str(i)
for k in sorted(keys):
 n,j,q,R,Y=k
 occ.append({
  "id":bykey[k],
  "next":[bykey[t] for t in edges.get(k,set()) if t in bykey],
  "exit":k in exits,
  "parity":Y&1,
  "q_excess":q-qmin[j] if j else q,
  "source_bits":n.bit_length(),
  "R_zero":R==0,
  "M_zero":Y==R,
  "j_mod_125":j%125,
 })
result=compile_with_separators(
 occ,
 base_fields=[],
 separator_bank=["M_zero","parity","q_excess","R_zero","j_mod_125","source_bits"])
print(json.dumps({"schema":"COLLATZ_CRYSTAL_MNONNEG_KERNEL_V1",
 "source_bits":BITS,"depth":DEPTH,"nodes":len(keys),"exits":len(exits),
 "compiler":result,
 "claim_boundary":"bounded actual-source exact-state viability graph only",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"},indent=2))
