#!/usr/bin/env python3
"""Bounded component-anchor audit for hereditary q=0 RIGID sources.

Discovery only, not a Collatz proof.

Nodes are fixed ordinary sources that survive all earlier cylinder
DESCEND/CLOSED/TAIL_CLOSED tests and arrive q=0 as RIGID.

For each node n, follow only its pre-descent trajectory.  If it intersects a
pre-descent trajectory previously owned by m<n, record a certified lower-
coalescence reduction n -> m.  Because sources are processed increasingly,
all such edges decrease the ordinary integer.  Components therefore collapse
to minimal anchors; only anchors require an independent certificate.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import collatz_q0_coalescence_component_audit as base

class UF:
    def __init__(self,items):
        self.p={x:x for x in items}
    def find(self,x):
        while self.p[x]!=x:
            self.p[x]=self.p[self.p[x]]
            x=self.p[x]
        return x
    def union(self,a,b):
        a=self.find(a);b=self.find(b)
        if a==b:return
        if a>b:a,b=b,a
        self.p[b]=a

def pre_descent_path(n:int,H:int):
    y=n; out=[y]
    for _ in range(H):
        y=base.T(y);out.append(y)
        if y<n:
            return out,True
    return out,False

def audit(N:int,H:int):
    survivors=[]
    for n in range(3,N+1,2):
        ok,_=base.survives_to_q0(n)
        if not ok: continue
        st,_=base.birth_status(n)
        if st=="RIGID":
            survivors.append(n)

    uf=UF(survivors)
    owner={}
    reductions=[]
    paths={}
    for n in survivors:
        path,desc=pre_descent_path(n,H)
        paths[n]=(path,desc)
        best=None
        for t,y in enumerate(path):
            m=owner.get(y)
            if m is not None and m<n:
                best=(m,t,y)
                break
        if best is not None:
            m,t,y=best
            reductions.append((n,m,t,y))
            uf.union(n,m)
        for y in path:
            old=owner.get(y)
            if old is None or n<old:
                owner[y]=n

    comps=defaultdict(list)
    for n in survivors:
        comps[uf.find(n)].append(n)
    rows=sorted(((min(v),len(v),max(v)) for v in comps.values()),
                key=lambda x:(-x[1],x[0]))
    anchors=sorted(min(v) for v in comps.values())

    cert=Counter();uncert=[];max_cert=0;anchor_examples=[]
    for n in anchors:
        d=base.first_direct(n,H)
        p=base.first_immediate_lower_predecessor(n,H)
        candidates=[]
        if d is not None:candidates.append((d[0],"D",d))
        if p is not None:candidates.append((p[0],"P",p))
        if candidates:
            best=min(candidates)
            cert[best[1]]+=1;max_cert=max(max_cert,best[0])
            if len(anchor_examples)<30:
                anchor_examples.append((n,best))
        else:
            uncert.append(n)

    print("SOURCE_LIMIT",N)
    print("HEREDITARY_Q0_RIGID_SOURCES",len(survivors))
    print("PRE_DESCENT_REDUCTION_EDGES",len(reductions))
    print("COALESCENCE_COMPONENTS",len(comps))
    print("COMPONENT_ANCHORS",len(anchors))
    print("LARGEST_COMPONENTS",rows[:20])
    print("ANCHOR_CERTIFICATES",dict(cert))
    print("MAX_ANCHOR_CERTIFICATE_STEPS",max_cert)
    print("UNCERTIFIED_ANCHORS",len(uncert),uncert[:30])
    for row in anchor_examples:
        print("ANCHOR_WITNESS",row)
    if uncert:
        print("SEPARATOR_UNCERTIFIED_COMPONENT_ANCHOR",uncert[0])
    else:
        print("OBSERVED_ALL_BOUNDED_COMPONENT_ANCHORS_CERTIFIED")
    print("STATUS BOUNDED_DISCOVERY_ONLY")
    print("MISSING_THEOREM parameterized_component_anchor_termination")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--N",type=int,default=65535)
    ap.add_argument("--H",type=int,default=512)
    a=ap.parse_args();audit(a.N,a.H)

if __name__=="__main__":
    main()
