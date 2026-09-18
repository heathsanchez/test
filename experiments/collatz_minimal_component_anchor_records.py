#!/usr/bin/env python3
"""Pre-descent coalescence quotient of current minimal-counterexample candidates.

Candidates:
  * no D or immediate-P certificate before q0,
  * survives compiled grammar to q0 as RIGID.

Process candidates in increasing n.  For each n, follow its ordinary shortcut
orbit only until the first value < n.  If before that event it hits a state on
the pre-descent path of any smaller candidate, n has an exact lower-merge
certificate to that smaller source.  Otherwise n creates a new component
anchor.

The quotient is exact over the bounded source range; no convergence-to-1
assumption is used.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import collatz_q0_coalescence_component_audit as base

def preq0_dp(n):
    k0=n.bit_length(); y=n
    for t in range(1,k0+1):
        y=base.T(y)
        if y<n:return ('D',t,y)
        if y%3==2:
            p=(2*y-1)//3
            if 0<p<n and base.T(p)==y:return ('P',t,y,p)
    return None

def candidate(n):
    if preq0_dp(n) is not None:return False
    ok,_=base.survives_to_q0(n)
    return ok and base.birth_status(n)[0]=='RIGID'

def pre_descent_path(n,H=5000):
    y=n; out=[n]
    for t in range(1,H+1):
        y=base.T(y)
        if y<n:
            return out,(t,y)
        out.append(y)
    return out,None

owner={}   # state -> smallest candidate source whose pre-descent path contains it
anchors=[]
rows=[]
stats=defaultdict(Counter)
for n in range(3,65536,2):
    if not candidate(n):continue
    k=n.bit_length()
    path,desc=pre_descent_path(n)
    assert desc is not None,(n,len(path))
    hit=None
    for t,y in enumerate(path):
        m=owner.get(y)
        if m is not None and m<n:
            hit=(t,y,m)
            break
    if hit is None:
        anchors.append(n)
        stats[k]['anchor']+=1
    else:
        stats[k]['coalesce']+=1
    rows.append((n,k,len(path)-1,desc,hit))
    for y in path:
        if y not in owner or n<owner[y]:
            owner[y]=n

print("CANDIDATES",len(rows))
print("ANCHORS",len(anchors))
print("ANCHOR_LIST",anchors)
for k in sorted(stats):
    print("BITS",k,dict(stats[k]))
print("FIRST_ROWS",rows[:80])
# Record anchor stopping geometry.
for n in anchors:
    row=next(z for z in rows if z[0]==n)
    print("ANCHOR",row)
print("STATUS MINIMAL_PRE_DESCENT_COALESCENCE_QUOTIENT")
