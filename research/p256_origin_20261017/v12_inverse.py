#!/usr/bin/env python3
"""V12 exact lattice all-hidden-state inversion for 1997 FreeLIP 11x26 output.

Uses source-quantified q-invariant P-256 residue bits and a *complete* exact
weighted lattice enumeration, not speculative q/seed enumeration.
The original FreeLIP no-rejection assumption is explicit and preserved.
"""
from __future__ import annotations
import json, time, math, hashlib, argparse
from pathlib import Path
from fractions import Fraction as F
from sympy import Matrix, Rational

M=(1<<107)-1
A=pow(3,121,M)
INV_A=pow(A,-1,M)
U=1<<26
P=int('FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF',16)
GX=int('6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296',16)
QMAX=((1<<(11*26))-1-GX)//P
N=11
DIM=5
MASK_INDEX_BITS=((2,26),(3,18),(5,26),(6,26),(7,10)) # digit i, low b_i observed
PROTO='9578ccae67a49f68c4e85ebe0103f46733e8125e'
ROOT=Path(__file__).parent

def raw_words(raw,orientation):
    words=[(raw>>(26*i))&(U-1) for i in range(N)]
    if orientation=='msf':words.reverse()
    return words

def pack(words,orientation):
    if orientation=='lsf':words=words[::-1]
    x=0
    for v in words:x=x*U+v
    return x

def source_states(seed,offset,n):
    s=seed%M
    for _ in range(offset):s=s*A%M
    result=[]
    for _ in range(n):
        s=s*A%M
        result.append(s)
    return result

def digit_of(raw,i):return (raw>>(26*i))&(U-1)

