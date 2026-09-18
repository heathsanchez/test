#!/usr/bin/env python3
"""Search for simple well-founded state potentials on exact RIGID return switches.

A state is a completed return pattern c together with its residual separation
h to the next distinct pattern. For consecutive distinct switches
W->V->U, the exact transport law identifies:
  old state = (W, h(W,V))
  new state = (V, h(V,U)).

We test low-complexity scalar and lexicographic features prospectively:
D, h, slack=D+1-h, bit lengths of fixed-point numerator/denominator,
and the prime-to-6 defect core at the completed state.

This is discovery only. Any candidate is trained on sources <=8191 and must
survive a disjoint held-out range 8193..32767.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from itertools import product
import collatz_q0_rigid_recharge_audit as ra

def vp(x,p):
    x=abs(x);v=0
    if x==0:return 10**9
    while x%p==0:x//=p;v+=1
    return v

def core6(x):
    x=abs(x); assert x
    while x%2==0:x//=2
    while x%3==0:x//=3
    return x

def defect(c,m):
    p,u=c['q']; return u*m-p

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
            assert ra.admissible(c,m0)
            assert ra.replay(c,m0)==m1
            out[r].append((c,m0,m1,starts[start][0]))
        last[r]=end
    return out

def feature(c,h,m_after):
    p,u=c['q']
    E=defect(c,m_after)
    assert E
    return {
        'D':c['D'],
        'h':h,
        'slack':c['D']+1-h,
        'pbits':abs(p).bit_length(),
        'ubits':u.bit_length(),
        'qbits':max(abs(p).bit_length(),u.bit_length()),
        'kbits':core6(E).bit_length(),
        'v3':vp(E,3),
    }

def edges(lo,hi,K):
    E=[]
    start=max(3,lo)
    if start%2==0:start+=1
    for n in range(start,hi+1,2):
        for r,seq in returns(n,K).items():
            sw=[]
            for i in range(len(seq)-1):
                w,m0,m1,k0=seq[i]
                v,n0,n1,k1=seq[i+1]
                assert m1==n0
                if w['q']==v['q']:continue
                z=ra.switch_law(w,v,n0,n1)
                if z is None:continue
                sw.append((i,w,v,z,m1,n1))
            # Need adjacent switches: W->V and V->U.
            for a,b in zip(sw,sw[1:]):
                i,w,v,z,m1,n1=a
                j,v2,u,z2,m2,m3=b
                if j!=i+1 or v['q']!=v2['q']:
                    continue
                # completed W state at m1 has h=z.h;
                # completed V state at n1=m2 has h=z2.h.
                old=feature(w,z['h'],m1)
                new=feature(v,z2['h'],n1)
                E.append((n,r,z['outcome'],z2['outcome'],old,new,w['q'],v['q'],u['q']))
    return E

FEATURES=['D','h','slack','pbits','ubits','qbits','kbits','v3']

def dot(w,f):
    return sum(a*f[k] for a,k in zip(w,FEATURES))

def search_weights(train,limit=3):
    found=[]
    vals=range(-limit,limit+1)
    for w in product(vals,repeat=len(FEATURES)):
        if all(x==0 for x in w):continue
        # normalize first nonzero positive to avoid sign duplicates where possible
        first=next(x for x in w if x)
        if first<0:continue
        if all(dot(w,e[5]) < dot(w,e[4]) for e in train):
            found.append(w)
            if len(found)>=20:break
    return found

def simple_tests(E):
    tests={}
    for k in FEATURES:
        tests[k+'_DOWN']=sum(e[5][k]<e[4][k] for e in E)
        tests[k+'_UP']=sum(e[5][k]>e[4][k] for e in E)
        tests[k+'_EQ']=sum(e[5][k]==e[4][k] for e in E)
    return tests

def audit(K):
    train=edges(3,8191,K)
    held=edges(8193,32767,K)
    print("TRAIN_EDGES",len(train))
    print("HELD_EDGES",len(held))
    print("SIMPLE_TRAIN",simple_tests(train))
    ws=search_weights(train,2)
    print("LINEAR_CANDIDATES",len(ws))
    for w in ws:
        bad=[e for e in held if not dot(w,e[5])<dot(w,e[4])]
        print("WEIGHT",dict(zip(FEATURES,w)),"HELD_PASS",len(held)-len(bad),
              "HELD_FAIL",len(bad),"FIRST_FAIL",bad[0] if bad else None)
    # Explicit lexicographic pairs, both orientations where lower is better.
    lex=[]
    for a in FEATURES:
        for b in FEATURES:
            if a==b:continue
            bad=[e for e in train if not ((e[5][a],e[5][b])<(e[4][a],e[4][b]))]
            if not bad:
                lex.append((a,b))
    print("LEX_CANDIDATES",lex)
    for a,b in lex:
        bad=[e for e in held if not ((e[5][a],e[5][b])<(e[4][a],e[4][b]))]
        print("LEX",a,b,"HELD_FAIL",len(bad),"FIRST_FAIL",bad[0] if bad else None)
    if not ws and not lex:
        print("NO_SIMPLE_GLOBAL_SWITCH_RANK_ON_TRAIN")
    print("STATUS SWITCH_STATE_RANK_SPIKE")

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--K",type=int,default=128)
    a=ap.parse_args();audit(a.K)
