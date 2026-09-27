#!/usr/bin/env python3
"""Search for a minimum-sufficient block contraction of live-origin envelope debt.

Exact finite diagnostic. For each dyadic origin window and each start depth j,
find the smallest b<=B such that the actual live count contracts enough relative
to the target envelope ratio E_{j+b}/E_j. Zero-exit single steps are allowed.
If a uniform small b appears, emit the exact worst block as the theorem target.
"""
import json
from collatz_live_origin_bridge_v1 import language_counts, first_crossing
BITS=20; DEPTH=512; BMAX=32
qmin,F,_=language_counts(DEPTH)
hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for n in range(1,1<<BITS,2):
    z=first_crossing(n,qmin)
    if z:
        j,_,_=z; hist[j][n.bit_length()]+=1
C=[[0]*(BITS+1) for _ in range(DEPTH+1)]
P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for j in range(1,DEPTH+1):
  for m in range(1,BITS+1): C[j][m]=C[j][m-1]+hist[j][m]
for m in range(1,BITS+1):
  P[0][m]=1<<(m-1)
  for j in range(1,DEPTH+1): P[j][m]=P[j-1][m]-C[j][m]

# E_j(m) = F_j * 2^(1+floor(6j/125)+m-j).
# Need P_{j+b}/P_j <= E_{j+b}/E_j.
# Cross multiply exactly; powers of two are shifted to avoid rationals.
def block_good(j,b,m):
    if not P[j][m]: return True
    a=P[j+b][m]*F[j]
    d=P[j][m]*F[j+b]
    # inequality a/d <= 2^(floor6diff-b)
    e=((6*(j+b))//125)-((6*j)//125)-b
    if e>=0:return a <= (d<<e)
    return (a<<(-e)) <= d

rows=[]; no_block=[]; worst_b=0; worst=None
for j in range(60,DEPTH-BMAX+1):
  for m in range(1,BITS+1):
    if not P[j][m]:continue
    found=None
    for b in range(1,BMAX+1):
      if block_good(j,b,m):
        found=b;break
    if found is None:no_block.append({"j":j,"m":m,"live":P[j][m]})
    else:
      if found>worst_b:
        worst_b=found;worst={"j":j,"m":m,"live":P[j][m],"block":found,
          "live_after":P[j+found][m],"exits_in_block":P[j][m]-P[j+found][m]}
      rows.append((j,m,found))
# Adversarial record-survivor resource extraction.
# For each live state define debt numerator/denominator D=P*2^j/(F*2^(1+floor(6j/125)+m)).
# A universal proof may use the natural live mass P as the well-founded resource
# provided every nonempty state has a bounded future block with a strict loss.
record=[]
for j in range(60,DEPTH-BMAX+1):
  for m in range(1,BITS+1):
    if not P[j][m]: continue
    life=0
    while j+life<=DEPTH and P[j+life][m]:
      life+=1
    exits21=P[j][m]-P[min(DEPTH,j+21)][m]
    debt_num=P[j][m]<<j
    debt_den=F[j] << (1+(6*j)//125+m)
    record.append({"survival":life,"j":j,"m":m,"live":P[j][m],
      "exits21":exits21,"debt_num":str(debt_num),"debt_den":str(debt_den)})
record.sort(key=lambda r:(-r["survival"],-r["j"],-r["m"]))
result={"schema":"COLLATZ_LIVE_ORIGIN_BLOCK_CONTRACTION_V0",
 "source_bits":BITS,"depth":DEPTH,"max_block":BMAX,
 "checked_states":len(rows)+len(no_block),"states_without_block":len(no_block),
 "first_no_block":no_block[:20],"max_minimum_block":worst_b,"worst_block":worst,
 "status":"FINITE_UNIFORM_BLOCK_FOUND" if not no_block else "FINITE_BLOCK_OBSTRUCTION",
 "theorem_target":("prove the same block contraction from exact carry state for all depths/windows"
                   if not no_block else "refine consequential state using first no-block separator"),
 "record_survivors":record[:40],
 "resource_candidate":{"name":"live_mass","value":"P_j(X)","order":"Nat","progress_obligation":"for every nonempty actual live-origin state, some lawful finite block has P strictly decrease; envelope contraction supplies quantitative strengthening"},
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
