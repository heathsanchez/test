#!/usr/bin/env python3
"""Read-only standards-derived NIST coefficient-sign policy falsifier.

All candidate hypotheses were frozen in GitHub V6_FROZEN_PROTOCOL before
inspecting these OpenSSL primary-curve parameter outputs.
"""
from __future__ import annotations
import subprocess, hashlib, json, pathlib, re

CURVES = ['prime192v1','secp224r1','prime256v1','secp384r1','secp521r1']
BASE = pathlib.Path(__file__).resolve().parent
P256_C_876 = int('276E46B26A6E09FBA8200CDD418D6DC3738C6B169131927838EC8E71DE4E8548', 16)
B876_LO = int('57B035B319C68D8A8A3315B5631325B46FF3CD238179E6D548E4CAA0217DAA42',16)
B876_HI = int('A84FCA4BE639727675CCEA4A9CECDA4B900C32DD7E86192AB71B355FDE8255BD',16)
C1842 = int('7EFBA1662985BE9403CB055C75D4F7E0CE8D84A9C5114ABCAF3177680104FA0D',16)
B1842 = int('5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B',16)
P256 = int('FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF',16)
FROZEN_SHA = 'ac022b760f5bdd785b5e127c2814d4214c336779'

def split_fields(report: str):
    pat = re.compile(r'(?m)^(Prime|A|B|Generator \(uncompressed\)|Order|Seed):\s*(?:\n)?')
    matches = list(pat.finditer(report))
    blocks = {}
    for idx,m in enumerate(matches):
        nextpos = matches[idx+1].start() if idx+1<len(matches) else len(report)
        block = report[m.end():nextpos]
        hexdigits = ''.join(re.findall(r'(?:[0-9a-f]{2}:)+[0-9a-f]{2}|[0-9a-f]{2}:[0-9a-f]{2}|[0-9a-f]{2}', block, flags=re.I))
        # simpler: hex by line with optional colon and space; no metadata expected
        raw=''.join(re.findall(r'\b[0-9a-fA-F]{2}\b',block))
        if not raw: raise ValueError(f'hex field missing {m.group(1)}')
        blocks[m.group(1)] = bytes.fromhex(raw)
    return blocks

def extract_curve(name):
    pr = subprocess.run(['openssl','ecparam','-name',name,'-param_enc','explicit','-text','-noout'],check=True,text=True,capture_output=True)
    vals=split_fields(pr.stdout)
    for key in ['Prime','A','B','Seed','Order']:
        if key not in vals:raise ValueError(f'{name} lacks {key}')
    p=int.from_bytes(vals['Prime'],'big')
    a=int.from_bytes(vals['A'],'big')
    b=int.from_bytes(vals['B'],'big')
    assert 0 < b < p and a==p-3
    return {'curve':name,'p':p,'a':a,'b':b,'seed':vals['Seed'],'order':int.from_bytes(vals['Order'],'big'),'raw_output_sha256':hashlib.sha256(pr.stdout.encode()).hexdigest()}

def c_from_sha1(seed:bytes, length:int)->int:
    # Official procedure concatenates consecutive SHA-1(seed + i) outputs.
    count = (length+159)//160
    k=int.from_bytes(seed,'big')
    bits=[]
    for i in range(count):
        bits.append(int.from_bytes(hashlib.sha1(((k+i)%(1<<160)).to_bytes(20,'big')).digest(),'big'))
    val=0
    for q in bits:val=(val<<160)|q
    return val&((1<<length)-1)

def root_status(p,b,c):
    assert b and b!=p-b
    inv=(-27*pow(c,-1,p))%p
    valid=(b*b-inv)%p==0
    return {'b':'0x'+format(b,'x'), 'b_complement':'0x'+format(p-b,'x'),
            'sha1_seed_coefficient_equation':bool(valid),
            'R_min': b==min(b,p-b),'R_even':b%2==0,
            'R_mod4':(b==pow(inv,(p+1)//4,p)) if p%4==3 else None,
            'p_mod4':p%4}

def main():
    rows=[]
    for name in CURVES:
        row=extract_curve(name)
        p,b=row['p'],row['b']
        m=p.bit_length()-1
        c=c_from_sha1(row['seed'],m)
        sign=root_status(p,b,c)
        # For source-compatibility, fail closed if SHA1 trace is not exact.
        if not sign['sha1_seed_coefficient_equation']:
            raise AssertionError(f'{name} published b does not satisfy reconstructed c; trace format may differ')
        rows.append({'curve':name,'field_bits':p.bit_length(),'seed':row['seed'].hex().upper(),
                     'p':'0x'+format(p,'x'),'published_b': '0x'+format(b,'x'),
                     'derived_c':'0x'+format(c,'x'), 'source_sha256':row['raw_output_sha256'],
                     'rules': sign})
    assert rows[2]['derived_c'].lower()=='0x'+format(C1842,'x')
    assert int(rows[2]['published_b'],16)==B1842 and int(rows[2]['p'],16)==P256
    skipped=root_status(P256,B876_LO,P256_C_876)
    accepted=root_status(P256,B1842,C1842)
    skipped_upper=root_status(P256,B876_HI,P256_C_876)
    assert skipped['sha1_seed_coefficient_equation'] and skipped_upper['sha1_seed_coefficient_equation']
    assert B876_LO+B876_HI==P256
    assert skipped['R_min'] and not skipped_upper['R_min']
    verdict={}
    for rule in ('R_min','R_even','R_mod4'):
        vals=[r['rules'][rule] for r in rows]
        n=sum(x is True for x in vals)
        fail=[rows[i]['curve'] for i,v in enumerate(vals) if v is False]
        verdict[rule]={'matches':n,'applicable':sum(v is not None for v in vals),'mismatches':fail,
                       'all_published_compatible': len(fail)==0 and all(v is not None for v in vals)}
    result={'status':'WARRANTED_BOUNDED_EXACT_PARAMETER_CROSSCHECK; HISTORICAL_POLICY_UNKNOWN',
        'date':'2026-10-17','protocol_sha':FROZEN_SHA,
        'source':'OpenSSL 3.5.5 installed on developer runner; official named NIST curve constants',
        'openssl_version':subprocess.check_output(['openssl','version'],text=True).strip(),
        'cases':rows,'published_policy_results':verdict,
        'candidate_876':{'b_low':skipped,'b_high':skipped_upper,'b_low_group_order':'COMPOSITE_PARIGP_V5','b_high_group_order':'PRIME_PARIGP_V5'},
        'published_1842_rules':accepted,
        'conclusion':'R_min/R_even and other exact rule failures only falsify a common uniform convention, not local P256 root-choice history; first-acceptable conditioned on documented b-root choice is not independently refuted; history unknown',
        'general_provenance':'UNKNOWN','cryptographic_security_implication':'NONE'}
    out=BASE/'V6_RESULTS.json'
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'rules':verdict,'876_low':{k:skipped[k] for k in ('R_min','R_even','R_mod4')},'1842':{k:accepted[k] for k in ('R_min','R_even','R_mod4')},'source_hash':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'out':str(out)},indent=2))
if __name__=='__main__':main()