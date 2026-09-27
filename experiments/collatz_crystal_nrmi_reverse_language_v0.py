#!/usr/bin/env python3
"""NRMI Crystal probe: first-contracting reverse language along hard actual orbits.

For each hard source and Q=1..14, find the earliest orbit endpoint admitting any
exact first-contracting reverse predecessor p<n. Record whether increasing Q
strictly advances closure and the endpoint's threshold slack at the hit.
"""
import json
import collatz_reverse_predecessor_tree as pred
from collatz_live_origin_bridge_v1 import language_counts
H=2000
qmin,_,_=language_counts(H)
sources=[13421671,14378779,8088063,12132095,9280639,13774695,1126015,2252031,1689023,6206655]
def T(x): return (3*x+1)//2 if x&1 else x//2
banks={}
for Q in range(1,15):
 cs=pred.enumerate_first_contractions(Q); by={}
 for c in cs: by.setdefault(c.d,{}).setdefault(c.residue,[]).append(c)
 banks[Q]=(cs,by)
def hit(y,n,by):
 best=None
 for d,rows in by.items():
  for c in rows.get(y%d,()):
   z=c.a*y-c.c
   if z%d:continue
   p=z//d
   if 0<p<n:
    assert pred.reverse_apply(y,c.word)==p
    cand=(p,c.steps,c.word,c.odd_inverse_steps,c.d,c.residue)
    if best is None or cand<best:best=cand
 return best
rows=[]
for n in sources:
 y=n;q=0; orbit=[]
 for j in range(1,H+1):
  bit=y&1;y=T(y);q+=bit;orbit.append((j,y,q,q-qmin[j]))
  if q<qmin[j] and j>n.bit_length()+300: break
 byQ=[]
 for Q in range(1,15):
  cs,by=banks[Q]; found=None
  for j,y,q,s in orbit:
   h=hit(y,n,by)
   if h:
    found={"j":j,"y":y,"slack":s,"p":h[0],"steps":h[1],"word":h[2],
           "odd_inverse_steps":h[3],"mod":h[4],"residue":h[5]};break
  byQ.append({"Q":Q,"hit":found})
 rows.append({"n":n,"byQ":byQ})
print(json.dumps({"schema":"COLLATZ_CRYSTAL_NRMI_REVERSE_LANGUAGE_V0",
 "sources":rows,
 "target":"derive finite contracting reverse hit from nondescending affine margin + no-exit assumptions",
 "boundary":"Q<=14 finite discovery only","global_collatz":"UNKNOWN"},indent=2))
