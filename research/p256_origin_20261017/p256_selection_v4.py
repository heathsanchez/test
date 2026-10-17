#!/usr/bin/env python3
"""V4 exact P-256 candidate-selection audit.  Prime order of skipped 876 is EXTERNAL, not computed."""
import ctypes
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

P = int('FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF', 16)
N = int('FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551', 16)
B = int('5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B', 16)
G = (int('6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296', 16),
     int('4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5', 16))
SEED1842 = 'C49D360886E704936A6678E1139D26B7819F7E90'
C1842 = int('7EFBA1662985BE9403CB055C75D4F7E0CE8D84A9C5114ABCAF3177680104FA0D', 16)
T = int(datetime(1997, 8, 16, 1, 52, 34, tzinfo=timezone.utc).timestamp())
LCG_A,LCG_C,LCG_MASK=0x5DEECE66D,11,(1<<48)-1


def candidate_slices_python(indices=(876,1842)):
    idxs=set(indices); state=(T<<16)|0x330e; data={};buf=bytearray()
    for i in range(1,max(indices)*20+1):
        state=(state*LCG_A+LCG_C)&LCG_MASK
        buf.append(state>>40)
        if i%20==0:
            k=i//20
            if k in idxs: data[k]=bytes(buf[-20:])
    return data


def candidate_slices_libc(indices=(876,1842)):
    libc=ctypes.CDLL(None)
    libc.srand48.argtypes=[ctypes.c_long]
    libc.srand48.restype=None
    libc.lrand48.argtypes=[]
    libc.lrand48.restype=ctypes.c_long
    libc.srand48(T); data={}; buf=bytearray()
    for i in range(1,max(indices)*20+1):
        buf.append(libc.lrand48()>>23)
        if i%20==0 and i//20 in indices: data[i//20]=bytes(buf[-20:])
    return data


def nist_c_one(seed):
    z=int.from_bytes(seed,'big');h0=hashlib.sha1(seed).digest()
    h1=hashlib.sha1(((z+1)%(1<<160)).to_bytes(20,'big')).digest()
    return ((int.from_bytes(h0,'big')&((1<<95)-1))<<160)|int.from_bytes(h1,'big')


def nist_c_two(seed):
    # Independent concatenated-stream formula, then take right 255 bits.
    z=int.from_bytes(seed,'big');chunks=[]
    for delta in (0,1):
        msg=((z+delta)%(1<<160)).to_bytes(20,'big')
        chunks.append(int.from_bytes(hashlib.sha1(msg).digest(),'big'))
    return ((chunks[0]<<160)|chunks[1])&((1<<255)-1)


