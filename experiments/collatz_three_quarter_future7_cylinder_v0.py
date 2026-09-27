#!/usr/bin/env python3
import json, math
LIMIT=1<<22; CAP=1024
def T(x): return (3*x+1)//2 if x&1 else x//2
def word_affine(y):
 x=y;bits=[];A=1;B=0;D=0
 for a in range(1,CAP+1):
  bit=x&1;bits.append(bit)
  if bit:A*=3;B=3*B+(1<<D)
  D+=1;x=T(x)
  if 4*x<=3*y:
   assert (1<<D)*x==A*y+B
   return tuple(bits),A,B,D,x
 return None
def threshold(A,B,D):
 delta=3*(1<<D)-4*A
 return None if delta<=0 else (4*B+delta-1)//delta
words={};unresolved=[]
for y in range(7,LIMIT,12):
 z=word_affine(y)
 if z is None:unresolved.append(y);continue
 w,A,B,D,x=z;key=(w,A,B,D)
 row=words.setdefault(key,{"count":0,"min_y":y,"max_y":y,"samples":[]})
 row["count"]+=1;row["min_y"]=min(row["min_y"],y);row["max_y"]=max(row["max_y"],y)
 if len(row["samples"])<3:row["samples"].append((y,x))
certs=[]
for (w,A,B,D),obs in words.items():
 th=threshold(A,B,D)
 if th is None:continue
 mod=1<<D;residue=obs["min_y"]%mod
 y0=residue or mod
 while y0%12!=7:y0+=mod
 period=math.lcm(mod,12)
 while y0<th:y0+=period
 certs.append({"word":"".join(map(str,w)),"steps":D,"odd":sum(w),"A":A,"B":B,
 "delta":3*(1<<D)-4*A,"threshold":th,"residue_mod_2a":residue,
 "period_with_mod12":period,"first_certified_y":y0,**obs})
certs.sort(key=lambda c:(c["steps"],c["threshold"],c["residue_mod_2a"]))
miss=[]
for y in range(7,LIMIT,12):
 if not any(y>=c["threshold"] and y%(1<<c["steps"])==c["residue_mod_2a"] for c in certs):miss.append(y)
print(json.dumps({"schema":"COLLATZ_THREE_QUARTER_FUTURE7_CYLINDER_COMPILER_V0","limit":LIMIT,"cap":CAP,
"tested":len(range(7,LIMIT,12)),"unique_first_hit_words":len(words),"symbolic_certificates":len(certs),
"discovery_unresolved":unresolved[:20],"symbolic_uncovered_count":len(miss),"symbolic_uncovered_first":miss[:50],
"certificates":certs[:200],"status":"BOUNDED_SYMBOLIC_DISCOVERY","universal_status":"UNKNOWN"},indent=2))
