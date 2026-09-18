#!/usr/bin/env python3
"""Spike: sign-refined coprimality for same-anchor return words.

Part A gives an exact counterexample to raw
  RIGID => gcd(B,2^D-3^R)=1:
source 111 stays hereditarily q=0 RIGID through a 16-step expanding
same-anchor return with gcd 5.

Part B exhausts every cyclic episode word of total shortcut length D<=20.
Among contracting-sign words (C=2^D-A>0) with gcd(B,C)>1, it asks whether
there exists an admissible positive odd m <= B/C. Such an m would be a
non-descending occurrence; an integral zero-defect fixed point is a special
case.  Up to D=20 the only such cases are repetitions of the trivial m=1
cycle.
"""
from __future__ import annotations
from itertools import combinations
from fractions import Fraction
from math import gcd
import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

def compositions(n,k):
    for cuts in combinations(range(1,n),k-1):
        prev=0; arr=[]
        for z in cuts+(n,):
            arr.append(z-prev);prev=z
        yield arr

def word_from_parts(parts):
    L=len(parts)//2
    rs=parts[0::2]; ss=parts[1::2]
    return tuple((rs[i],ss[i],rs[(i+1)%L]) for i in range(L))

def hereditary_rigid(n,K):
    ok,why=base.survives_to_q0(n)
    if not ok:return False,('pre_q0',why)
    for k in range(n.bit_length(),K+1):
        out,data=base.cylinder_status(k,n)
        if out!='RIGID':
            return False,(k,out,data)
    return True,None

# Exact raw-coprimality separator.
W=((4,1,2),(2,1,6),(6,2,4))
c=ra.certificate(W)
assert (c['A'],c['B'],c['D'],c['C'])==(3**12,c['B'],16,(1<<16)-3**12)
assert gcd(abs(c['B']),abs(c['C']))==5
m=c['rho']; n=(1<<c['r'])*m-1
assert n==111
assert ra.replay(c,m)==((base.forward_state(16,n)[1]+1)>>c['r'])
ok,why=hereditary_rigid(n,16)
assert ok,(n,why)
print("RAW_COPRIMALITY_SEPARATOR",n,W,c['A'],c['B'],c['D'],c['C'],
      gcd(abs(c['B']),abs(c['C'])))

words=0; contracting_gcd=0; nondec=[]
integral=[]
for D in range(2,21):
    for L in range(1,D//2+1):
        for parts in compositions(D,2*L):
            w=word_from_parts(parts)
            cc=ra.certificate(w)
            assert cc['D']==D
            words+=1
            C=cc['C']; B=cc['B']; g=gcd(abs(B),abs(C))
            if C<=0 or g<=1:
                continue
            contracting_gcd+=1
            q=Fraction(B,C)
            if q.denominator==1 and q.numerator>1:
                integral.append((D,w,q.numerator,g))
            m=cc['rho'] or cc['modulus']
            if m<=q:
                nondec.append((D,w,g,q,m))

print("WORDS_EXHAUSTED",words)
print("CONTRACTING_GCD_GT1_WORDS",contracting_gcd)
print("NONDESCENDING_ADMISSIBLE",len(nondec))
for z in nondec: print("NONDESCENDING",z)
print("NONTRIVIAL_INTEGRAL_FIXEDPOINTS",len(integral))
for z in integral[:20]: print("INTEGRAL",z)
if all(z[3]==Fraction(1,1) and z[4]==1 for z in nondec) and not integral:
    print("PASS_CONTRACTING_GCD_NONDESCENDING_ONLY_TRIVIAL_THROUGH_D20")
else:
    print("SEPARATOR_CONTRACTING_SIGN_COPRIMALITY_ROUTE")
print("STATUS FINITE_GRAMMAR_SPIKE_ONLY")
