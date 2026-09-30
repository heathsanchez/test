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
    while x%p==0:
        x//=p; v+=1
    return v

def centre(c):
    return Fraction(c["B"],(1<<c["D"])-c["A"])

def returns(n,K):
    starts,branches=ra.rigid_episode_segment(n,K)
    cache={}; last={}; out=defaultdict(list)
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            start=last[r]; w=tuple(branches[start:end])
            c=cache.setdefault(w,ra.certificate(w))
            m0=starts[start][2]; m1=starts[end][2]; k0=starts[start][0]
            assert ra.admissible(c,m0) and ra.replay(c,m0)==m1
            out[r].append((c,m0,m1,k0))
        last[r]=end
    return out

def odd_prefix(n,K):
    q=[0]*(K+1); x=n
    for k in range(K):
        q[k+1]=q[k]+(x&1)
        x=base.T(x)
    return q

def audit(lo,hi,K):
    rows=[]
    s=max(3,lo); s += (s%2==0)
    for n in range(s,hi+1,2):
        qpref=odd_prefix(n,K)
        for anchor,seq in returns(n,K).items():
            if len(seq)<2: continue
            states=[]
            for c,m0,m1,k0 in seq:
                cm=centre(c)
                qk=qpref[k0]
                # Exact pullback from owner coordinate m=(T^k(n)+1)/2^anchor
                # to original source coordinate n.
                cn=Fraction(n,1) + Fraction(1<<(k0+anchor),3**qk)*(cm-Fraction(m0,1))
                p,q=cn.numerator,cn.denominator
                assert q>0 and q%2==1
                N=n*q-p
                assert N!=0
                k=v2z(N)
                u=abs(N)>>k
                v3=vp(u,3)
                core3=u//(3**v3)
                states.append({
                  "centre":cn,"precision":k,"N":N,
                  "u":u,"ubits":u.bit_length(),"v3u":v3,
                  "core3":core3,"core3bits":core3.bit_length(),
                  "q":q,"qbits":q.bit_length(),
                  "k0":k0,"anchor":anchor
                })
            for a,b in zip(states,states[1:]):
                if a["centre"]==b["centre"]: continue
                rows.append((n,anchor,a,b))
    tests={
      "PRECISION_UP":lambda a,b:b["precision"]>a["precision"],
      "U_DOWN":lambda a,b:b["u"]<a["u"],
      "UBITS_DOWN":lambda a,b:b["ubits"]<a["ubits"],
      "V3U_DOWN":lambda a,b:b["v3u"]<a["v3u"],
      "CORE3_DOWN":lambda a,b:b["core3"]<a["core3"],
      "CORE3BITS_DOWN":lambda a,b:b["core3bits"]<a["core3bits"],
      "LEX_CORE3_V3":lambda a,b:(b["core3"],b["v3u"])<(a["core3"],a["v3u"]),
      "LEX_CORE3BITS_V3":lambda a,b:(b["core3bits"],b["v3u"])<(a["core3bits"],a["v3u"]),
      "LEX_UBITS_V3":lambda a,b:(b["ubits"],b["v3u"])<(a["ubits"],a["v3u"]),
    }
    out={}
    for name,fn in tests.items():
        bad=[r for r in rows if not fn(r[2],r[3])]
        out[name]={"pass":len(rows)-len(bad),"fail":len(bad),
          "first_fail":None if not bad else {
            "source":bad[0][0],"anchor":bad[0][1],
            "old":{k:str(v) for k,v in bad[0][2].items() if k!="centre"},
            "new":{k:str(v) for k,v in bad[0][3].items() if k!="centre"},
          }}
    beyond=[r for r in rows if r[2]["precision"]>=r[0].bit_length()]
    return {"range":[lo,hi],"switches":len(rows),"source_tail_switches":len(beyond),"tests":out}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--K",type=int,default=128)
    a=ap.parse_args()
    tr=audit(3,8191,a.K); ho=audit(8193,32767,a.K)
    rank_names=[k for k in tr["tests"] if k!="PRECISION_UP"]
    survivors=[k for k in rank_names if tr["tests"][k]["fail"]==0 and ho["tests"][k]["fail"]==0]
    result={"schema":"COLLATZ_ORIGINAL_SOURCE_MISMATCH_20260930",
      "train":tr,"heldout":ho,"survivors":survivors,
      "precision_up_both":tr["tests"]["PRECISION_UP"]["fail"]==0 and ho["tests"]["PRECISION_UP"]["fail"]==0,
      "verdict":"ORIGINAL_SOURCE_RANK_FOUND" if survivors else "NO_POINTWISE_ORIGINAL_SOURCE_RANK",
      "global_collatz":"UNKNOWN"}
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__": main()
