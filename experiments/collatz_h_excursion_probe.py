#!/usr/bin/env python3
"""Spike: exact separation-depth h excursions on RIGID return switches.

For consecutive distinct switches the proved law gives h_next relative to h:
drop <, recharge =, flat >.  A stepwise h rank is impossible because flats
increase it.  This probe asks a stronger regenerative question: does every
maximal non-drop excursion eventually return below its starting h?
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import collatz_q0_rigid_recharge_audit as ra

def returns(n,K):
    starts,branches=ra.rigid_episode_segment(n,K)
    cache={};last={};out=defaultdict(list)
    for end in range(1,len(starts)):
        r=starts[end][1]
        if r in last:
            start=last[r]
            word=tuple(branches[start:end])
            c=cache.setdefault(word,ra.certificate(word))
            m0=starts[start][2];m1=starts[end][2]
            out[r].append((c,m0,m1,starts[start][0]))
        last[r]=end
    return out

def switch_walk(seq):
    sw=[]
    for i in range(len(seq)-1):
        w,m0,m1,k0=seq[i]
        v,n0,n1,k1=seq[i+1]
        assert m1==n0
        if w['q']==v['q']: continue
        z=ra.switch_law(w,v,n0,n1)
        if z is None: continue
        sw.append((i,z['outcome'],z['h'],w['q'],v['q'],k1))
    # retain only truly consecutive switches so transport applies without same-pattern gap
    out=[]
    for a,b in zip(sw,sw[1:]):
        if b[0]==a[0]+1:
            out.append((a,b))
    return sw,out

def audit(lo,hi,K):
    pairs=Counter(); triples=Counter()
    excursions=[]; bad=[]
    max_h=0;max_climb=0
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        for r,seq in returns(n,K).items():
            sw,_=switch_walk(seq)
            if not sw: continue
            for a,b in zip(sw,sw[1:]):
                if b[0]!=a[0]+1: continue
                pairs[(a[1],b[1])]+=1
                max_h=max(max_h,a[2],b[2])
            for a,b,c in zip(sw,sw[1:],sw[2:]):
                if b[0]==a[0]+1 and c[0]==b[0]+1:
                    triples[(a[1],b[1],c[1])]+=1
            # Excursion starts at any switch and runs through recharge/flat until first drop.
            for i in range(len(sw)):
                h0=sw[i][2]
                peak=h0
                j=i+1
                while j<len(sw) and sw[j][0]==sw[j-1][0]+1 and sw[j-1][1]!="drop":
                    peak=max(peak,sw[j][2]);j+=1
                if j<len(sw) and sw[j][0]==sw[j-1][0]+1 and sw[j-1][1]=="drop":
                    # drop outcome at sw[j-1] determines h at sw[j]
                    hend=sw[j][2]
                    row=(n,r,i,j,h0,peak,hend,tuple(x[1] for x in sw[i:j+1]),
                         tuple(x[2] for x in sw[i:j+1]))
                    excursions.append(row)
                    max_climb=max(max_climb,peak-h0)
                    if hend>=h0: bad.append(row)
    print("PAIR_COUNTS",dict(sorted(pairs.items())))
    print("TRIPLE_COUNTS",dict(sorted(triples.items())))
    print("EXCURSIONS",len(excursions),"MAX_H",max_h,"MAX_CLIMB",max_climb)
    print("EXCURSION_RETURN_BELOW",len(excursions)-len(bad),"FAIL",len(bad))
    if bad:
        print("EXCURSION_SEPARATOR",bad[:20])
    else:
        print("OBSERVED_ALL_NON_DROP_EXCURSIONS_RETURN_BELOW_START")
    print("STATUS H_WALK_SPIKE")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,default=3)
    ap.add_argument("--hi",type=int,default=32767)
    ap.add_argument("--K",type=int,default=128)
    a=ap.parse_args();audit(a.lo,a.hi,a.K)
