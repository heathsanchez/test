"""Crystal V1: source-coupled Collatz residual discovery.

Discovery only. Protected observation is an exact bounded witness of OrdinaryExit:
terminal/descent, or intersection with a smaller positive source orbit.
No bounded miss is promoted to a universal no-exit claim.
"""
from dataclasses import dataclass
from collections import defaultdict
import json, math, random

def T(n):
    return n//2 if n%2==0 else (3*n+1)//2

def orbit_prefix(n,h):
    out=[n]
    for _ in range(h): out.append(T(out[-1]))
    return out

def zero_tail_depth(n):
    return max(0,n.bit_length())

def lower_basin(n,h):
    hit={}
    for p in range(1,n):
        x=p
        for r in range(h+1):
            hit.setdefault(x,(p,r))
            x=T(x)
    return hit

def first_exit(n,forward_h=160,reverse_h=160):
    basin=lower_basin(n,reverse_h)
    x=n
    for k in range(forward_h+1):
        if x in (1,2): return k,("terminal",x)
        if x<n: return k,("descent",x)
        if x in basin:
            p,r=basin[x]
            return k,("merge",p,r,x)
        x=T(x)
    return None

def trace_features(n,h=96):
    K=zero_tail_depth(n); xs=orbit_prefix(n,K+h)
    q=0; b=0; rows=[]
    # exact affine cocycle: 2^k*y = 3^q*n+b
    for k,y in enumerate(xs):
        if k>=K:
            rows.append((k-K,y,q,b,y%3,y%9,y%12,y%27))
        if k<len(xs)-1:
            if y%2:
                b=3*b+2**k; q+=1
    return rows

def future_signature(n,k,h,basin):
    x=orbit_prefix(n,k)[-1]
    sig=[]
    for j in range(h+1):
        if x in (1,2): sig.append(("T",j)); break
        if x<n: sig.append(("D",j)); break
        if x in basin:
            p,r=basin[x]; sig.append(("M",j,p,r)); break
        sig.append(("N", x%2, x%3, x%9, x%12))
        x=T(x)
    return tuple(sig)

def coarse(row):
    _,y,q,b,m3,m9,m12,m27=row
    # Deliberately small initial interface. Separators must earn refinements.
    return (m3,y%2)

def refined(row):
    _,y,q,b,m3,m9,m12,m27=row
    return (m12,m27,q%2,b%3)

def census(sources,post=24,future=24,reverse=96):
    coarse_groups=defaultdict(list); records=[]
    for n in sources:
        basin=lower_basin(n,reverse)
        K=zero_tail_depth(n)
        rows=trace_features(n,post)
        for row in rows:
            k=K+row[0]
            sig=future_signature(n,k,future,basin)
            coarse_groups[coarse(row)].append((n,row,sig))
            records.append((n,row,sig))
    separators=[]
    for key,items in coarse_groups.items():
        bysig=defaultdict(list)
        for item in items: bysig[item[2]].append(item)
        if len(bysig)>1:
            vals=list(bysig.values())
            a,b=vals[0][0],vals[1][0]
            separators.append({
                "coarse_class":key,
                "a":{"n":a[0],"row":a[1],"refined":refined(a[1])},
                "b":{"n":b[0],"row":b[1],"refined":refined(b[1])},
                "different_protected_futures":True})
    return {
      "schema":"COLLATZ_CRYSTAL_SOURCE_COUPLED_V1",
      "epistemic":"DISCOVERY_ONLY_BOUNDED",
      "sources":len(sources),"states":len(records),
      "coarse_classes":len(coarse_groups),
      "separator_count":len(separators),
      "first_separators":separators[:20],
      "boundary":"A bounded miss is UNKNOWN, never no-exit. Global Collatz UNKNOWN."
    }

if __name__=="__main__":
    train=list(range(3,513))
    rng=random.Random(28092026)
    prospective=[rng.randrange(513,4097) for _ in range(256)]
    print(json.dumps({
      "train":census(train),
      "prospective":census(prospective),
    },indent=2))
