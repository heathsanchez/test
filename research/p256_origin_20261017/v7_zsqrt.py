#!/usr/bin/env python3
"""Exact semantic translation of FreeLIP v1.1 zsqrtmod (historical source, not provenance).

This file deliberately does NOT incorporate FreeLIP's noncommercially licensed C source;
its transition semantics are independently encoded from source lines 11734..11823.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

CURVES = ['prime192v1','secp224r1','prime256v1','secp384r1','secp521r1']
P256 = int('FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF', 16)
C876 = int('276E46B26A6E09FBA8200CDD418D6DC3738C6B169131927838EC8E71DE4E8548',16)
B876_LO = int('57B035B319C68D8A8A3315B5631325B46FF3CD238179E6D548E4CAA0217DAA42',16)
B876_HI = int('A84FCA4BE639727675CCEA4A9CECDA4B900C32DD7E86192AB71B355FDE8255BD',16)
C256 = int('7EFBA1662985BE9403CB055C75D4F7E0CE8D84A9C5114ABCAF3177680104FA0D',16)
B256 = int('5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B',16)
SRC_COMMIT='00898a4814d2cc1244bf348682be6ed10dda35f0'
SRC_BLOB='a86ce8ae5be49e0f35999a2c87f52e1718ebdb81'
SRC_H='080cda8aec8c0939348452ea3beb9f1afad845ef'


def original_zsqrtmod(a,p):
    """Return (root, smallest nonresidue, iterations), or (None, n, j).

    Emulates the branching/order of historical original zsqrtmod, including
    exactly the source's first eligible odd-prime quadratic nonresidue search.
    Only odd-prime p and a in 1..p-1 are admitted (avoid legacy a=0 behavior).
    """
    assert p > 5 and p % 2 == 1 and 0 < a < p
    if p%4 == 3:
        root=pow(a,(p+1)//4,p)
        return (root if pow(root,2,p)==a else None,None,0)
    q=p-1; r=0
    while q%2==0:
        q//=2; r+=1
    n=3
    while True:
        if is_small_prime(n) and pow(n,(p-1)//2,p)==p-1:break
        n+=2
    z=pow(n,q,p)
    y=z
    xx=pow(a,(q-1)//2,p)
    bb=a*xx*xx%p
    xx=(a*xx)%p
    steps=0
    # The 1997 source's b==1 exit is above the inner Tonelli update.
    while True:
        if bb==1:
            assert xx*xx%p==a
            return xx,n,steps
        t=bb*bb%p; m=1
        while t!=1:
            if m==r:return None,n,steps
            t=t*t%p;m+=1
        if m>=r:return None,n,steps
        twiddle=pow(y,1<<(r-m-1),p)
        y=twiddle*twiddle%p
        r=m
        xx=xx*twiddle%p
        bb=bb*y%p
        steps+=1

def is_small_prime(n):
    if n<2:return False
    if n==2:return True
    if n%2==0:return False
    d=3
    while d*d<=n:
        if n%d==0:return False
        d+=2
    return True

def hex_fields(text):
    pat = re.compile(r'(?m)^(Prime|A|B|Order|Seed|Generator \(uncompressed\)):\s*(?:\n)?')
    parts=list(pat.finditer(text)); out={}
    for i,m in enumerate(parts):
        block=text[m.end():parts[i+1].start() if i+1<len(parts) else len(text)]
        vals=''.join(re.findall(r'\b[0-9a-fA-F]{2}\b',block))
        if vals:out[m.group(1)]=int(vals,16) if m.group(1)!='Seed' else bytes.fromhex(vals)
    return out

def c_sha(seed,p):
    m=p.bit_length()-1
    n=(m+159)//160
    val=int.from_bytes(seed,'big'); joined=0
    for j in range(n):joined=(joined<<160)|int.from_bytes(hashlib.sha1(((val+j)%(1<<160)).to_bytes(20,'big')).digest(),'big')
    return joined & ((1<<m)-1)

def data_row(name):
    proc=subprocess.run(['openssl','ecparam','-name',name,'-param_enc','explicit','-text','-noout'],capture_output=True,text=True,check=True)
    fields=hex_fields(proc.stdout)
    assert 'Seed' in fields and 'Prime' in fields and 'B' in fields
    p=fields['Prime']; b=fields['B']; c=c_sha(fields['Seed'],p)
    a=-27*pow(c,-1,p)%p
    assert b*b%p==a,(name,'source SHA1 coefficient does not match')
    result,n,iterations=original_zsqrtmod(a,p)
    assert result is not None and result*result%p==a
    assert result in (b,(p-b)%p)
    return dict(curve=name,p_hex=hex(p),source_b_hex=hex(b),source_c_hex=hex(c),
                original_zsqrtmod_b_hex=hex(result),original_zsqrtmod_matches_published_b=result==b,
                alternate_sign=(result==p-b),p_mod4=p%4,
                first_quadratic_nonresidue=n,iterations=iterations,sha256_openssl_source=hashlib.sha256(proc.stdout.encode()).hexdigest(),
                seed=fields['Seed'].hex().upper(),native_zsqrtmod_check='PENDING_CI')

def main():
    rows=[data_row(name) for name in CURVES]
    assert rows[2]['source_b_hex']==hex(B256) and rows[2]['source_c_hex']==hex(C256)
    a876=-27*pow(C876,-1,P256)%P256
    root876,_,_=original_zsqrtmod(a876,P256)
    assert root876 in (B876_LO,B876_HI)
    mutants=[]
    for p in [int(r['p_hex'],16) for r in rows]:
        # Small deterministic nonresidue, checked via Euler's criterion.
        z=2
        while pow(z,(p-1)//2,p)!=p-1:z+=1
        assert original_zsqrtmod(z,p)[0] is None
        mutants.append({'p_bits':p.bit_length(),'nonresidue':z,'rejected':True})
    assert rows[2]['original_zsqrtmod_matches_published_b'] is True
    output={
        'protocol':'V7_FROZEN_PROTOCOL.md',
        'status':'LOCAL_EXACT_SOURCE_TRANSLATION; HISTORICAL_USE_UNKNOWN',
        'source_ref':{'mirror_commit':SRC_COMMIT,'lip_c_blob':SRC_BLOB,'lip_h_blob':SRC_H},
        'source_description':'source-translated 1997 zsqrtmod; not a claim of historical NSA program use',
        'cases':rows,
        'case_match_count':sum(r['original_zsqrtmod_matches_published_b'] for r in rows),
        'candidate_876':{'result_b_hex':hex(root876),'V5_group_order':('PRIME' if root876==B876_HI else 'COMPOSITE'),'basis':'V5 point count, no new order computation'},
        'negative_nonresidue_controls':mutants,
        'historical_selector':'UNKNOWN',
        'historical_point_G_origin':'UNKNOWN',
        'crypto_security_implication':'NONE',
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    path=Path(__file__).with_name('V7_RESULTS.json');path.write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'count':output['case_match_count'],'total':len(rows),'cases':[{'name':r['curve'],'match':r['original_zsqrtmod_matches_published_b'],'root':r['original_zsqrtmod_b_hex']} for r in rows],'candidate_876':output['candidate_876'],'saved':str(path)},indent=2))
if __name__=='__main__':main()
