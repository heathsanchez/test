#!/usr/bin/env python3
"""Independent first coefficient-return audit.

For each positive odd source n, follow the actual shortcut orbit WITHOUT
stopping at descent. Let q_k be the number of odd shortcut steps. Define k as
the first positive depth after the initial supercritical event at which
2^k > 3^q_k. Test the exact affine descent margin
  M = (2^k-3^q_k)n - B_k = 2^k(n-T^k(n)).
No descent information is used to choose k.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"source_product_v1"))
from source_product import initial,advance
BITS=22; DEPTH=4096
bad=[]; no_return=[]; minpos=None; records=[]
for n in range(3,1<<BITS,2):
 s=initial(n); seen_super=False; ret=None
 for _ in range(DEPTH):
  s=advance(s)
  A=3**s.odd_steps; two=2**s.depth
  if A>two: seen_super=True
  if seen_super and two>A:
   D=two-A
   M=D*n-s.intercept
   exact=two*(n-s.endpoint)
   if M!=exact: raise AssertionError((n,s.depth,M,exact))
   ret=(s.depth,s.odd_steps,s.endpoint,D,s.intercept,M)
   break
 if ret is None:
  if len(no_return)<40:no_return.append(n)
  continue
 k,q,y,D,B,M=ret
 if M<=0 and len(bad)<40:bad.append({"n":n,"k":k,"q":q,"y":y,"D":str(D),"B":str(B),"M":str(M)})
 if M>0 and (minpos is None or M<minpos[0]):minpos=(M,n,k,q,y)
 if not records or k>records[-1]["k"]:records.append({"n":n,"k":k,"q":q,"y":y,"M":str(M)})
out={"schema":"COLLATZ_FIRST_COEFFICIENT_RETURN_V1","source_bits":BITS,"depth_limit":DEPTH,
 "tested_odd_sources":(1<<(BITS-1))-1,"counterexamples":bad,
 "no_return_count_sampled":len(no_return),"no_return_sample":no_return,
 "minimum_positive_margin":None if minpos is None else {"M":str(minpos[0]),"n":minpos[1],"k":minpos[2],"q":minpos[3],"y":minpos[4]},
 "record_return_depths":records[-40:],
 "status":"BOUNDED_CANDIDATE_SURVIVES" if not bad and not no_return else ("AFFINE_MARGIN_COUNTEREXAMPLE" if bad else "COEFFICIENT_RETURN_RESIDUAL"),
 "theorem_target":"universally prove existence of first coefficient return and M>0 there",
 "global_collatz":"UNKNOWN"}
print(json.dumps(out,indent=2))
