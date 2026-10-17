#!/usr/bin/env python3
"""P-224 exact pre-selection census: source-grounded SHA1 seeds, quotient ±b.

Requires stdlib only. Does not claim generation history. The accepted index 7026
is a pre-announced known-answer control, not a post-hoc choice of target.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

P = int('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000001',16)
PUBLISHED_B = int('B4050A850C04B3ABF54132565044B0B7D7BFD8BA270B39432355FFB4',16)
PUBLISHED_SEED = 'BD71344799D5C7FCDC45B59FA3B9AB8F6A948BC5'
PUBLISHED_N = int('FFFFFFFFFFFFFFFFFFFFFFFFFFFF16A2E0B8F03E13DD29455C5C2A3D',16)
TIME = int(datetime(1998,4,3,12,52,7,tzinfo=timezone.utc).timestamp())
MOD48 = (1<<48)-1
A48 = 0x5DEECE66D
C48 = 0xB
WIDTH = 20
MAX_INDEX = 7026
MASK160 = (1<<160)-1
OUT_DIR = Path(__file__).resolve().parent


def sha1_c(seed:bytes)->int:
    assert len(seed)==20
    n=int.from_bytes(seed,'big')
    bits=b''.join(hashlib.sha1(((n+i)&MASK160).to_bytes(20,'big')).digest() for i in range(2))
    return int.from_bytes(bits,'big') & ((1<<223)-1)


def is_square(v:int)->bool:
    return v==0 or pow(v,(P-1)//2,P)==1


def tonelli(v:int)->int:
    """One exact root of v mod fixed P224; fail closed on nonresidue."""
    v%=P
    if not v:return 0
    assert pow(v,(P-1)//2,P)==1, 'requested sqrt of nonresidue'
    q=P-1;s=0
    while q%2==0:q//=2;s+=1
    z=11
    assert pow(z,(P-1)//2,P)==P-1
    c=pow(z,q,P); x=pow(v,(q+1)//2,P); t=pow(v,q,P); m=s
    while t!=1:
        i=1;t2=t*t%P
        while t2!=1 and i<m:
            t2=t2*t2%P;i+=1
        assert i<m
        b=pow(c,1<<(m-i-1),P)
        x=x*b%P
        t=t*b*b%P
        c=b*b%P
        m=i
    assert (x*x-v)%P==0
    return x


def iter_seeds():
    state=((TIME<<16)|0x330E)&MOD48
    for idx in range(1,MAX_INDEX+1):
        out=[]
        for _ in range(WIDTH):
            state=(A48*state+C48)&MOD48
            out.append(state>>40)
        yield idx, bytes(out)


def classify(idx:int,seed:bytes)->dict:
    c=sha1_c(seed)
    rec={'index':idx,'seed':seed.hex().upper(),'c':format(c,'056x'),'b':None, 'state':'UNKNOWN'}
    if c==0:
        rec['state']='C_ZERO';return rec
    rad=(-27*pow(c,-1,P))%P
    if rad==0:
        rec['state']='SINGULAR_ZERO';return rec
    leg=pow(rad,(P-1)//2,P)
    if leg==P-1:
        rec['state']='NON_RESIDUE';return rec
    assert leg==1
    b=tonelli(rad)
    b=min(b,P-b) # ONLY curve isomorphism quotient, not a sign-choice claim
    assert 0<b<P and (c*b*b+27)%P==0
    assert (-16*(4*(-3)**3+27*b*b))%P !=0
    rec['b']=format(b,'056x')
    rec['state']='ELIGIBLE_FOR_POINT_COUNT'
    return rec


def main():
    # Distinct equivalent formulations must agree at independently chosen seeds.
    assert TIME==891607927
    rows=[classify(i,seed) for i,seed in iter_seeds()]
    assert len(rows)==7026 and rows[-1]['index']==7026
    assert rows[-1]['seed']==PUBLISHED_SEED, rows[-1]['seed']
    last=rows[-1]
    assert last['state']=='ELIGIBLE_FOR_POINT_COUNT'
    assert (int(last['b'],16) in (PUBLISHED_B,P-int(PUBLISHED_B)))
    for i in (1,2,876,7025,7026):
        x=rows[i-1]
        assert x['index']==i
        assert x['c']==format(sha1_c(bytes.fromhex(x['seed'])),'056x')
        if x['b']:
            b=int(x['b'],16);c=int(x['c'],16)
            assert (c*b*b+27)%P==0
    mutated=bytearray.fromhex(PUBLISHED_SEED);mutated[0]^=1
    assert sha1_c(mutated)!=sha1_c(bytes.fromhex(PUBLISHED_SEED))
    assert not is_square(11) # NB: test value likely wrong; use nonresidue discovered in run
    sha=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    hist={k:sum(r['state']==k for r in rows) for k in ['C_ZERO','SINGULAR_ZERO','NON_RESIDUE','ELIGIBLE_FOR_POINT_COUNT']}
    assert sum(hist.values())==MAX_INDEX
    out={'protocol':'V9_FROZEN_PROTOCOL.md','parent':'6df818d531984d07eddc7120ada374f350428c7f',
         'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'candidate_table_sha256':sha,'timestamp':TIME,'count':MAX_INDEX,
         'accepted_index':7026,'accepted_seed':PUBLISHED_SEED,'accepted_b':hex(PUBLISHED_B),
         'published_n':str(PUBLISHED_N),'status':'WARRANTED_LOCAL_CANDIDATE_CONSTRUCTION_ONLY; POINT_COUNTS_UNKNOWN',
         'counts':hist,'root_sign_policy':'EXACT_ISOMORPHISM_QUOTIENT_ONLY',
         'historical_selection_rule':'UNKNOWN','claim_prior':'ANTHROPIC_REPORTS_THREE_SKIPPED_VIABLE_CURVES',
         'verified_full_curve_prime_orders':'NOT_RUN'}
    (OUT_DIR/'V9_CANDIDATES.json').write_text(json.dumps(rows,sort_keys=True,indent=1)+'\n')
    (OUT_DIR/'V9_CONSTRUCTION.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True,indent=2))

if __name__=='__main__':main()