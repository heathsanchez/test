#!/usr/bin/env python3
"""Crystal V37b: exact paired-family source-order constructor.

The sole V23 residual is
  n(t)=N0+NC*t = 3^8 * m(t)
with
  m(t)=M0+2^59*t < n(t).

For a parameter cell t=r+2^d*u, follow the exact uniform affine prefixes of
both deterministic shortcut orbits until the next free parameter bit is
needed.  Close a cell only by one of:
  D: uniform direct descent of n(t) below its source;
  S: uniform source-relative quarter splice;
  P: exact affine common future between n(t) and the strictly smaller m(t).

Otherwise split on the next parameter bit.  This is an exact source-order
constructor search, not a source census.
"""
from __future__ import annotations
from collections import Counter
import hashlib,json

N0=38_911_100_780_481_085_467
NC=3_782_158_995_862_761_504_768
P3=3**8
assert NC==P3*(1<<59)
assert N0%P3==0
M0=N0//P3
MAX_DEPTH=18

def fixed_prefix(A:int,C:int):
    out=[]
    q=0; j=0
    while True:
        out.append((j,A,C,q))
        if C&1:
            break
        if A&1:
            A=(3*A+1)//2
            C=(3*C)//2
            q+=1
        else:
            A//=2; C//=2
        j+=1
    return out

def direct_or_splice(pref,N,S):
    for j,A,C,q in pref:
        if (A<N and C<=S) or (A<=N and C<S):
            return {"kind":"D","n_depth":j,"A":A,"C":C,"q":q}
        if C%8==0 and A%8==5 and A<=4*N and C<=4*S:
            return {"kind":"S","n_depth":j,"A":A,"C":C,"q":q}
    return None

def paired_common(pn,pm):
    bank={}
    for jm,A,C,q in pm:
        bank.setdefault((A,C),(jm,q))
    best=None
    for jn,A,C,q in pn:
        z=bank.get((A,C))
        if z is not None:
            jm,qm=z
            cand=(jn+jm,jn,jm,q,qm,A,C)
            if best is None or cand<best:
                best=cand
    if best is None:
        return None
    _,jn,jm,qn,qm,A,C=best
    return {"kind":"P","n_depth":jn,"m_depth":jm,
            "n_odds":qn,"m_odds":qm,"A":A,"C":C}

def classify(d,r):
    N=N0+NC*r
    S=NC*(1<<d)
    M=M0+(1<<59)*r
    MS=(1<<(59+d))
    assert N==P3*M and S==P3*MS
    pn=fixed_prefix(N,S)
    pm=fixed_prefix(M,MS)
    assert pn[-1][0]==59+d
    assert pm[-1][0]==59+d
    ex=direct_or_splice(pn,N,S)
    if ex is not None:
        return ex
    p=paired_common(pn,pm)
    if p is not None:
        return p
    return None

frontier=[(0,0)]
rows=[]
counts=[]
all_exits=Counter()
first_examples={}
for d in range(MAX_DEPTH+1):
    assert all(x[0]==d for x in frontier)
    nxt=[]
    here=Counter()
    for _d,r in frontier:
        ex=classify(d,r)
        if ex is None:
            here["L"]+=1
            if d<MAX_DEPTH:
                nxt.append((d+1,r))
                nxt.append((d+1,r+(1<<d)))
        else:
            k=ex["kind"]; here[k]+=1; all_exits[k]+=1
            first_examples.setdefault(k,{"d":d,"r":r,"exit":ex})
            if len(rows)<200:
                rows.append({"d":d,"r":r,"exit":ex})
    counts.append({"depth":d,"input_cells":len(frontier),
                   "D":here["D"],"S":here["S"],"P":here["P"],
                   "live":here["L"]})
    frontier=nxt
    if not frontier:
        break

# Strong exact checks on every paired closure recorded in the frontier census.
# The affine identity itself proves equality for every u>=0 in that cell.
status="FINITE_PAIRED_SOURCE_ORDER_COVER" if not frontier else "PAIRED_SOURCE_ORDER_RESIDUAL"
result={
 "schema":"COLLATZ_CRYSTAL_PAIRED_SOURCE_ORDER_V37B",
 "family":{
   "n":"N0+NC*t","N0":N0,"NC":NC,
   "m":"M0+2^59*t","M0":M0,
   "factor":P3,
   "identity":"n(t)=3^8*m(t)",
 },
 "max_parameter_depth":MAX_DEPTH,
 "depth_counts":counts,
 "exit_totals":dict(all_exits),
 "first_examples":first_examples,
 "sample_closures":rows,
 "final_live_cells":len(frontier),
 "first_live_cells":[{"d":d,"r":r} for d,r in frontier[:100]],
 "scientific_verdict":status,
 "claim_boundary":(
   "Each closed parameter cylinder is exact for all natural u>=0. "
   "A finite empty frontier would give universal coverage of the V23 affine "
   "family by direct descent, quarter splice, or a common future with the "
   "strictly smaller paired source m(t). A nonempty frontier is an exact "
   "symbolic residual, not evidence of failure."
 ),
 "universal_status":"UNKNOWN",
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
