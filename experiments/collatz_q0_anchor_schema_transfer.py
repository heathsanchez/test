#!/usr/bin/env python3
"""Prospective transfer of compiled q=0 component-anchor certificates.

Train on component anchors up to N_train.  For each anchor, compile its cheapest
exact direct-descent (D) or immediate-lower-predecessor (P) witness into a
binary source-cylinder rule.  Freeze the bank.  Rebuild components up to a
larger N_test and measure coverage of genuinely new anchors without acquiring
new rules.

This is theorem-discovery evidence, not a global Collatz proof.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from collections import Counter

import collatz_q0_coalescence_component_audit as base
import collatz_q0_anchor_q7_tournament as q7


@dataclass(frozen=True)
class DRule:
    t:int; residue:int; A:int; B:int; minimum:int
    def applies(self,n:int)->bool:
        return n>=self.minimum and n%(1<<self.t)==self.residue


@dataclass(frozen=True)
class PRule:
    t:int; residue:int; seed:int; c:int; y0:int; p0:int
    def applies(self,n:int)->bool:
        if n<self.seed or n%(1<<self.t)!=self.residue:
            return False
        q=(n-self.seed)>>self.t
        p=self.p0 + 2*(3**(self.c-1))*q
        return 0<p<n


def prefix_affine(n:int,t:int):
    x=n; A=1; B=0; c=0
    for j in range(t):
        if x&1:
            A=3*A; B=3*B+(1<<j); c+=1
        x=base.T(x)
    assert A*n+B==(1<<t)*x
    return A,B,c,x


def compile_D(n:int,w):
    t,y=w
    A,B,c,y2=prefix_affine(n,t)
    assert y2==y and y<n and A<(1<<t)
    minimum=B//((1<<t)-A)+1
    return DRule(t,n%(1<<t),A,B,minimum)


def compile_P(n:int,w):
    t,y,p=w
    A,B,c,y2=prefix_affine(n,t)
    assert y2==y and y%3==2 and p==(2*y-1)//3 and 0<p<n and base.T(p)==y
    if c==0:
        return None
    # On n(q)=n+2^t q, endpoint y(q)=y+3^c q and
    # p(q)=p+2*3^(c-1)q.  Require asymptotic lower slope.
    if 2*(3**(c-1)) >= (1<<t):
        return None
    return PRule(t,n%(1<<t),n,c,y,p)


def anchor_cert(n,H):
    d=base.first_direct(n,H)
    p=base.first_immediate_lower_predecessor(n,H)
    cand=[]
    if d is not None: cand.append((d[0],"D",d))
    if p is not None: cand.append((p[0],"P",p))
    return min(cand) if cand else None


def build_bank(N,H):
    _,comps=q7.build_components(N,H)
    anchors=sorted(comps)
    bank=[];stats=Counter();failed=[]
    for a in anchors:
        cert=anchor_cert(a,H)
        if cert is None:
            failed.append(a);continue
        _,kind,w=cert
        rule=compile_D(a,w) if kind=="D" else compile_P(a,w)
        if rule is None:
            stats["nontransferable_"+kind]+=1
            continue
        bank.append(rule);stats[kind]+=1
    return anchors,bank,stats,failed


def dedupe(bank):
    # Same semantic rule key: retain one copy.  D rules can share exact affine
    # consequence; P rules share the learned seed threshold and affine family.
    uniq={}
    for r in bank:
        if isinstance(r,DRule):
            key=("D",r.t,r.residue,r.A,r.B,r.minimum)
        else:
            key=("P",r.t,r.residue,r.seed,r.c,r.y0,r.p0)
        uniq[key]=r
    return list(uniq.values())


def cover(bank,n):
    for r in bank:
        if r.applies(n):
            return r
    return None


def audit(Ntrain,Ntest,H):
    train_anchors,bank,stats,failed=build_bank(Ntrain,H)
    bank=dedupe(bank)
    _,test_comps=q7.build_components(Ntest,H)
    test_anchors=sorted(test_comps)
    new=[a for a in test_anchors if a>Ntrain]
    hits=[];miss=[]
    hitkind=Counter()
    for a in new:
        r=cover(bank,a)
        if r is None: miss.append(a)
        else:
            hits.append(a);hitkind["D" if isinstance(r,DRule) else "P"]+=1

    print("TRAIN_LIMIT",Ntrain)
    print("TEST_LIMIT",Ntest)
    print("TRAIN_ANCHORS",len(train_anchors))
    print("COMPILED_RULES",len(bank),dict(stats))
    print("TRAIN_UNCERTIFIED",len(failed),failed[:20])
    print("TEST_ANCHORS",len(test_anchors))
    print("NEW_ANCHORS",len(new))
    print("FROZEN_NEW_ANCHOR_HITS",len(hits),dict(hitkind))
    print("FROZEN_NEW_ANCHOR_MISSES",len(miss),miss[:30])
    if miss:
        print("SEPARATOR_FROZEN_ANCHOR_SCHEMA_TRANSFER",miss[0])
    else:
        print("OBSERVED_FROZEN_ANCHOR_SCHEMAS_COVER_ALL_NEW_ANCHORS")
    print("STATUS BOUNDED_PROSPECTIVE_TRANSFER_ONLY")
    print("MISSING_THEOREM recursive_universal_anchor_schema_cover")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--train",type=int,default=65535)
    ap.add_argument("--test",type=int,default=262143)
    ap.add_argument("--H",type=int,default=512)
    a=ap.parse_args()
    audit(a.train,a.test,a.H)
