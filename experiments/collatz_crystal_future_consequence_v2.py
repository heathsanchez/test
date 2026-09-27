#!/usr/bin/env python3
"""Crystal V2: future lower-source consequence, no constructor bank.

Discovery labels are generated only by exact generic reverse reachability:
from an actual orbit endpoint y, breadth-first enumerate legal one-step
predecessors (2y and, when legal, (2y-1)/3). A label is positive iff any
enumerated predecessor p<n reaches y exactly. Historical constructor names are
never provided to Crystal.

Crystal then searches source-relative observables for consequence-pure values
predicting a lower-source certificate within a short future window. This is
bounded theorem discovery, not a Collatz proof.
"""
from collections import defaultdict, deque
import json

TRAIN_MAX=8192
H=256
REV_DEPTH=9
LOOK=8
HOLDOUT=[13421671,14378779,8088063,12132095,9280639,13774695,
         1126015,2252031,1689023,6206655,63728127]

def T(x):
    return (3*x+1)//2 if x&1 else x//2

def v2(x):
    if x<=0: return 0
    return (x & -x).bit_length()-1

def reverse_cert(n,target):
    if 0 < target < n:
        return (target,0)
    q=deque([(target,0)])
    seen={target}
    while q:
        z,d=q.popleft()
        if d>=REV_DEPTH: continue
        # exact even predecessor
        a=2*z
        if a not in seen:
            seen.add(a)
            if 0<a<n:
                x=a
                for _ in range(d+1): x=T(x)
                assert x==target
                return (a,d+1)
            q.append((a,d+1))
        # exact odd predecessor, when admissible
        if z%3==2:
            p=(2*z-1)//3
            if p>0 and p&1 and T(p)==z and p not in seen:
                seen.add(p)
                if p<n:
                    x=p
                    for _ in range(d+1): x=T(x)
                    assert x==target
                    return (p,d+1)
                q.append((p,d+1))
    return None

def feats(n,j,y):
    return {
      "parity":y&1,
      "mod3":y%3,
      "mod9":y%9,
      "v2y":min(v2(y),8),
      "v2_3y1":min(v2(3*y+1),8) if y&1 else -1,
      "ratio2":min((2*y)//n,12),
      "y_lt_2n":y<2*n,
      "2y_lt_3n1":2*y<3*n+1,
      "y_lt_3n":y<3*n,
      "jmod2":j&1,
    }

def trace(n):
    ys=[]; cert=[]
    y=n
    for j in range(H+1):
        ys.append(y); cert.append(reverse_cert(n,y))
        if cert[-1] is not None: break
        y=T(y)
    rows=[]
    for j,y in enumerate(ys):
        wait=None
        for t in range(0,min(LOOK,len(ys)-1-j)+1):
            if cert[j+t] is not None:
                wait=t; break
        r={"n":n,"j":j,"y":y,"cert_now":cert[j] is not None,
           "future_wait":wait if wait is not None else LOOK+1}
        r.update(feats(n,j,y))
        rows.append(r)
    return rows

train=[]
for n in range(3,TRAIN_MAX,2):
    train.extend(trace(n))

fields=["parity","mod3","mod9","v2y","v2_3y1","ratio2",
        "y_lt_2n","2y_lt_3n1","y_lt_3n","jmod2"]

# Consequence-pure atomic values for horizons 0,1,2,4.
pure={}
for horizon in [0,1,2,4]:
    out=[]
    for f in fields:
        tab=defaultdict(lambda:[0,0])
        for r in train:
            good=r["future_wait"]<=horizon
            tab[repr(r[f])][int(good)]+=1
        for val,(neg,pos) in tab.items():
            if pos and neg==0:
                out.append({"field":f,"value":val,"support":pos})
    pure[str(horizon)]=sorted(out,key=lambda x:(-x["support"],x["field"],x["value"]))[:40]

# Exact generic law discovered by consequence pullback:
# if y is even and y<2n, then T(y)=y/2<n, hence certificate next step.
for r in train:
    if r["parity"]==0 and r["y_lt_2n"]:
        assert r["future_wait"]<=1

# And if after r even halvings an endpoint z is 2 mod 3 and its exact odd
# predecessor is below n, generic reverse reachability certifies it. Verify the
# parametric algebra on all observed even runs without naming a bank.
pullback_checks=0
for n in range(3,TRAIN_MAX,2):
    y=n
    for j in range(H):
        z=y
        for r in range(0,min(v2(z),8)+1):
            if z%(1<<r): break
            u=z>>r
            if u%3==2:
                p=(2*u-1)//3
                if 0<p<n:
                    assert T(p)==u
                    x=u
                    # u is future of z by r even steps
                    assert (z>>r)==x
                    pullback_checks+=1
        y=T(y)
        if reverse_cert(n,y) is not None: break

hold=[]
for n in HOLDOUT:
    rs=trace(n)
    hold.append({
      "n":n,
      "rows":len(rs),
      "first_certificate_depth":next((r["j"] for r in rs if r["cert_now"]),None),
      "max_future_wait_seen":max(r["future_wait"] for r in rs),
      "terminal":rs[-1],
    })

out={
 "schema":"COLLATZ_CRYSTAL_FUTURE_CONSEQUENCE_V2",
 "constructor_bank_used":False,
 "label_engine":"exact generic reverse BFS over legal one-step predecessors",
 "train_odd_sources":(TRAIN_MAX-3)//2+1,
 "train_rows":len(train),
 "reverse_depth":REV_DEPTH,
 "future_window":LOOK,
 "consequence_pure_atomic_values":pure,
 "exact_pullback_law":"even y<2n => next endpoint y/2<n => LOWER_SOURCE_CERTIFICATE",
 "generic_even_run_reverse_checks":pullback_checks,
 "holdout":hold,
 "status":"BOUNDED_FUTURE_CONSEQUENCE_DISCOVERY",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(out,indent=2))
