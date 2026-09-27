#!/usr/bin/env python3
"""Search exact finite positive low-valuation orbits and identify the only
sources that can sustain long s in {1,2}. This is a falsifier for the candidate
'all infinite low paths over N are x=1' theorem; records source minima by length.
"""
import json
def v2(n):
 c=0
 while n%2==0:c+=1;n//=2
 return c
def U(x):
 z=3*x+1;s=v2(z);return z>>s,s
LIMIT=1<<28; CAP=200
records=[];best=0;bestx=None;bestword=""
hist={}
for x0 in range(1,LIMIT,2):
 x=x0;w=[]
 for j in range(CAP):
  x,s=U(x)
  if s>=3:break
  w.append(s)
 # exclude fixed 1 after recording separately
 L=len(w);hist[L]=hist.get(L,0)+1
 if x0!=1 and L>best:
  best=L;bestx=x0;bestword="".join(map(str,w));records.append({"x":x0,"length":L,"word":bestword,"end":x})
print(json.dumps({"schema":"COLLATZ_APERIODIC_LOW_PATH_FALSIFIER_V0","limit":LIMIT,"cap":CAP,
 "record_nontrivial_length":best,"record_nontrivial_source":bestx,"record_word":bestword,
 "records":records,"x1_is_infinite_low_fixed":True,
 "candidate":"the only positive integer odd orbit with s_i in {1,2} forever is x=1",
 "status":"BOUNDED_FALSIFIER_ONLY","global_collatz":"UNKNOWN"},indent=2))
