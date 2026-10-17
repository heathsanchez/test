#!/usr/bin/env python3
"""Independent PARI/GP order-certificate driver for the frozen P-256 876± experiment."""
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = int('FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF',16)
PUB_N = int('FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551',16)
B_PUB = int('5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B',16)
B_LO = int('57B035B319C68D8A8A3315B5631325B46FF3CD238179E6D548E4CAA0217DAA42',16)
B_HI = int('A84FCA4BE639727675CCEA4A9CECDA4B900C32DD7E86192AB71B355FDE8255BD',16)
FREEZE = 'de2d46e682d4866098d3e5e9dfb2d7b289481e38'


def fail_closed(status, detail, raw=''):
    obj={'status':status,'detail':detail,'raw_output_excerpt':raw[-6000:],'freeze':FREEZE}
    (HERE/'V5_STATUS.json').write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
    raise RuntimeError(f'{status}: {detail}')


def witness_point(b):
    for x in range(128):
        v=(x**3-3*x+b)%P
        if v==0: return x,0
        if pow(v,(P-1)//2,P)==1:
            y=pow(v,(P+1)//4,P)
            if y%2:y=P-y
            assert (y*y-x**3+3*x-b)%P==0
            return x,y
    raise AssertionError('No point in original frozen x 0..127 range')


def ec_add(a,b):
    if a is None:return b
    if b is None:return a
    x,y=a;u,v=b
    if x==u and (y+v)%P==0:return None
    if a==b:
        m=(3*x*x-3)*pow(2*y,-1,P)%P
    else:
        m=(v-y)*pow((u-x)%P,-1,P)%P
    z=(m*m-x-u)%P
    return z,(m*(x-z)-y)%P


def mul(n,point):
    r=None;q=point
    while n:
        if n&1:r=ec_add(r,q)
        q=ec_add(q,q);n//=2
    return r


def check_embedding(p,n):
    x=p%n
    for k in range(1,1024):
        if x==1:return k
        x=x*p%n
    return None


def main():
    # Preserve source identity and original candidate coefficient signs.
    v4=json.loads((HERE/'V4_RESULTS.json').read_text())
    assert v4['reconstruction']['876']['seed']=='50C71A63F911DB7B2F31618ECF609D37154437F9'
    assert sorted(int(v,16) for v in v4['reconstruction']['876']['b_roots'])==[B_LO,B_HI]
    assert B_PUB in [int(v,16) for v in v4['reconstruction']['1842']['b_roots']]
    for b in (B_PUB,B_LO,B_HI):
        assert (4*(-3)**3+27*b*b)%P!=0
    if not shutil.which('gp'):
        fail_closed('ENVIRONMENT_NOT_ADMITTED','Missing pari-gp executable; scientific status UNKNOWN')
    t0=time.monotonic()
    try:
        proc=subprocess.run(['gp','-q','-f',str(HERE/'v5_ellsea.gp')],capture_output=True,
                            text=True,timeout=1100,check=False)
    except subprocess.TimeoutExpired as exc:
        fail_closed('POINT_COUNT_RESOURCE_UNKNOWN','gp execution timed out',str(exc))
    raw=proc.stdout+'\n'+proc.stderr
    (HERE/'V5_PARI_OUTPUT.txt').write_text(raw)
    if proc.returncode!=0 or '***' in raw:
        fail_closed('POINT_COUNT_RUN_RED',f'PARI exited {proc.returncode} or emitted an error',raw)
    rows={}
    for label,order,prime in re.findall(r'V5\|([a-z_]+)\|(\d+)\|(-?\d+)',raw):
        if label in rows:fail_closed('DUPLICATE_RESULT','duplicate '+label,raw)
        rows[label]={'sea_output':int(order),'proven_prime':int(prime)}
    if set(rows)!={'published','skipped_lo','skipped_hi'}:
        fail_closed('POINT_COUNT_PARSE_RED',f'Unexpected GP rows {set(rows)}',raw)
    if rows['published']!={'sea_output':PUB_N,'proven_prime':1}:
        fail_closed('POSITIVE_CONTROL_RED','Published NIST P-256 point count/primality mismatch',raw)
    group={}
    for name,b in [('published',B_PUB),('skipped_lo',B_LO),('skipped_hi',B_HI)]:
        n=rows[name]['sea_output']; pr=rows[name]['proven_prime']
        if n==0:
            assert pr==-1
            group[name]={'method':'SEA_TORSION_EARLY_REJECTION','exact_order':None,
                         'primality':'NONPRIME_SMALL_FACTOR_INDICATED_BY_PARIGP'}
            continue
        assert n>1 and abs(n-(P+1))**2<=4*P, 'Hasse bound invalid'
        assert pr in (0,1)
        point=witness_point(b)
        assert mul(n,point) is None, f'Independent group-law disagrees on {name}'
        emb=check_embedding(P,n) if pr==1 else None
        assert pr!=1 or (emb is None and n!=P)
        group[name]={'method':'SEA_POINT_COUNT','exact_order':str(n),'hex_order':hex(n),
                     'primality':'PROVEN_PARIGP' if pr==1 else 'PROVEN_COMPOSITE_PARIGP',
                     'deterministic_point_hex':[hex(x) for x in point],
                     'independent_point_order_divides_n':True,'hasse_pass':True,
                     'anomalous_n_eq_p':n==P,'first_bad_embedding_k_up_to_1023':emb}
    l=group['skipped_lo']['exact_order'];h=group['skipped_hi']['exact_order']
    if l or h:
        a=int(l or h)
        n_other=2*(P+1)-a
        other='skipped_hi' if l else 'skipped_lo'
        if group[other]['exact_order']:
            assert int(group[other]['exact_order'])==n_other,'Quadratic twist cardinal mismatch'
            group['twist_cardinality_sum_exact']=True
        else:
            group[other]['exact_order']=str(n_other)
            group[other]['hex_order']=hex(n_other)
            group[other]['method']='QUADRATIC_TWIST_DERIVED_FROM_EXACT_OTHER_ROOT'
            group[other]['derived_hasse_pass']=abs(n_other-(P+1))**2<=4*P
            small_factor=next((q for q in range(2,10001) if n_other%q==0),None)
            group[other]['small_factor_witness']=small_factor
            assert small_factor is not None or rows[other]['sea_output']==0
            point=witness_point(B_HI if other=='skipped_hi' else B_LO)
            assert mul(n_other,point) is None
            group[other]['independent_point_order_divides_n']=True
            group['twist_cardinality_sum_exact']=True
    any_prime=any(rows[k]['proven_prime']==1 for k in ('skipped_lo','skipped_hi'))
    both_early=all(rows[k]['sea_output']==0 for k in ('skipped_lo','skipped_hi'))
    result='INDEPENDENT_PARIGP_876_PRIME_ORDER_CONFIRMED' if any_prime else ('REJECTED_REPORTED_PRIME_IF_BOTH_ABORT' if both_early else 'INDEPENDENT_PRIME_ORDER_UNKNOWN')
    record={'result':result,'protocol_commit':FREEZE,
            'p256_v4_parent_sha':'c41af2df7d9c67a3948fcf753134e7feb4a2a1fe',
            'pari_version_stdout':[line for line in raw.splitlines() if line.startswith('PARI_VERSION|')],
            'gp_source_sha256':hashlib.sha256((HERE/'v5_ellsea.gp').read_bytes()).hexdigest(),
            'python_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'ellsea_tors_parameter':1,'candidate_roots_tested':'BOTH_POSITIVE_AND_NEGATIVE_ROOTS_FROZEN',
            'prime_group_values':rows,'group_checks':group,
            'elapsed_seconds':round(time.monotonic()-t0,3),
            'epistemic':{'mathematical_point_count':'PARIGP_SEA_INDEPENDENT_SOFTWARE_REPLAY' if any_prime else 'UNKNOWN_OR_REJECTED_WITHIN_PARIGP',
                        'historical_selection_rule':'UNKNOWN','basepoint_origin':'UNKNOWN',
                        'retained_v1_v4_negatives':'UNCHANGED',
                        'not_a_security_vulnerability':True,'formal_lean_proof':'NOT_RUN',
                        'strong_agent_comparator':'NOT_RUN'}}
    (HERE/'V5_RESULTS.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':result,'orders':{k:v['exact_order'] for k,v in group.items() if isinstance(v,dict)},
                      'pari_version':record['pari_version_stdout'],'elapsed':record['elapsed_seconds']},indent=2))

if __name__=='__main__':main()