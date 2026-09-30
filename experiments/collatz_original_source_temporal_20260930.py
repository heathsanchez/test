#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from collections import defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import io
with redirect_stdout(io.StringIO()):
    import collatz_q0_rigid_recharge_audit as ra
    import collatz_q0_coalescence_component_audit as base

def v2z(x:int):
    x=abs(x); assert x
    return (x & -x).bit_length()-1

def vp(x:int,p:int):
    x=abs(x); assert x
    v=0
    while x%p==0: x//=p; v+=1
    return v

def centre(c): return Fraction(c["B"],(1<<c["D"])-c["A"])

def odd_prefix(n,K):
    q=[0]*(K+1); x=n
    for k in range(K):
        q[k+1]=q[k]+(x&1); x=base.T(x)
    return q

def sequences(n,K):
    starts,branches=ra.rigid_episode_segment(n,K)
    cache={}; last={}; out=defaultdict(list)
    qpref=odd_prefix(n,K)
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            start=last[r]; w=tuple(branches[start:end])
            c=cache.setdefault(w,ra.certificate(w))
            m0=starts[start][2]; m1=starts[end][2]; k0=starts[start][0]
            assert ra.admissible(c,m0) and ra.replay(c,m0)==m1
            cm=centre(c); qk=qpref[k0]
            cn=Fraction(n,1)+Fraction(1<<(k0+r),3**qk)*(cm-Fraction(m0,1))
            p,q=cn.numerator,cn.denominator
            N=n*q-p; assert N
            prec=v2z(N); u=abs(N)>>prec; v3=vp(u,3); core3=u//3**v3
            st={"centre":cn,"precision":prec,"u":u,"ubits":u.bit_length(),
                "v3":v3,"core3":core3,"core3bits":core3.bit_length()}
            if not out[r] or out[r][-1]["centre"]!=cn:
                out[r].append(st)
        last[r]=end
    return out

def audit(lo,hi,K):
    seqs=[]
    s=max(3,lo); s+=(s%2==0)
    for n in range(s,hi+1,2):
        for r,z in sequences(n,K).items():
            if len(z)>=2: seqs.append((n,r,z))
    fields=["u","ubits","core3","core3bits","v3"]
    horizons={}
    for h in range(1,6):
        hh={}
        total=0
        for f in fields:
            bad=[]; passed=0; totalf=0
            for n,r,z in seqs:
                for i in range(len(z)-h):
                    totalf+=1
                    if z[i+h][f] < z[i][f]: passed+=1
                    elif len(bad)<3: bad.append({"source":n,"anchor":r,"i":i,
                        "old":str(z[i][f]),"new":str(z[i+h][f]),
                        "old_precision":z[i]["precision"],"new_precision":z[i+h]["precision"]})
            hh[f]={"comparisons":totalf,"pass":passed,"fail":totalf-passed,"first_fail":bad}
            total=max(total,totalf)
        # Two mechanism-shaped lex orders.
        for name,a,b in [("LEX_CORE3_V3","core3","v3"),("LEX_CORE3BITS_V3","core3bits","v3"),
                         ("LEX_UBITS_V3","ubits","v3")]:
            bad=[];passed=0;totalf=0
            for n,r,z in seqs:
                for i in range(len(z)-h):
                    totalf+=1
                    if (z[i+h][a],z[i+h][b]) < (z[i][a],z[i][b]): passed+=1
                    elif len(bad)<3: bad.append({"source":n,"anchor":r,"i":i,
                        "old":[str(z[i][a]),str(z[i][b])],
                        "new":[str(z[i+h][a]),str(z[i+h][b])],
                        "old_precision":z[i]["precision"],"new_precision":z[i+h]["precision"]})
            hh[name]={"comparisons":totalf,"pass":passed,"fail":totalf-passed,"first_fail":bad}
        horizons[str(h)]=hh
    return {"range":[lo,hi],"sequence_count":len(seqs),"horizons":horizons}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--K",type=int,default=128)
    a=ap.parse_args()
    tr=audit(3,8191,a.K); ho=audit(8193,32767,a.K)
    survivors=[]
    for h in tr["horizons"]:
        for f in tr["horizons"][h]:
            if tr["horizons"][h][f]["comparisons"] and tr["horizons"][h][f]["fail"]==0 and ho["horizons"][h][f]["fail"]==0:
                survivors.append([int(h),f])
    print(json.dumps({"schema":"COLLATZ_ORIGINAL_SOURCE_TEMPORAL_20260930",
      "train":tr,"heldout":ho,"survivors":survivors,
      "verdict":"TEMPORAL_RANK_FOUND" if survivors else "NO_FIXED_HORIZON_RANK_H1_TO_H5",
      "global_collatz":"UNKNOWN"},indent=2,sort_keys=True))

if __name__=="__main__": main()
