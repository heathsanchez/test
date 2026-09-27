#!/usr/bin/env python3
"""Canonical inequality audit for singleton live sources.

At first coefficient crossing d, exact affine form is
  2^d y = 3^q n + b, q<qmin[d].
For each nonterminal singleton source, record the normalized bias threshold
needed for y<n:
  b < (2^d-3^q)n.
Mine whether singleton status forces this through a simple source-prefix gap.
Discovery only; emit margin and separator.
"""
import json
from collatz_live_origin_bridge_v1 import language_counts,first_crossing
BITS=20;DEPTH=512
qmin,F,H=language_counts(DEPTH)
def affine(n,d):
 y=n;q=0;b=0
 for k in range(d):
  if y&1:
   b=3*b+(1<<k);q+=1;y=(3*y+1)//2
  else:y//=2
 assert (1<<d)*y==(3**q)*n+b
 return y,q,b
# recover all unique singleton sources
cross={n:first_crossing(n,qmin) for n in range(1,1<<BITS,2)}
sources=set()
for m in range(1,BITS+1):
 pool=[n for n in cross if n<(1<<m)]
 for j in range(1,DEPTH):
  live=[n for n in pool if cross[n] is None or cross[n][0]>j]
  if len(live)==1:sources.add(live[0])
rows=[];bad=[]
for n in sorted(sources):
 z=cross[n]
 if n==1:rows.append({"n":1,"terminal":True});continue
 if z is None:bad.append({"n":n,"kind":"unresolved"});continue
 d=z[0];y,q,b=affine(n,d);margin=(1<<d)-(3**q)
 row={"n":n,"d":d,"y":y,"q":q,"b":b,"coefficient_margin":margin,
      "descent_budget":margin*n-b,"descending":y<n,
      "q_deficit":qmin[d]-q}
 rows.append(row)
 if not y<n:bad.append(row)
result={"schema":"COLLATZ_CRYSTAL_SINGLETON_AFFINE_MARGIN_V1",
 "sources":len(sources),"violations":len(bad),"first_violations":bad[:20],
 "rows":rows,
 "candidate":"singleton status must force affine bias b below coefficient margin (2^d-3^q)n at first crossing",
 "universal":"NOT_PROVED","global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
