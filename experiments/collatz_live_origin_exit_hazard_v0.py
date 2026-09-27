#!/usr/bin/env python3
"""Exact local exit-hazard audit for the live-origin envelope.

Uses P_{j-1}(X)=P_j(X)+C_j(X). For the exact dyadic envelope
 E_j(m)=F_j*2^(1+floor(6j/125))*2^(m-j),
record whether an induction step starting at the *actual* P_{j-1} has enough
terminal loss C_j to land below E_j, and the normalized exit hazard C_j/P_{j-1}.
This is a finite diagnostic for the missing carry theorem, not a proof.
"""
import json
from collatz_live_origin_bridge_v1 import language_counts,first_crossing

BITS=20;DEPTH=512
qmin,F,_=language_counts(DEPTH)
hist=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for n in range(1,1<<BITS,2):
    z=first_crossing(n,qmin)
    if z:
        j,_,_=z;hist[j][n.bit_length()]+=1
C=[[0]*(BITS+1) for _ in range(DEPTH+1)]
P=[[0]*(BITS+1) for _ in range(DEPTH+1)]
for j in range(1,DEPTH+1):
    for m in range(1,BITS+1):C[j][m]=C[j][m-1]+hist[j][m]
for m in range(1,BITS+1):
    P[0][m]=1<<(m-1)
    for j in range(1,DEPTH+1):P[j][m]=P[j-1][m]-C[j][m]

rows=[]; failures=[]; worst=None
for j in range(60,DEPTH+1):
  for m in range(1,min(BITS,j)+1):
    prev=P[j-1][m]
    if not prev: continue
    # envelope scaled by 2^j to avoid fractions:
    # E_j*2^j = F_j * 2^(1+floor(6j/125)+m)
    Ej_num=F[j] << (1+(6*j)//125+m)
    # actual condition P_j <= E_j:
    slack=Ej_num-(P[j][m]<<j)
    ok=slack>=0
    if not ok:failures.append((j,m))
    hazard_num=C[j][m]
    rec={"j":j,"m":m,"prev":prev,"exits":hazard_num,"live":P[j][m],
         "hazard_ppm":(hazard_num*1000000)//prev,
         "envelope_slack_scaled":str(slack)}
    rows.append(rec)
    # worst = smallest relative slack E_j/P_j (integer cross-product)
    if P[j][m]:
      key=(Ej_num, P[j][m]<<j)
      if worst is None or key[0]*worst["_den"] < worst["_num"]*key[1]:
        worst={**rec,"_num":key[0],"_den":key[1]}
result={"schema":"COLLATZ_LIVE_ORIGIN_EXIT_HAZARD_V0","source_bits":BITS,
 "depth":DEPTH,"checked_windows":len(rows),"envelope_failures":len(failures),
 "worst_observed":{k:v for k,v in worst.items() if not k.startswith("_")} if worst else None,
 "status":"FINITE_LOCAL_HAZARD_SUPPORTS_ENVELOPE" if not failures else "FINITE_COUNTEREXAMPLE",
 "theorem_target":"derive sufficient C_j(X) lower bound from exact carry/P35-P37 state so P_{j-1}<=E_{j-1} implies P_j<=E_j",
 "global_collatz":"UNKNOWN"}
print(json.dumps(result,indent=2))
