#!/usr/bin/env python3
"""Exact endpoint-trit compiler from the last b odd positions of a parity word.

For shortcut Collatz,
  2^t T^t(n) = 3^q n + A_t.
Modulo 3^b with q>=b, the source term vanishes. Also
  A_t = sum_{odd positions j} 2^j 3^(# later odd positions),
so modulo 3^b every contribution before the last b odd positions vanishes.
Thus the endpoint residue mod 3^b is compiled from only those b positions.

This file exhaustively/randomly replays the identity; the algebra above is the
authority statement to formalize next, not a Collatz proof.
"""
import json,random

def T(n): return n//2 if n%2==0 else (3*n+1)//2

def trace(n,t):
    x=n; odds=[];A=0;q=0
    for j in range(t):
        if x&1:
            odds.append(j);q+=1;A=3*A+(1<<j)
        x=T(x)
    assert (1<<t)*x==3**q*n+A
    return x,odds,A,q

def compiled(odds,t,b):
    assert len(odds)>=b>=1
    P=3**b
    last=odds[-b:]
    a=0
    for j in last:
        a=(3*a+pow(2,j,P))%P
    return a*pow(pow(2,t,P),-1,P)%P

checks=0
for n in range(1,2049):
    for t in (16,32,64,96):
        y,odds,A,q=trace(n,t)
        for b in range(1,min(8,q)+1):
            assert compiled(odds,t,b)==y%(3**b)
            checks+=1

rng=random.Random(26092026)
for _ in range(512):
    n=rng.getrandbits(72)|1
    t=rng.choice((96,128,192,256,384))
    y,odds,A,q=trace(n,t)
    for b in (1,2,5,10,20):
        if q>=b:
            assert compiled(odds,t,b)==y%(3**b)
            checks+=1

P=3**20
phi=2*3**19
result={
 "schema":"COLLATZ_ENDPOINT_TRIT_SUFFIX_V0",
 "checks":checks,
 "target_b":20,
 "target_modulus":P,
 "position_period_mod_3pow20":phi,
 "law":"for q>=b, T^t(n) mod 3^b is determined solely by t and the last b odd-step positions",
 "source_term_vanishes_mod_3powb":True,
 "older_odd_contributions_vanish_mod_3powb":True,
 "crystal_binding_input":["t mod phi(3^20)","last 20 odd positions mod phi(3^20)"],
 "crystal_binding_output":"endpoint residue mod 3^20",
 "remaining_source_admission":"relate minimal-bad source residue mod 3^20 to this compiled endpoint residue",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
