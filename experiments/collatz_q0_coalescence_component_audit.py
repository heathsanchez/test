#!/usr/bin/env python3
"""Bounded q=0 RIGID coalescence-component audit.

This is theorem-discovery evidence, not a Collatz proof.

For each odd source n <= N:
  * classify its q=0 birth cylinder at k=bit_length(n) using an exact
    Complete-O search bounded by the source replay cost k;
  * retain only RIGID birth sources;
  * test whether every RIGID source n>27 coalesces with the certified
    anchor orbit of 27;
  * independently verify explicit lower-merge certificates for the six
    small RIGID anchors <=27.

The intended lesson is component compression: many hard q=0 sources may be
different presentations of one already-certified coalescence basin.
"""
from __future__ import annotations
import argparse
from collections import Counter

def T(n:int)->int:
    return n//2 if n%2==0 else (3*n+1)//2

def forward_state(k:int,b:int):
    d=b;c=0
    for _ in range(k):
        if d&1:
            d=(3*d+1)//2;c+=1
        else:
            d//=2
    return c,d

def best_complete_o_within_source_cost(k:int,b:int):
    """Exact lexicographic optimum (total cost, terminal integer) for S<=k.

    The source replay itself has total cost k, so no optimizer relevant to
    CLOSED/TAIL_CLOSED/RIGID can have cost >k.
    """
    c,d=forward_state(k,b)
    if c==0:
        return None
    cur={(d,0)}
    for j in range(c):
        rem=c-j-1
        nxt={}
        for x,S in cur:
            max_a=k-S-rem
            for a in range(1,max_a+1):
                num=(1<<a)*x-1
                if num%3:
                    continue
                y=num//3
                if y<=0:
                    continue
                S2=S+a
                old=nxt.get(y)
                if old is None or S2<old:
                    nxt[y]=S2
        cur={(y,S) for y,S in nxt.items()}
        if not cur:
            return None
    return min(((S,y) for y,S in cur),key=lambda z:(z[0],z[1]))

def birth_status(n:int):
    k=n.bit_length()
    c,d=forward_state(k,n)
    if d<n:
        return "DESCEND",(k,c,d)
    opt=best_complete_o_within_source_cost(k,n)
    if opt is None:
        raise AssertionError(("missing source replay",n,k,c,d))
    S,x=opt
    if S<k:
        return "TAIL_CLOSED",(k,c,d,S,x)
    if S==k and x<n:
        return "CLOSED",(k,c,d,S,x)
    if S==k and x==n:
        return "RIGID",(k,c,d,S,x)
    raise AssertionError(("optimizer worse than source",n,k,c,d,opt))

def orbit_map(n:int,H:int):
    y=n; out={y:0}
    for t in range(1,H+1):
        y=T(y)
        out.setdefault(y,t)
        if y==1:
            # continue a few steps is unnecessary: 1/2 cycle adds no new
            # large coalescence targets.
            break
    return out

def first_direct(n:int,H:int):
    y=n
    for t in range(1,H+1):
        y=T(y)
        if y<n:
            return t,y
    return None

def first_immediate_lower_predecessor(n:int,H:int):
    y=n
    for t in range(1,H+1):
        y=T(y)
        if y%3==2:
            p=(2*y-1)//3
            if 0<p<n and T(p)==y:
                return t,y,p
    return None

def audit(N:int,H:int):
    anchor_orbit=orbit_map(27,H)
    assert anchor_orbit.get(23)==59, anchor_orbit.get(23)
    # Explicit anchor certificates. 15 uses lower predecessor 13 at endpoint 20.
    expected={
        3:("D",4,2),
        7:("D",7,5),
        9:("D",2,7),
        11:("D",5,10),
        15:("P",6,20,13),
        27:("D",59,23),
    }
    for n,w in expected.items():
        if w[0]=="D":
            got=first_direct(n,H)
            assert got==(w[1],w[2]),(n,got,w)
        else:
            got=first_immediate_lower_predecessor(n,H)
            assert got==(w[1],w[2],w[3]),(n,got,w)

    counts=Counter(); rigid=[]; misses=[]; examples=[]; max_hit=0
    for n in range(3,N+1,2):
        st,_=birth_status(n)
        counts[st]+=1
        if st!="RIGID":
            continue
        rigid.append(n)
        if n<=27:
            continue
        y=n; hit=None; descended=None
        for t in range(H+1):
            if t>0 and y<n:
                descended=(t,y)
                break
            if y in anchor_orbit:
                hit=(t,y,anchor_orbit[y]);break
            y=T(y)
        if hit is None:
            misses.append((n,descended))
            if len(examples)<20:
                examples.append((n,"NO_PRE_DESCENT_27_HIT",descended))
        else:
            max_hit=max(max_hit,hit[0])
            if len(examples)<20 and n in (31,47,71,91,103,111,155,167,251):
                examples.append((n,hit))

    print("SOURCE_LIMIT",N)
    print("BIRTH_OUTCOMES",dict(sorted(counts.items())))
    print("RIGID_BIRTH_SOURCES",len(rigid))
    print("SMALL_RIGID_ANCHORS",[n for n in rigid if n<=27])
    print("ANCHOR_27_DIRECT_CERT t=59 endpoint=23")
    print("RIGID_GT27_PRE_DESCENT_COALESCE_TO_27",len([n for n in rigid if n>27])-len(misses))
    print("MAX_STEPS_TO_27_BASIN",max_hit)
    print("PRE_DESCENT_COALESCENCE_MISSES",len(misses))
    for x in examples:
        print("WITNESS",x)
    if misses:
        print("SEPARATOR_OUTSIDE_PRE_DESCENT_27_COMPONENT",misses[:20])
    else:
        print("OBSERVED_ALL_TESTED_HARD_CHAMPIONS_PRE_DESCENT_COALESCE_TO_27")
    print("STATUS BOUNDED_DISCOVERY_ONLY")
    print("MISSING_THEOREM characterize_pre_descent_coalescence_components_and_terminate_anchors")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--N",type=int,default=65535)
    ap.add_argument("--H",type=int,default=512)
    a=ap.parse_args()
    audit(a.N,a.H)

if __name__=="__main__":
    main()
