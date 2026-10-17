#!/usr/bin/env python3
"""Exact source-pinned P-224 root-sign isomorphism / P-256 twist distinction.

Not an NSA generator reconstruction, cryptographic exploit, or Lean-certified theorem.
"""
import hashlib,json,subprocess
from pathlib import Path
from v7_zsqrt import data_row,original_zsqrtmod


def is_on(P,p,a,b):
    if P is None:return True
    x,y=P
    return y*y%p==(x*x*x+a*x+b)%p

def add(P,Q,p,a):
    if P is None:return Q
    if Q is None:return P
    x1,y1=P;x2,y2=Q
    if x1==x2 and (y1+y2)%p==0:return None
    if x1==x2:
        if y1%p==0:return None
        lam=((3*x1*x1+a)*pow(2*y1,-1,p))%p
    else:
        lam=((y2-y1)*pow((x2-x1)%p,-1,p))%p
    x3=(lam*lam-x1-x2)%p
    y3=(lam*(x1-x3)-y1)%p
    return x3,y3

def find_points(p,a,b,count):
    ps=[];j=0
    while len(ps)<count and j<count*15:
        rhs=(j*j*j+a*j+b)%p
        if rhs and pow(rhs,(p-1)//2,p)==1:
            y=original_zsqrtmod(rhs,p)[0]
            assert y is not None
            assert y*y%p==rhs
            ps.append((j,y))
        j+=1
    if len(ps)<count:raise AssertionError('too few validated curve points')
    return ps,j

def main():
    r224=data_row('secp224r1');r256=data_row('prime256v1')
    p224,b224=int(r224['p_hex'],16),int(r224['source_b_hex'],16)
    p256,b256=int(r256['p_hex'],16),int(r256['source_b_hex'],16)
    assert p224%4==1 and p256%4==3
    assert pow(p224-1,(p224-1)//2,p224)==1
    assert pow(p256-1,(p256-1)//2,p256)==p256-1
    q=3
    while pow(q,(p224-1)//2,p224)!=p224-1:q+=1
    u=pow(q,(p224-1)//4,p224)
    assert u*u%p224==p224-1
    a=-3
    points,xvisited=find_points(p224,a,b224,64)
    def phi(P):
        if P is None:return None
        return ((-P[0])%p224,(u*P[1])%p224)
    invu=pow(u,-1,p224)
    def phi_inv(P):
        if P is None:return None
        return ((-P[0])%p224,(invu*P[1])%p224)
    assert phi(None) is None and phi_inv(None) is None
    for P in points:
        assert is_on(P,p224,a,b224)
        Q=phi(P)
        assert is_on(Q,p224,a,-b224)
        assert phi_inv(Q)==P
    laws=[]
    for i in range(24):
        P=points[i];Q=points[63-i]
        S=add(P,Q,p224,a)
        S2=add(phi(P),phi(Q),p224,a)
        assert is_on(S,p224,a,b224)
        assert is_on(S2,p224,a,-b224)
        assert phi(S)==S2
        laws.append((i,63-i))
    for P in points[:12]:
        neg=(P[0],(-P[1])%p224)
        assert phi(neg)==(phi(P)[0],(-phi(P)[1])%p224)
    # Deliberate P-256 mutant: choose candidates that DO NOT square to -1.
    misses=[u0 for u0 in (0,1,2) if (u0*u0)%p256!=p256-1]
    assert len(misses)==3
    GX=int('6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296',16)
    GY=int('4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5',16)
    assert is_on((GX,GY),p256,a,b256)
    for fake_u in misses:
        P=((-GX)%p256,(fake_u*GY)%p256)
        assert not is_on(P,p256,a,-b256)
    # P-224 b choices are not equal as field elements but are isomorphic curves.
    assert b224!=(-b224)%p224
    assert r224['original_zsqrtmod_matches_published_b'] is False
    assert r256['original_zsqrtmod_matches_published_b'] is True
    out={
      'status':'PASS_EXACT_FIELD_ISOMORPHISM_BOUNDARY; NOT_LEAN_CERTIFIED',
      'historical_use':'UNKNOWN',
      'old_v7_native_green_run':38992150553,
      'p224':{
        'p_hex':r224['p_hex'],'published_b':r224['source_b_hex'],
        'freeLIP_b':r224['original_zsqrtmod_b_hex'],
        'quadratic_nonresidue':q,'sqrt_minus_one':hex(u),
        'u_squared_is_minus_one':True,'mutual_inverse_map_points':64,
        'additional_law_pairs':24,'negation_pairs':12,
        'sample_x_examined':xvisited,
        'group_order_relation':'#E_b = #E_{-b} by explicit Fp-isomorphism',
        'prime_order_independent_census':'NOT_NEEDED_FOR_EQUIVALENCE',
      },
      'p256':{
        'p_hex':r256['p_hex'],'published_b':r256['source_b_hex'],
        'minus_one_legendre':-1,'no_sqrt_minus_one_in_Fp':True,
        'invalid_fake_u_checks':len(misses),
        'root_paired_curve_relation':'quadratic twist: #E_b + #E_{-b}=2(p+1) (standard nonsingular case)',
        'actual_pair_prime_status':'V5 skipped candidate 876 b_hi prime / b_lo composite',
      },
      'symbolic_proof':'X=-x, Y=u*y; Y^2=-(x^3+a*x+b)=X^3+a*X-b when u^2=-1; inverse X->-X,Y->u^-1*Y; group law transported by nonsingular Weierstrass coordinate change.',
      'next_residual':'authentic 1997-98 source or prospective P224 candidate-selection experiment; origin G remains unknown',
      'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'evidence_oracle':'NIST named-source parameters via openssl; reused V7 exact source-translated modular sqrt for construction of test points',
    }
    target=Path(__file__).with_name('V8_RESULTS.json');target.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'p224':{'isomorphism_points':64,'addition_pairs':24,'u':hex(u)},'p256':{'no_field_sqrt_minus_one':True,'mutant_failures':3},'out':str(target)},indent=2))
if __name__=='__main__':main()
