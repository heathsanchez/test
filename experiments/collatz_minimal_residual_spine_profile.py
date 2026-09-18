#!/usr/bin/env python3
"""Profile source-spine and q=0 episode-spine geometry of the 40 current hard candidates.

These are the exact residuals after:
  * pre-q0 D/P filtering,
  * hereditary q0 RIGID grammar,
  * universal reverse-episode BFS depth 5 (R,S <= 14).

For each fixed source n:
  - source trailing-ones resource v2(n+1);
  - q0 endpoint d0=T^k0(n);
  - q0 episode sequence (r,s,r') while the actual orbit stays >= n;
  - first direct descent below n.

Discovery only.
"""
from __future__ import annotations
from collections import Counter
import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

SOURCES=[
4167,4255,4263,4399,4511,4591,4719,4735,4763,4767,
4863,4935,5055,5151,5223,5247,5403,5479,5535,5679,
5887,6079,6171,6271,6303,6471,6591,6823,6895,6939,
7167,7323,7327,7335,7527,7707,7839,7935,7963,8175,
]

def v2(x:int)->int:
    assert x>0
    return (x & -x).bit_length()-1

rows=[]
rseqs=Counter(); first_rel=Counter(); maxr_hist=Counter(); source_r_hist=Counter()
q0_r_hist=Counter(); episode_count_hist=Counter()
for n in SOURCES:
    k0=n.bit_length()
    c0,d0=base.forward_state(k0,n)
    rs=v2(n+1)
    source_r_hist[rs]+=1
    rq=v2(d0+1) if d0&1 else None
    if rq is not None:q0_r_hist[rq]+=1

    y=d0
    t=k0
    eps=[]
    # Normalize any even q0 endpoint to next odd state first, retaining exact steps.
    while y%2==0:
        y=base.T(y); t+=1
        if y<n:
            break

    direct=None
    if y<n:
        direct=(t,y)
    else:
        for _ in range(64):
            assert y&1
            r,m,s,rp,mp,z=ra.episode(y)
            start=y
            # replay shortcut-by-shortcut to locate first descent exactly
            cur=y
            hit=None
            for j in range(1,r+s+1):
                cur=base.T(cur)
                if cur<n and hit is None:
                    hit=(t+j,cur,j)
            assert cur==z
            eps.append((t,start,r,s,rp,z,z-n,hit))
            t+=r+s
            y=z
            if hit is not None:
                direct=(hit[0],hit[1])
                break

    rseq=tuple(e[2] for e in eps)
    rpseq=tuple(e[4] for e in eps)
    rseqs[rseq]+=1
    episode_count_hist[len(eps)]+=1
    maxr=max(rseq,default=0);maxr_hist[maxr]+=1
    if len(eps)>=2:
        first_rel['down' if eps[1][2]<eps[0][2] else ('up' if eps[1][2]>eps[0][2] else 'eq')]+=1
    row=(n,k0,rs,c0,d0,v2(d0+1),len(eps),rseq,rpseq,maxr,direct,tuple(eps))
    rows.append(row)
    print("SPINE",row)

print("N",len(rows))
print("SOURCE_R_HIST",dict(sorted(source_r_hist.items())))
print("Q0_R_HIST",dict(sorted(q0_r_hist.items())))
print("EPISODE_COUNT_HIST",dict(sorted(episode_count_hist.items())))
print("MAX_R_HIST",dict(sorted(maxr_hist.items())))
print("FIRST_R_RELATION",dict(first_rel))
print("MAX_DIRECT",max((r[10][0]-r[1],r[0],r[10]) for r in rows if r[10]))
print("MAX_EPISODES",max((r[6],r[0],r[7]) for r in rows))
print("STATUS MINIMAL_RESIDUAL_SPINE_PROFILE")
