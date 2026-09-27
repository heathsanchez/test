#!/usr/bin/env python3
"""Crystal: strong reverse coverage sufficient under hard-crossing y < 4n/3."""
import json
import collatz_reverse_predecessor_tree as pred
rows=[]
for Q in range(1,15):
 cs=pred.enumerate_first_contractions(Q); M=3**Q
 killed=bytearray(M); selected=[]
 for c in cs:
  # p=(a*y-c)/d. If y<4n/3, a/d <=3/4 implies p<n uniformly.
  if 4*c.a>3*c.d: continue
  add=0
  for r in range(c.residue,M,c.d):
   if r%3!=1: continue # hard large-source endpoint is 1 mod 3
   if not killed[r]: killed[r]=1;add+=1
  if add:selected.append((c.word,c.d,c.residue,add,c.a,c.c))
 universe=[r for r in range(1,M,3)]
 live=[r for r in universe if not killed[r]]
 rows.append({"Q":Q,"universe":len(universe),"killed":len(universe)-len(live),
  "live":len(live),"first_live":live[:30],"selected":selected[:30]})
print(json.dumps({"schema":"COLLATZ_CRYSTAL_HARD_CROSSING_STRONG_REVERSE_COVER_V0",
 "criterion":"4*a <= 3*d guarantees p<n from y<4n/3",
 "rows":rows,"global_collatz":"UNKNOWN"},indent=2))
