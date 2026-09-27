#!/usr/bin/env python3
"""Exact low-valuation automaton for odd Collatz acceleration.
Study odd x with s=v2(3x+1) in {1,2}. Compute residue transitions modulo 2^m
under U(x)=(3x+1)/2^s and find cycles that avoid s>=3. This isolates whether
'high valuation eventually occurs' is true or false and the exact exceptional
2-adic language.
"""
import json
def v2(n):
 c=0
 while n%2==0:c+=1;n//=2
 return c
def U(x):
 z=3*x+1;s=v2(z);return z>>s,s
rows=[]
for m in range(3,17):
 M=1<<m; states=[r for r in range(1,M,2) if v2(3*r+1) in (1,2)]
 # transition is only residue-deterministic modulo 2^(m-s); use all two lifts at target modulus m
 # Instead characterize finite words by enumerating odd residues mod 2^m and their low-s prefix.
 hist={}; maxlen=0; survivors=[]
 for r in range(1,M,2):
  x=r; w=[]
  for j in range(m-2):
   x,s=U(x)
   if s>=3:break
   w.append(s)
  if len(w)>maxlen:maxlen=len(w)
  if len(w)>=m-2:survivors.append({"r":r,"word":"".join(map(str,w))})
  hist[len(w)]=hist.get(len(w),0)+1
 rows.append({"m":m,"odd_residues":M//2,"max_low_run":maxlen,
              "full_low_survivors":len(survivors),"first_survivors":survivors[:20],
              "length_hist":hist})
print(json.dumps({"schema":"COLLATZ_LOW_VALUATION_AVOIDANCE_AUTOMATON_V0","rows":rows,
 "interpretation":"If full_low_survivors persist one per compatible tower, high-valuation eventuality is false 2-adically and positivity/source bounds must kill the tower.",
 "global_collatz":"UNKNOWN"},indent=2))
