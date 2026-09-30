#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from collections import defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import io
with redirect_stdout(io.StringIO()):
    import collatz_q0_rigid_recharge_audit as ra

def v2z(x:int):
    x=abs(x)
    return (x & -x).bit_length()-1

def vp(x:int,p:int):
    x=abs(x); v=0
    while x and x%p==0:
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
            m0=starts[start][2]; m1=starts[end][2]
            assert ra.admissible(c,m0) and ra.replay(c,m0)==m1
            out[r].append((c,m0,m1))
        last[r]=end
    return out

def audit(lo,hi,K):
    rows=[]
    s=max(3,lo); s += (s%2==0)
    for n in range(s,hi+1,2):
        for anchor,seq in returns(n,K).items():
            if len(seq)<2: continue
            m=seq[0][1]
            Abar=Bbar=0; Abar=1; Pbar=1
            states=[]
            for c,m0,m1 in seq:
                cc=centre(c)
                pulled=(Pbar*cc-Bbar)/Abar
                p,q=pulled.numerator,pulled.denominator
                assert q>0 and q%2==1
                N=m*q-p
                assert N>0
                k=v2z(N)
                u=N>>k
                states.append({
                    "centre":pulled,"k":k,"u":u,"ubits":u.bit_length(),
                    "v3u":vp(u,3),"q":q,"qbits":q.bit_length(),
                    "height":max(abs(p).bit_length(),q.bit_length())
                })
                Abar,Bbar,Pbar=(c["A"]*Abar,c["A"]*Bbar+c["B"]*Pbar,(1<<c["D"])*Pbar)
            for a,b in zip(states,states[1:]):
                if a["centre"]==b["centre"]: continue
                assert b["k"]>a["k"]
                rows.append((n,anchor,a,b))
    tests={
      "U_DOWN":lambda a,b:b["u"]<a["u"],
      "UBITS_DOWN":lambda a,b:b["ubits"]<a["ubits"],
      "V3U_DOWN":lambda a,b:b["v3u"]<a["v3u"],
      "LEX_U_V3":lambda a,b:(b["u"],b["v3u"])<(a["u"],a["v3u"]),
      "LEX_UBITS_V3":lambda a,b:(b["ubits"],b["v3u"])<(a["ubits"],a["v3u"]),
      "Q_DOWN":lambda a,b:b["q"]<a["q"],
      "HEIGHT_DOWN":lambda a,b:b["height"]<a["height"],
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
    return {"range":[lo,hi],"switches":len(rows),"tests":out}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--K",type=int,default=128)
    a=ap.parse_args()
    train=audit(3,8191,a.K); held=audit(8193,32767,a.K)
    survivors=[k for k in train["tests"] if train["tests"][k]["fail"]==0 and held["tests"][k]["fail"]==0]
    print(json.dumps({"schema":"COLLATZ_NORMALIZED_MISMATCH_TOURNAMENT_20260930",
      "train":train,"heldout":held,"survivors":survivors,
      "verdict":"SURVIVOR_FOUND" if survivors else "NO_NORMALIZED_MISMATCH_RANK",
      "global_collatz":"UNKNOWN"},indent=2,sort_keys=True))

if __name__=="__main__": main()
