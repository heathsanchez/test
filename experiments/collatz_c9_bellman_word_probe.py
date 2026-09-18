#!/usr/bin/env python3
"""Spike: recover exact Complete-O optimal words for repeated C9 return cylinders."""
from __future__ import annotations
import collatz_q0_coalescence_component_audit as base

A=729;B=467;D=9;R=6
C=(1<<D)-A

def start_m(t:int):
    bits=t*D+1
    return (B*pow(C,-1,1<<bits))%(1<<bits)

def optimal_word(k:int,b:int):
    c,d=base.forward_state(k,b)
    cur={(d,0):()}
    for j in range(c):
        rem=c-j-1
        nxt={}
        for (x,S),w in cur.items():
            max_a=k-S-rem
            for a in range(1,max_a+1):
                num=(1<<a)*x-1
                if num%3: continue
                y=num//3
                if y<=0: continue
                key=(y,S+a)
                ww=w+(a,)
                old=nxt.get(key)
                if old is None or ww<old:
                    nxt[key]=ww
        # keep only cheapest S for each y
        best={}
        for (y,S),w in nxt.items():
            old=best.get(y)
            if old is None or S<old[0] or (S==old[0] and w<old[1]):
                best[y]=(S,w)
        cur={(y,S):w for y,(S,w) in best.items()}
    cand=[(S,y,w) for (y,S),w in cur.items()]
    return min(cand,key=lambda z:(z[0],z[1],z[2]))

block=None
for t in range(1,9):
    m=start_m(t); b=2*m-1
    S,y,w=optimal_word(9*t,b)
    chunks=[w[i:i+6] for i in range(0,len(w),6)]
    if t==1: block=w
    periodic=(len(w)==6*t and all(ch==block for ch in chunks))
    print("OPT",t,"S",S,"y",y,"periodic",periodic,"word",w)
    assert S==9*t and y==b
print("BLOCK",block)
print("STATUS COMPLETE_O_PERIODIC_WORD_SPIKE")
