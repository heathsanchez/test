#!/usr/bin/env python3
"""Exact bounded census of reverse depth in first source-order coalescence witnesses.

For each source n<=2^20, process sources increasingly and stop its actual
shortcut orbit at the first state already owned by a smaller processed source.
Record the smaller source's forward depth b.  This is the reverse-certificate
length needed to regenerate that meeting state from the smaller source.

The goal is to test the Crystal hypothesis suggested by the coalescence record
rows: forward waiting may be long while the source-changing reverse witness is
shallow.
"""
from collections import Counter
import json

LIMIT=(1<<20)-1
STEP_CAP=10000

def T(n):
    return n//2 if n%2==0 else (3*n+1)//2

def reverse_word(p,b):
    x=p; letters=[]
    for _ in range(b):
        letters.append("E" if x%2==0 else "O")
        x=T(x)
    return "".join(reversed(letters)),x

owner={1:(1,0),2:(1,1)}
hist=Counter()
odd_hist=Counter()
max_b=-1; max_rows=[]
record_a=-1; record_rows=[]
above_hist=Counter()

for n in range(2,LIMIT+1):
    x=n; path=[]
    for a in range(STEP_CAP+1):
        if x in owner: break
        path.append(x); x=T(x)
    else: raise AssertionError(("STEP_CAP",n,x))
    p,b=owner[x]
    assert 0<p<n
    w,z=reverse_word(p,b)
    assert z==x
    hist[b]+=1
    if n&1: odd_hist[b]+=1
    if x>=n: above_hist[b]+=1

    if b>max_b:
        max_b=b; max_rows=[{"n":n,"a":a,"meeting":x,"p":p,"b":b,"reverse_word":w}]
    elif b==max_b and len(max_rows)<20:
        max_rows.append({"n":n,"a":a,"meeting":x,"p":p,"b":b,"reverse_word":w})

    if a>record_a:
        record_a=a
        record_rows.append({"n":n,"a":a,"meeting":x,"p":p,"b":b,"reverse_word":w})

    for d,y in enumerate(path):
        owner.setdefault(y,(n,d))

result={
 "schema":"COLLATZ_COALESCENCE_REVERSE_DEPTH_CENSUS_V1",
 "source_limit":LIMIT,
 "sources":LIMIT-1,
 "max_smaller_source_depth":max_b,
 "depth_histogram":dict(sorted(hist.items())),
 "odd_depth_histogram":dict(sorted(odd_hist.items())),
 "above_source_depth_histogram":dict(sorted(above_hist.items())),
 "max_depth_examples":max_rows,
 "coalescence_forward_record_rows":record_rows,
 "candidate":(
   "bounded data suggest source-order coalescence can require arbitrarily long "
   "forward waiting while the inherited smaller-source witness is often shallow; "
   "only a universal bound on reverse witness depth would turn this into a finite "
   "reverse-cone avoidance theorem."
 ),
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