def curve_coefficients(c):
    if c==0 or (4*c+27)%P==0:
        return {'admissible':False, 'reason':'c=0 or 4c+27=0'}
    u=(-27*pow(c,-1,P))%P
    if pow(u,(P-1)//2,P)!=1:
        return {'admissible':False, 'reason':'no square root for b²=-27/c'}
    r=pow(u,(P+1)//4,P)
    assert r*r%P==u
    roots=sorted([r,(-r)%P])
    for b in roots:
        assert (b*b*c+27)%P==0
        assert (-108+27*b*b)%P!=0
    return {'admissible':True, 'b_roots':roots,
            'congruence':all((b*b*c+27)%P==0 for b in roots),
            'nonsingular':all((-108+27*b*b)%P!=0 for b in roots),
            'j_invariant':(1728*(-108)*pow((-108+27*r*r)%P,-1,P))%P}


def first_point_with_even_y(b):
    for x in range(128):
        rhs=(x*x*x-3*x+b)%P
        if rhs==0:
            return [x,0]
        if pow(rhs,(P-1)//2,P)!=1:continue
        y=pow(rhs,(P+1)//4,P)
        if y&1:y=P-y
        assert y*y%P==rhs and y%2==0
        return [x,y]
    raise AssertionError('No point in bounded deterministic search 0..127')


def point_add(A,B,b):
    if A is None:return B
    if B is None:return A
    x1,y1=A;x2,y2=B
    if x1==x2 and (y1+y2)%P==0:return None
    if A==B:
        slope=((3*x1*x1-3)*pow(2*y1,-1,P))%P
    else:
        slope=((y2-y1)*pow((x2-x1)%P,-1,P))%P
    x3=(slope*slope-x1-x2)%P
    return x3,(slope*(x1-x3)-y1)%P


def point_mult(n,G,b):
    out=None;cur=G
    while n:
        if n&1:out=point_add(out,cur,b)
        cur=point_add(cur,cur,b)
        n>>=1
    return out


def main():
    assert P%4==3
    assert (G[1]*G[1]-(G[0]**3-3*G[0]+B))%P==0
    assert point_mult(N,G,B) is None  # independent group-law replay, NOT independent prime certification.
    ours=candidate_slices_python()
    native=candidate_slices_libc()
    assert ours==native
    assert ours[1842].hex().upper()==SEED1842
    out={}
    for i in (876,1842):
        seed=ours[i];c=nist_c_one(seed)
        assert c==nist_c_two(seed)
        curve=curve_coefficients(c)
        assert curve['admissible'] and len(curve['b_roots'])==2
        b=curve['b_roots'][0]
        pnt=first_point_with_even_y(b)
        out[str(i)]={'seed':seed.hex().upper(),'c':f'0x{c:064X}',
                     'b_roots':[f'0x{x:064X}' for x in curve['b_roots']],
                     'nonsingular':curve['nonsingular'],
                     'nist_congruence':curve['congruence'],
                     'j_invariant':f'0x{curve["j_invariant"]:064X}',
                     'example_point_on_curve':[f'0x{pnt[0]:X}',f'0x{pnt[1]:064X}'],
                     'example_point_construction':'smallest x in [0,127] with an even sqrt y; diagnostic only',
                     'order_and_emb_degree':'EXTERNAL_SOURCE_REPORT' if i==876 else 'PUBLISHED_N_AND_EXACT_NG_CHECK'}
    assert int(out['1842']['c'],16)==C1842
    assert f'0x{B:064X}' in out['1842']['b_roots']
    assert ours[876]!=ours[1842]
    assert out['876']['c']!=out['1842']['c']
    # Mutants: published coefficient must NOT be accepted under unrelated or malformed certificates.
    assert not curve_coefficients(0)['admissible']
    assert not curve_coefficients((-27*pow(4,-1,P))%P)['admissible']
    invalid_c=next(x for x in range(1,32) if not curve_coefficients(x)['admissible'])
    assert curve_coefficients(invalid_c)['reason']=='no square root for b²=-27/c'
    altered=bytes([ours[1842][0]^1])+ours[1842][1:]
    assert nist_c_one(altered)!=C1842
    assert (B*B*nist_c_one(altered)+27)%P!=0
    doc={
      'title':'P-256 V4 conditional selection witness',
      'frozen_protocol_commit':'0d48ca1489af07549b5e9a0bd5c67ccfeecb3dac',
      'sha256_source':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'historical_sources':{'anthropic':'https://www.anthropic.com/research/ecdsa-curve-origins',
         'nist_2023':'https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-186.pdf'},
      'candidate_indices':[876,1842],
      'reconstruction':out,
      'positive_controls':{'p256_published_seed':True,'p256_c':True,'p256_b_sign_root':True,
          'published_G_on_curve':True,'exact_published_order_times_G_is_infinity':True,
          'stdlib_python_matches_system_native_lrand48':True,
          'first_876_seed_differs':True,
          'two_independent_sha1_c_derivations_agree':True},
      'negative_controls':{'c_zero_refused':True,'c_discriminant_zero_refused':True,
          'first_nonresidue_c':invalid_c,'nonresidue_refused':True,
          'mutant_seed_breaks_published_c_and_b':True},
      'decision':{
          'independently_warranted':'SEEDS_SHA1_C_B_ROOTS_NONSINGULAR_EXACT',
          'prime_order_876':'SOURCE_REPORTED_BY_ANTHROPIC_NOT_INDEPENDENTLY_CERTIFIED',
          'first_acceptable_rule':'CONDITIONALLY_REFUTED_GIVEN_ANTHROPIC_ORDER_CLAIM',
          'selection_rule':'UNKNOWN',
          'historical_execution_trace':'UNKNOWN',
          'compatible_histories':'TWO_POSSIBLE_SELECTION_POLICIES_IF_BOTH_CURVES_PASS_FULL_SECURITY_TESTS'},
      'scope_limits':['This computes neither #E(Fp) for candidate 876 nor its embedding degree.',
          'The 2023 NIST restatement is not a contemporaneous 1997 implementation trace.',
          'A smallest-x point construction is only an arithmetic witness, not historical evidence.',
          'A numerical explanation does not establish historical provenance or cryptographic weakness.']
    }
    result=Path(__file__).with_name('V4_RESULTS.json')
    result.write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':doc['decision'],'seed876':out['876']['seed'],'seed1842':out['1842']['seed'],
                      'nonresidue_example':invalid_c,'output':str(result)},indent=2))

if __name__=='__main__':main()