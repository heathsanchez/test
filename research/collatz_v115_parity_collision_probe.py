"""V115 independent symbolic regression of the parity collision mechanism.

This checks exact all-offset affine shortcuts on test congruence cylinders
through variable odd-run depths. The *universal* theorem requires Lean.
No finite test or numeric density establishes global Collatz.
"""
import json
from collections import Counter

def shortcut(n):
    return n//2 if n%2==0 else (3*n+1)//2

def affine_shortcut(base,slope):
    # For all t>=0, base+slope*t has fixed parity only if slope is even.
    assert slope%2==0
    if base%2==0:
        return base//2,slope//2
    return (3*base+1)//2,3*slope//2

def residue_for_bits(bits):
    r=0
    for k,bit in enumerate(bits):
        x=r
        for _ in range(k):x=shortcut(x)
        if x%2!=bit:r+=2**k
    return r

def crt_base(r,depth):
    dyad=2**depth
    s=((60-r)*pow(dyad,-1,81))%81
    return r+dyad*s

def inspect(k):
    # Exact original source parity critical pair: 1^k 0 1.
    bits=[1]*k+[0,1]
    r=residue_for_bits(bits)
    n0=crt_base(r,k+2)
    if n0<=1:n0+=81*(2**(k+2))
    assert n0%81==60 and n0%(2**(k+2))==r
    q=(n0-60)//81
    p0=64*q+47
    M=81*(2**(k+2))
    P=64*(2**(k+2))
    assert 0<p0<n0 and 0<P<M
    # For ALL offsets t, odd-run/even/odd shortcut parity is fixed.
    x,a=n0,M
    y,b=3*n0+2,3*M
    for j,bit in enumerate(bits):
        assert x%2==bit
        assert a%2==0
        x,a=affine_shortcut(x,a)
        assert b%2==0
        y,b=affine_shortcut(y,b)
    assert (x,a)==(y,b)
    # Exact six-step source predecessor formula and affine slope.
    u,v=p0,P
    for _ in range(6):
        u,v=affine_shortcut(u,v)
    assert (u,v)==(3*n0+2,3*M)
    # The actual clocks are k+2 and k+8.
    z,c=p0,P
    for _ in range(k+8):
        z,c=affine_shortcut(z,c)
    assert (z,c)==(x,a)
    # Sanity on distinct natural sources; samples are not the proof.
    for t in (0,1,7):
        n=n0+M*t;p=p0+P*t
        assert 0<p<n
        nn=n;pp=p
        for _ in range(k+2):nn=shortcut(nn)
        for _ in range(k+8):pp=shortcut(pp)
        assert nn==pp
    return dict(k=k,dyadic_residue=r,source=n0,
                predecessor=p0,source_slope=M,predecessor_slope=P,
                source_clock=k+2,predecessor_clock=k+8)

def main():
    cases=[inspect(k) for k in range(0,41)]
    assert len(cases)==41
    data=dict(schema="COLLATZ_V115_PARITY_COLLISION_PROBE",
              status="BOUNDED_EXACT_REGRESSION_FORMAL_CANDIDATE",
              global_collatz="UNKNOWN",qed=False,
              tested_odd_run_depth_min=0,tested_odd_run_depth_max=40,
              exact_offset_affine_trace_cases=len(cases),
              general_six_step_predecessor=True,
              source_relative_protection=True,
              universal_parity_theorem_lean_qualified=False,
              examples=[cases[k] for k in (0,2,3,4,10,20,40)])
    print(json.dumps(data,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
