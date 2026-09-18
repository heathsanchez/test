#!/usr/bin/env python3
"""Tournament universal q7 lower-predecessor schemas against q=0 component anchors.

Bounded theorem-discovery audit only.

The q7 reverse predecessor bank is independently verified by
collatz_reverse_predecessor_tree.py.  If an anchor lies in one of its killed
3-adic residue classes, it has an immediate universal lower-merge certificate
at the source itself.  Since every other member of the bounded component
already has a pre-descent coalescence reduction to the anchor, certifying the
anchor certifies the whole bounded component.

This scores q7 by component consequences eliminated, not raw residue density.
"""
from __future__ import annotations
import argparse
from collections import defaultdict,Counter

import collatz_q0_coalescence_component_audit as base
import collatz_reverse_predecessor_tree as pred

class UF:
    def __init__(self,items): self.p={x:x for x in items}
    def find(self,x):
        while self.p[x]!=x:
            self.p[x]=self.p[self.p[x]]; x=self.p[x]
        return x
    def union(self,a,b):
        a=self.find(a);b=self.find(b)
        if a==b:return
        if a>b:a,b=b,a
        self.p[b]=a

def pre_descent_path(n,H):
    y=n; out=[y]
    for _ in range(H):
        y=base.T(y);out.append(y)
        if y<n:break
    return out

def build_components(N,H):
    survivors=[]
    for n in range(3,N+1,2):
        ok,_=base.survives_to_q0(n)
        if ok and base.birth_status(n)[0]=="RIGID":
            survivors.append(n)
    uf=UF(survivors); owner={}
    for n in survivors:
        path=pre_descent_path(n,H)
        for y in path:
            m=owner.get(y)
            if m is not None and m<n:
                uf.union(n,m);break
        for y in path:
            if y not in owner or n<owner[y]: owner[y]=n
    comps=defaultdict(list)
    for n in survivors: comps[uf.find(n)].append(n)
    # union-find root is minimal because union always points larger root to smaller.
    return survivors,{min(v):v for v in comps.values()}

def q7_table():
    certs=pred.enumerate_first_contractions(7)
    killed, selected=pred.quotient(certs,7)
    assert (sum(killed),len(killed))==(1013,2187)
    return killed,selected

def direct_or_p(n,H):
    d=base.first_direct(n,H)
    p=base.first_immediate_lower_predecessor(n,H)
    cand=[]
    if d:cand.append((d[0],"D",d))
    if p:cand.append((p[0],"P",p))
    return min(cand) if cand else None

def audit(N,H):
    survivors,comps=build_components(N,H)
    killed,selected=q7_table()
    q7anchors=[];rem=[]
    members=0
    cert_hits=Counter()
    selected_certs=[c for c,_ in selected]
    for a,vs in sorted(comps.items()):
        r=a%2187
        if killed[r]:
            q7anchors.append(a);members+=len(vs)
            for c in selected_certs:
                if a%c.d==c.residue:
                    cert_hits[(c.d,c.residue,c.word)]+=1
                    break
        else: rem.append(a)

    # Characterize remaining anchors by current cheapest scalar fallback.
    hardest=[]
    uncert=[]
    for a in rem:
        cert=direct_or_p(a,H)
        if cert is None: uncert.append(a)
        else: hardest.append((cert[0],a,cert[1],cert[2]))
    hardest.sort(reverse=True)

    print("SOURCE_LIMIT",N)
    print("HEREDITARY_Q0_RIGID_SOURCES",len(survivors))
    print("COMPONENTS",len(comps))
    print("Q7_CERTIFICATES",len(selected))
    print("Q7_ANCHORS_CLOSED",len(q7anchors))
    print("Q7_COMPONENT_MEMBERS_CLOSED",members)
    print("Q7_ANCHOR_FRACTION",f"{len(q7anchors)}/{len(comps)}")
    print("REMAINING_ANCHORS",len(rem))
    print("TOP_Q7_CERTIFICATE_HITS",
          sorted(((v,k) for k,v in cert_hits.items()),reverse=True)[:13])
    print("HARDEST_REMAINING_FALLBACKS",hardest[:25])
    print("UNCERTIFIED_REMAINING",len(uncert),uncert[:20])
    print("FIRST_REMAINING_ANCHORS",rem[:30])
    if uncert:
        print("SEPARATOR_Q7_PLUS_DP_UNCERTIFIED",uncert[0])
    else:
        print("OBSERVED_Q7_PLUS_DP_CERTIFIES_ALL_BOUNDED_ANCHORS")
    print("STATUS BOUNDED_DISCOVERY_ONLY")
    print("MISSING_THEOREM recursive_universal_cover_of_component_anchors")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--N",type=int,default=65535)
    ap.add_argument("--H",type=int,default=512)
    a=ap.parse_args();audit(a.N,a.H)

if __name__=="__main__": main()