def invariants():
    assert QMAX==(1<<30)-1
    xlow52=GX% (1<<52)
    xlow192=GX % (1<<192)
    high_end=xlow192 + QMAX*((1<<96)-1)
    assert P%(1<<96)==(1<<96)-1
    assert P%(1<<192)==(1<<96)-1
    assert xlow52>QMAX, 'borrow would cross the low slice'
    assert high_end < 1<<192, 'overflow would wrap high slice'
    assert xlow192>>130 == high_end>>130, 'carry crosses high slice'
    expected={str(i):{'known_low_bits':b, 'value':digit_of(GX,i)&((1<<b)-1)} for i,b in MASK_INDEX_BITS}
    for q in [0,1,2,77,412664470,412664471,QMAX//2,QMAX-1,QMAX]:
        raw=GX+q*P
        assert raw<(1<<286)
        for i,b in MASK_INDEX_BITS:
            assert digit_of(raw,i)&((1<<b)-1) == expected[str(i)]['value']
    return {'q_max':QMAX,'x_low52_gt_qmax':xlow52>QMAX,
            'high_slice_end_lt_2^192':high_end<(1<<192),
            'high_slice_130_to_191_stable':(xlow192>>130)==(high_end>>130),
            'invariant_digit_lowbits':expected,
            'invariant_bits_total':sum(b for _,b in MASK_INDEX_BITS),
            'whole_q_interval_proved_by_endpoint_inequalities':True}


def observed_from_temporal(words,orientation):
    obs=[]
    for digit,bits in MASK_INDEX_BITS:
        index=digit if orientation=='lsf' else N-1-digit
        obs.append((index,bits,words[index]&((1<<bits)-1)))
    return sorted(obs)


def observed_from_invariants(orientation,invs):
    o=[]
    for digit,bits in MASK_INDEX_BITS:
        index=digit if orientation=='lsf' else N-1-digit
        o.append((index,bits,invs['invariant_digit_lowbits'][str(digit)]['value']))
    return sorted(o)


def dot(a,b):return sum(x*y for x,y in zip(a,b))

def gs_exact(rows):
    gram=[];mu=[[F(0) for _ in rows] for _ in rows];norm=[]
    for i,row in enumerate(rows):
        v=row[:]
        for j in range(i):
            mu[i][j]=dot(row,gram[j])/norm[j]
            v=[x-mu[i][j]*y for x,y in zip(v,gram[j])]
        gram.append(v);norm.append(dot(v,v))
        assert norm[-1]>0
    assert all(dot(gram[i],gram[j])==0 for i in range(len(rows)) for j in range(i))
    return gram,mu,norm


def enumerate_states(obs, orientation, node_limit=2000000):
    assert len(obs)==DIM and len({i for i,_,_ in obs})==DIM
    t0=obs[0][2]; i0=obs[0][0]
    weights=[1<<b for _,b,_ in obs]
    hmax=[(M-1)//w for w in weights]
    a=[pow(A,i-i0,M) for i,_,_ in obs]
    C=[1]+[(a[k]*weights[0]*pow(weights[k],-1,M))%M for k in range(1,DIM)]
    c=[0]+[((obs[k][2]-a[k]*t0)*pow(weights[k],-1,M))%M for k in range(1,DIM)]
    b0=[weights[0]]+[weights[k]*C[k] for k in range(1,DIM)]
    matrix=Matrix([b0]+[[weights[j]*M if k==j else 0 for k in range(DIM)] for j in range(1,DIM)])
    determinant=(M**(DIM-1))*math.prod(weights)
    assert int(matrix.det())==determinant
    reduced, transform=matrix.lll_transform(delta=Rational(3,4))
    assert transform*matrix==reduced and abs(int(transform.det()))==1
    rows=[[F(int(x)) for x in reduced.row(i)] for i in range(DIM)]
    star,mu,norm=gs_exact(rows)
    mid=[F(weights[k]*hmax[k],2) + (weights[k]*c[k] if k else 0) for k in range(DIM)]
    beta=[dot(mid,star[i])/norm[i] for i in range(DIM)]
    radius_sq=sum(F((weights[k]*hmax[k])**2,4) for k in range(DIM))
    z=[0]*DIM
    nodes=0;sphere_leaves=0;valid_box_states=[];unique_state=set();max_width=0
    started=time.perf_counter()
    def recurse(k,cost):
        nonlocal nodes,sphere_leaves,max_width
        nodes+=1
        if nodes>node_limit:raise RuntimeError('UNKNOWN_RESOURCE_NODE_LIMIT')
        if k<0:
            sphere_leaves+=1
            v=[int(sum(F(z[j])*rows[j][n] for j in range(DIM))) for n in range(DIM)]
            high=[v[0]//weights[0]]+[int(v[j]//weights[j])-c[j] for j in range(1,DIM)]
            assert all(v[j]%weights[j]==0 for j in range(DIM))
            if any(high[j]<0 or high[j]>hmax[j] for j in range(DIM)):return
            states=[obs[j][2]+weights[j]*high[j] for j in range(DIM)]
            if any(s<0 or s>=M for s in states):return
            s0=states[0]
            if any((a[j]*s0)%M!=states[j] for j in range(DIM)):raise AssertionError('Inconsistent lattice high-state relation')
            if s0 in unique_state:return
            unique_state.add(s0)
            # s0 is state at first observed output index i0; invert earlier clock outputs.
            first=(s0*pow(INV_A,i0,M))%M
            temporal=[int(first*pow(A,i,M))%M for i in range(N)]
            observed=[(temp_index, b, temporal[temp_index]&((1<<b)-1)) for temp_index,b,_ in obs]
            assert observed==obs
            limbs=[s%U for s in temporal]
            raw=pack(limbs,orientation)
            valid_box_states.append({'first_observation_state':str(s0),
                'temporal_first_state':str(first),
                'raw_full_11_hex':hex(raw),
                'raw_mod_p_hex':hex(raw%P),
                'matches_P256_Gx':raw%P==GX,
                'accepted_no_internal_skips':all(s<M-(M%U) for s in temporal),
                'prng_lowbits':limbs})
            return
        offset=sum(F(z[j])*mu[j][k] for j in range(k+1,DIM))
        center=beta[k]-offset
        remaining=radius_sq-cost
        if remaining<0:return
        ratio=remaining/norm[k]
        exact_sqrt_floor=math.isqrt(ratio.numerator//ratio.denominator)
        excess=exact_sqrt_floor+1
        center_floor=center.numerator//center.denominator
        lo=center_floor-excess-1
        hi=center_floor+excess+2
        max_width=max(max_width,hi-lo+1)
        for candidate in range(lo,hi+1):
            term=(F(candidate)+offset-beta[k])**2*norm[k]
            if cost+term<=radius_sq:
                z[k]=candidate
                recurse(k-1,cost+term)
    recurse(DIM-1,F(0))
    return {'orientation':orientation,'observed':obs,
        'exact_total_nodes':nodes,'exact_sphere_leaves':sphere_leaves,
        'true_box_hidden_states':len(valid_box_states),
        'full_Gx_matches':sum(v['matches_P256_Gx'] for v in valid_box_states),
        'source_native_accepted_matches':sum(v['matches_P256_Gx'] and v['accepted_no_internal_skips'] for v in valid_box_states),
        'max_candidate_integer_interval':max_width,
        'states':valid_box_states,
        'elapsed_seconds':round(time.perf_counter()-started,4),
        'verified_unimodular_lattice_change':True,
        'exact_full_sphere_enumeration':True}


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default=str(ROOT/'V12_RESULTS.json'))
    args=p.parse_args()
    inv=invariants()
    controls=[]
    for seed,offset in ((20000,7),(20420,29)):
        ss=source_states(seed,offset,11)
        limbs=[s%U for s in ss]
        for orientation in ('msf','lsf'):
            obs=observed_from_temporal(limbs,orientation)
            r=enumerate_states(obs,orientation)
            assert any(v['temporal_first_state']==str(ss[0]) and v['raw_full_11_hex']==hex(pack(limbs,orientation)) for v in r['states']),(seed,offset,orientation)
            controls.append({'seed':seed,'offset':offset,'orientation':orientation,
                             'matched_correct_state':True,
                             'box_state_count':r['true_box_hidden_states'],
                             'complete':r['exact_full_sphere_enumeration']})
    targets=[]
    for orientation in ('msf','lsf'):
        obs=observed_from_invariants(orientation,inv)
        r=enumerate_states(obs,orientation)
        targets.append(r)
    matches=sum(x['full_Gx_matches'] for x in targets)
    status='BOUNDED_11_LIMB_NO_STATE_MATCH_UNDER_NO_REJECTIONS' if matches==0 else 'FULL_11_LIMB_MATCH_CANDIDATE_ONLY'
    result={'status':status,'protocol_commit':PROTO,
        'scope':'11x26 consecutive accepted low-bit FreeLIP outputs (no rejection), both output packing directions; all M states; all 2^30 reduction quotients via exact invariant bit masks',
        'source':'FreeLIP v1.1 1997 mirror 00898a4814d2cc1244bf348682be6ed10dda35f0; no independent historical NSA program',
        'parameters':{'M':str(M),'A':str(A),'u':U,'nlimbs':N,'p':hex(P),'target_Gx':hex(GX)},
        'invariants':inv,'known_source_seed_positive_controls':controls,'target_orientations':targets,
        'all_hidden_initial_states_quantified':True,'all_reduction_quotients_quantified':True,
        'total_target_hidden_state_candidates':sum(x['true_box_hidden_states'] for x in targets),
        'total_exact_P256_full_matches':matches,
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'epistemic':{'actual_historical_G_generation':'UNKNOWN',
        'FreeLIP_rejection_skip_cases':'NOT_COVERED',
        'different_limb_widths_or_external_generator':'NOT_COVERED',
        'NSA_1997_curve_generator_usage':'NOT_ESTABLISHED',
        'strong_coding_agent_advantage':'NOT_RUN',
        'independent_CI_verdict':'AWAITING',
        'ECDSA_cryptanalytic_vulnerability':'NOT_CLAIMED'}}
    out=Path(args.out)
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':status,'invariant_bits':inv['invariant_bits_total'],
                      'quotient_count':QMAX+1,'controls':len(controls),
                      'orientations':[{k:r[k] for k in ['orientation','exact_total_nodes','exact_sphere_leaves','true_box_hidden_states','full_Gx_matches']} for r in targets],
                      'result':str(out)},indent=2))

if __name__=='__main__':main()
