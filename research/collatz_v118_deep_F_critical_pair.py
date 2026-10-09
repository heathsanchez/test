"""Exact source-attached V118 deep F critical pair.

For EVERY z>=0,
  n=19107135+23887872*z, p=13419551+16777216*z:
  T^15(n)=T^24(p), 0<p<n.
The full first 15 actual shortcut prefix has no direct descent or
strict source-capped ternary hit, uniformly in z by affine coefficients.
This is one congruence family, NOT universal Collatz.
"""
import json
import hashlib

N0, NM = 19107135, 23887872
P0, PM = 13419551, 16777216


def T(n):
    return n//2 if n%2==0 else (3*n+1)//2


def affine_step(base,slope):
    assert slope%2==0
    if base%2==0:
        return base//2,slope//2
    return (3*base+1)//2,3*slope//2


def main():
    n0,nm=N0,NM
    f0,fm=3*N0+2,3*NM
    prefixes=[]
    for k in range(1,16):
        assert nm%2==0 and fm%2==0
        n0,nm=affine_step(n0,nm)
        f0,fm=affine_step(f0,fm)
        # Both inequalities hold for EVERY nonnegative family offset.
        assert n0>=N0 and nm>=NM
        if n0%3==2:
            # Source-capped cone is STRICT, so equality is no exit.
            assert 2*n0-1>=3*N0
            assert 2*nm>=3*NM
        prefixes.append(dict(
            k=k,endpoint_intercept=n0,endpoint_slope=nm,
            F_intercept=f0,F_slope=fm,
            capped_hit=False,direct_descent=False))
    assert (n0,nm)==(f0,fm)==(34431680,43046721)
    # Symbolic reverse word already proved from target F(45+729*q).
    assert N0==3391+32768*583
    assert N0==45+729*26210
    assert P0==31+512*26210
    assert NM==32768*729 and PM==512*32768
    assert 0<P0<N0 and 0<PM<NM
    words='OEOEOOOOO'
    x,c=3*45+2,3*729
    for op in words:
        if op=='E':x,c=2*x,2*c
        else:
            assert op=='O' and x%3==2 and c%3==0
            ox,oc=x,c
            x,c=(2*x-1)//3,2*c//3
            assert 3*x+1==2*ox and 3*c==2*oc
    assert (x,c)==(31,512)
    regressions=[]
    for z in (0,1,2,7,33):
        n,p=N0+NM*z,P0+PM*z
        assert 0<p<n
        yy=n
        for j in range(15):
            yy=T(yy)
            assert yy>=n
            assert not (yy%3==2 and 2*yy-1<3*n)
        w=p
        for _ in range(24):
            w=T(w)
        assert w==yy==34431680+43046721*z
        regressions.append(dict(offset=z,n=n,p=p,common_endpoint=yy))
    result=dict(schema='COLLATZ_DEEP_F_15_STEP_SOURCE_COHERENT_MERGER',
        status='BOUNDED_EXACT_SYMBOLIC_FAMILY',
        source_base=N0,source_slope=NM,
        predecessor_base=P0,predecessor_slope=PM,
        source_clock=15,predecessor_clock=24,
        no_direct_descent_prefix_length=15,
        no_source_capped_hit_prefix_length=15,
        exact_prefix_records=prefixes,
        regressions=regressions,
        global_collatz='UNKNOWN',qed=False,
        universal_natural_source_bar=False)
    canonical=json.dumps(result,sort_keys=True,separators=(',',':'))
    result['payload_sha256']=hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':
    main()
