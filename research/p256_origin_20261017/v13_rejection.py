#!/usr/bin/env python3
"""Exhaustive source-rejection completion of V12's P-256 11x26 FreeLIP model.

V13 source was preregistered before this implementation at 3563c993... .
Exact 2D rejection-gap proof + 20 complete 5D weighted hidden-state lattices.
"""
from __future__ import annotations
import json,math,time,hashlib,argparse
from pathlib import Path
from fractions import Fraction as F
from sympy import Matrix, Rational
from v12_inverse import (M,A,U,P,GX,QMAX,N,DIM,PROTO as V12_PROTO,
                         MASK_INDEX_BITS,invariants, dot,gs_exact,pack)
ROOT=Path(__file__).parent
V13_PROTO='3563c99349d7fee713425ead832c18f2ee0ab8a9'
INV_A=pow(A,-1,M)
BOUND=M-(U-1)

def interval(center,remain,norm):
    if remain<0:return []
    ratio=remain/norm
    half=math.isqrt(ratio.numerator//ratio.denominator)+1
    floorcenter=center.numerator//center.denominator
    return range(floorcenter-half-1,floorcenter+half+3)


def rejection_gap_one(d):
    B=Matrix([[1,pow(A,d,M)],[0,M]])
    reduced,T=B.lll_transform(delta=Rational(3,4))
    assert T*B==reduced and abs(int(T.det()))==1
    rows=[[F(int(z)) for z in reduced.row(i)] for i in range(2)]
    ortho,mu,norm=gs_exact(rows)
    radius=F(2*(U-1)**2)
    z=[0,0];visited=0;leaves=0;reject_witness=[]
    def dfs(k,cost):
        nonlocal visited,leaves
        visited+=1
        assert visited<100000,'UNKNOWN_REJECTION_GAP_RESOURCE'
        if k==-1:
            leaves+=1
            point=[int(sum(F(z[j])*rows[j][i] for j in range(2))) for i in range(2)]
            kx,ry=point
            if 1<=kx<U and 1<=ry<U:reject_witness.append(point)
            return
        offset=sum(F(z[j])*mu[j][k] for j in range(k+1,2))
        center= -offset # target origin -> beta=0
        for n in interval(center,radius-cost,norm[k]):
            delta=(F(n)-center)**2*norm[k]
            if cost+delta<=radius:
                z[k]=n
                dfs(k-1,cost+delta)
    dfs(1,F(0))
    return {'gap':d,'integer_ball_exhaustive':True,'nodes':visited,'leaves':leaves,
            'rejected_state_pair_witnesses':reject_witness,
            'unimodular_transform':[[int(v) for v in T.row(i)] for i in range(2)],
            'reduced_basis':[[int(v) for v in reduced.row(i)] for i in range(2)]}

def temporal_schedule(skip_before_call):
    assert 1<=skip_before_call<=10
    return [i+(i>=skip_before_call) for i in range(N)]

def schedule_observations(invs,orientation,skip_before_call):
    times=temporal_schedule(skip_before_call)
    obs=[]
    for digit,bits in MASK_INDEX_BITS:
        call=digit if orientation=='lsf' else N-1-digit
        time_index=times[call]
        known=invs['invariant_digit_lowbits'][str(digit)]['value']
        obs.append((time_index,bits,known,call))
    return sorted(obs)

def from_wordlist_observations(words,orientation,skip_before_call):
    times=temporal_schedule(skip_before_call)
    obs=[]
    for digit,bits in MASK_INDEX_BITS:
        call=digit if orientation=='lsf' else N-1-digit
        obs.append((times[call],bits,words[call]&((1<<bits)-1),call))
    return sorted(obs)

def hidden_state_census(obs,orientation,skip_before_call,max_nodes=2000000):
    assert len(obs)==DIM
    assert len({v[0] for v in obs})==DIM
    i0,b0,t0,_=obs[0]
    w=[1<<x[1] for x in obs]
    H=[(M-1)//ww for ww in w]
    aa=[pow(A,x[0]-i0,M) for x in obs]
    C=[1]+[(aa[k]*w[0]*pow(w[k],-1,M))%M for k in range(1,DIM)]
    c=[0]+[((obs[k][2]-aa[k]*t0)*pow(w[k],-1,M))%M for k in range(1,DIM)]
    source_b=[[w[0]]+[w[k]*C[k] for k in range(1,DIM)]]+[[w[j]*M if j==k else 0 for j in range(DIM)] for k in range(1,DIM)]
    B=Matrix(source_b)
    assert B.det()==math.prod(w)*M**(DIM-1)
    red,T=B.lll_transform(delta=Rational(3,4))
    assert red==T*B and abs(int(T.det()))==1
    rows=[[F(int(v)) for v in red.row(i)] for i in range(DIM)]
    ortho,mu,norm=gs_exact(rows)
    target=[F(w[k]*H[k],2)+(w[k]*c[k] if k else 0) for k in range(DIM)]
    beta=[dot(target,ortho[i])/norm[i] for i in range(DIM)]
    radius_sq=sum(F((w[k]*H[k])**2,4) for k in range(DIM))
    z=[0]*DIM; nodes=0;sphere_leaves=0;box_states={}
    schedule=temporal_schedule(skip_before_call)
    def dfs(index,used):
        nonlocal nodes,sphere_leaves
        nodes+=1
        if nodes>max_nodes:raise RuntimeError('UNKNOWN_RESOURCE_NODE_LIMIT')
        if index<0:
            sphere_leaves+=1
            v=[int(sum(F(z[j])*rows[j][k] for j in range(DIM))) for k in range(DIM)]
            assert all(v[i]%w[i]==0 for i in range(DIM))
            hi=[v[0]//w[0]]+[v[i]//w[i]-c[i] for i in range(1,DIM)]
            if any(hi[i]<0 or hi[i]>H[i] for i in range(DIM)):return
            states=[obs[i][2]+w[i]*hi[i] for i in range(DIM)]
            if any(x<0 or x>=M for x in states):return
            s=states[0]
            assert all(aa[i]*s%M==states[i] for i in range(DIM))
            if s in box_states:return
            initial=s*pow(INV_A,i0,M)%M
            rawstates=[initial*pow(A,k,M)%M for k in range(12)]
            accepted=[rawstates[t] for t in schedule]
            rejected=rawstates[skip_before_call]
            for tick, b, expected, call in obs:
                assert accepted[call]&((1<<b)-1)==expected
            limbs=[s%U for s in accepted]
            original=pack(limbs,orientation)
            match=(original%P==GX)
            guard=(rejected>=BOUND and all(s<BOUND for s in accepted))
            box_states[s]={'earliest_observed_state':str(s),
                'initial_raw_state':str(initial),
                'full_raw_11_hex':hex(original),
                'full_p256_gx_match':bool(match),
                'is_valid_source_rejection_path':bool(guard),
                'rejected_state_hex':hex(rejected)}
            return
        off=sum(F(z[j])*mu[j][index] for j in range(index+1,DIM))
        middle=beta[index]-off
        for coeff in interval(middle,radius_sq-used,norm[index]):
            cost=(F(coeff)-middle)**2*norm[index]
            if cost+used<=radius_sq:
                z[index]=coeff
                dfs(index-1,cost+used)
    dfs(DIM-1,F(0))
    return {'orientation':orientation,'skip_before_call':skip_before_call,'observations':[list(x) for x in obs],
            'nodes':nodes,'sphere_leaves':sphere_leaves,'box_state_count':len(box_states),
            'full_Gx_matches':sum(int(s['full_p256_gx_match']) for s in box_states.values()),
            'valid_rejection_Gx_matches':sum(int(s['full_p256_gx_match'] and s['is_valid_source_rejection_path']) for s in box_states.values()),
            'all_states':list(box_states.values()),
            'lattice_change_unimodular':True,'enumeration_complete':True,
            'unimodular_transform':[[int(v) for v in T.row(i)] for i in range(DIM)],
            'reduced_basis':[[int(v) for v in red.row(i)] for i in range(DIM)]}

def control(skip_at,orientation):
    # Choose a raw sequence containing exactly one true FreeLIP rejected state M-1.
    s=(M-1)*pow(INV_A,skip_at,M)%M
    timeline=[s*pow(A,t,M)%M for t in range(12)]
    assert timeline[skip_at]==M-1
    schedule=temporal_schedule(skip_at)
    accepted=[timeline[t] for t in schedule]
    assert all(v<BOUND for v in accepted)
    limbs=[v%U for v in accepted]
    obs=from_wordlist_observations(limbs,orientation,skip_at)
    r=hidden_state_census(obs,orientation,skip_at)
    original=pack(limbs,orientation)
    assert any(v['initial_raw_state']==str(s) and v['is_valid_source_rejection_path'] and v['full_raw_11_hex']==hex(original) for v in r['all_states'])
    return {'skip_position':skip_at,'orientation':orientation,'correct_original_hidden_state_recovered':True,
            'source_rejected_state':hex(timeline[skip_at]),
            'box_state_count':r['box_state_count'],'nodes':r['nodes']}

def main():
    arg=argparse.ArgumentParser();arg.add_argument('--out',default=str(ROOT/'V13_RESULTS.json'))
    opts=arg.parse_args()
    inv=invariants()
    gaps=[rejection_gap_one(d) for d in range(1,23)]
    witnesses=[(x['gap'],x['rejected_state_pair_witnesses']) for x in gaps if x['rejected_state_pair_witnesses']]
    assert witnesses==[], ('Unexpected closely spaced rejected states',witnesses)
    controls=[control(k,o) for k in (1,7,10) for o in ('msf','lsf')]
    rows=[]
    for skip in range(1,11):
        for orientation in ('msf','lsf'):
            rows.append(hidden_state_census(schedule_observations(inv,orientation,skip),orientation,skip))
    exact_matches=sum(x['valid_rejection_Gx_matches'] for x in rows)
    outcome={'title':'V13 complete source 11x26 FreeLIP internal-rejection point-origin check',
      'status':'NO_FREELIP_11x26_Gx_SOURCE_SAMPLER_ALL_STATES' if exact_matches==0 else 'HISTORICAL_NUMERICAL_MATCH_CANDIDATE',
      'frozen_protocol':'3563c99349d7fee713425ead832c18f2ee0ab8a9',
      'source':'original mirrored FreeLIP v1.1 (1997) commit 00898a4814d2cc1244bf348682be6ed10dda35f0',
      'parameters':{'M':str(M),'A':str(A),'u':U,'rejection_lower_bound':str(BOUND),'p':hex(P),'Gx':hex(GX),
                    'limbs':N,'full_q_count':QMAX+1},
      'invariants':inv,'rejection_gap_certificates':gaps,
      'max_gap_checked':22,'positive_controls':controls,
      'one_rejection_schedules':rows,
      'all_possible_rejection_histories_covered':True,
      'warrant_interpretation':'SOURCE_FREELIP_26BIT_LIMB_SPECIFIC_NOT_ANY_HISTORICAL_NSA_GENERATOR',
      'exhaustive_target_20_schedule_case_count':len(rows),
      'total_fully_matching_source_models':exact_matches,
      'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'epistemic':{'historical_1997_NSA_program':'UNKNOWN','other_bitness_rng':'NOT_COVERED',
        'alternate_output_transforms':'NOT_COVERED','general_ECDSA_security':'NOT_A_VULNERABILITY',
        'independent_GitHub_CI':'AWAITING','strong_LLM_comparator':'NOT_RUN',
        'V12_no_rejection_source':'INDEPENDENT_QUALIFIED_CI_39014510101'}}
    Path(opts.out).write_text(json.dumps(outcome,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':outcome['status'],'gap_cases':len(gaps),'gap_witnesses':len(witnesses),
      'controls':len(controls),'tested_schedules':len(rows),
      'total_hidden_state_box_candidates':sum(r['box_state_count'] for r in rows),
      'source_matching_models':exact_matches,'max_nodes':max(r['nodes'] for r in rows),
      'out':opts.out},indent=2))

if __name__=='__main__':main()
