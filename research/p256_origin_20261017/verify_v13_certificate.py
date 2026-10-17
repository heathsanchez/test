#!/usr/bin/env python3
"""Source-exact independent proof checker, 100% Python standard library.

No call to the V13 synthesis script, SymPy, or LLL. Validates one-dimensional
state-rejection gap by exact 2D-lattice enumeration; complete weighted 5D
state schedules; 106-bit quotient-invariance; all source rejection guards.
"""
import json,math
from pathlib import Path
from fractions import Fraction as F

HERE=Path(__file__).parent
D=json.loads((HERE/'V13_CERTIFICATE.json').read_text())
assert D['protocol']=='3563c99349d7fee713425ead832c18f2ee0ab8a9'
M=(1<<107)-1; A=pow(3,121,M); U=1<<26
P=(1<<256)-(1<<224)+(1<<192)+(1<<96)-1
GX=int('6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296',16)
QMAX=(1<<30)-1;BOUND=M-(U-1);N=11
assert D['params']=={'M':str(M),'A':str(A),'u':U,'rejection_lower_bound':str(BOUND),'p':hex(P),'Gx':hex(GX),'limbs':N,'full_q_count':QMAX+1}


def det(matrix):
    if len(matrix)==1:return matrix[0][0]
    return sum((-1)**j*matrix[0][j]*det([row[:j]+row[j+1:] for row in matrix[1:]]) for j in range(len(matrix)))

def matmul(left,right):return [[sum(left[i][k]*right[k][j] for k in range(len(right))) for j in range(len(right[0]))] for i in range(len(left))]

def dot(a,b):return sum(x*y for x,y in zip(a,b))

def gs_exact(rows):
    N=len(rows);vectors=[];mu=[[F(0) for _ in rows] for _ in rows];norm=[]
    for i in range(N):
        v=[F(x) for x in rows[i]];orth=v[:]
        for j in range(i):
            mu[i][j]=dot(v,vectors[j])/norm[j]
            orth=[x-mu[i][j]*y for x,y in zip(orth,vectors[j])]
        vectors.append(orth)
        norm.append(dot(orth,orth))
        assert norm[i]>0
    assert all(dot(vectors[i],vectors[j])==0 for i in range(N) for j in range(i))
    return vectors,mu,norm

def integers_in_exact_radius(mid,rem,norm):
    if rem<0:return []
    fraction=rem/norm
    assert fraction>=0
    over=math.isqrt(fraction.numerator//fraction.denominator)+1
    f=mid.numerator//mid.denominator
    return range(f-over-1,f+over+3)

def exhaustive_lattice(rows,target,radius,maxnodes=2000000):
    N=len(rows);basis,mu,norm=gs_exact(rows)
    beta=[dot(target,basis[i])/norm[i] for i in range(N)]
    coeff=[0]*N
    completed=[];counter=[0]
    def dfs(i,used):
        counter[0]+=1
        if counter[0]>maxnodes:raise AssertionError('UNKNOWN_RESOURCE_TRUNCATION')
        if i<0:
            v=[int(sum(coeff[j]*rows[j][k] for j in range(N))) for k in range(N)]
            completed.append(v)
            return
        shift=sum(F(coeff[j])*mu[j][i] for j in range(i+1,N))
        middle=beta[i]-shift
        for z in integers_in_exact_radius(middle,radius-used,norm[i]):
            additional=(F(z)-middle)**2*norm[i]
            if used+additional<=radius:
                coeff[i]=z
                dfs(i-1,used+additional)
    dfs(N-1,F(0))
    return completed,counter[0]

# Source-rejection-gap proof covers all times 1..22, not only sampled states.
assert len(D['rejection_gap_witnesses'])==22
for d,case in enumerate(D['rejection_gap_witnesses'],start=1):
    assert case['d']==d
    B=[[1,pow(A,d,M)],[0,M]]
    T=case['unimodular_transform'];R=case['reduced_basis']
    assert abs(det(T))==1 and matmul(T,B)==R
    vectors,nodes=exhaustive_lattice(R,[F(0),F(0)],F(2*(U-1)**2),maxnodes=50000)
    assert nodes==case['nodes'] and len(vectors)==case['leaves']
    forbidden=[v for v in vectors if 1<=v[0]<U and 1<=v[1]<U]
    assert not forbidden and case['pairs']==[]

# Prove 106 fixed bits across every quotient, without enumerating q.
assert P%(1<<96)==(1<<96)-1
assert P%(1<<192)==(1<<96)-1
assert GX%(1<<52)>QMAX
xlow192=GX%(1<<192);final=xlow192+QMAX*((1<<96)-1)
assert final<(1<<192) and xlow192>>130==final>>130
masks=[(2,26),(3,18),(5,26),(6,26),(7,10)]
fixed={k:((GX>>(26*k))&((1<<bits)-1)) for k,bits in masks}
assert sum(bits for _,bits in masks)==106
for digit,bits in masks:
    assert D['invariants']['invariant_digit_lowbits'][str(digit)]=={'known_low_bits':bits,'value':fixed[digit]}

# One rejected draw at index zero is absorbed in arbitrary start state; V12
# independently proves that zero-rejection accepted sequence case has no match.
# For all other 10 locations and both endian models, enumerate all states.
assert len(D['schedule_witnesses'])==20
report=[]
for position in range(1,11):
    for orientation in ('msf','lsf'):
        matches=[x for x in D['schedule_witnesses'] if x['orientation']==orientation and x['skip_before_call']==position]
        assert len(matches)==1
        case=matches[0]
        time_of_call=lambda call:call+int(call>=position)
        obs=sorted((time_of_call(digit if orientation=='lsf' else 10-digit),
                    bits,fixed[digit],digit if orientation=='lsf' else 10-digit) for digit,bits in masks)
        assert case['observations']==[list(x) for x in obs]
        i0=obs[0][0];t0=obs[0][2]
        weights=[1<<item[1] for item in obs]
        H=[(M-1)//w for w in weights]
        ai=[pow(A,x[0]-i0,M) for x in obs]
        C=[1]+[(ai[k]*weights[0]*pow(weights[k],-1,M))%M for k in range(1,5)]
        c=[0]+[((obs[k][2]-ai[k]*t0)*pow(weights[k],-1,M))%M for k in range(1,5)]
        original=[[weights[0]]+[weights[j]*C[j] for j in range(1,5)]]+[[weights[j]*M if j==k else 0 for j in range(5)] for k in range(1,5)]
        T=case['unimodular_transform'];R=case['reduced_basis']
        assert abs(det(T))==1 and matmul(T,original)==R
        target=[F(weights[k]*H[k],2)+(weights[k]*c[k] if k else 0) for k in range(5)]
        radius=sum(F((weights[k]*H[k])**2,4) for k in range(5))
        vectors,nodes=exhaustive_lattice(R,target,radius)
        assert nodes==case['nodes'] and len(vectors)==case['sphere_leaves']
        allstates={}
        for v in vectors:
            assert all(v[k]%weights[k]==0 for k in range(5))
            hi=[v[0]//weights[0]]+[(v[j]//weights[j])-c[j] for j in range(1,5)]
            if any(hi[j]<0 or hi[j]>H[j] for j in range(5)):continue
            actual=[obs[j][2]+weights[j]*hi[j] for j in range(5)]
            if any(v<0 or v>=M for v in actual):continue
            current=actual[0]
            assert all(ai[j]*current%M==actual[j] for j in range(5))
            base=current*pow(A,-i0,M)%M
            states=[base*pow(A,k,M)%M for k in range(12)]
            accepted=[states[time_of_call(call)] for call in range(11)]
            rejected=states[position]
            for t,b,low,call in obs:assert accepted[call]&((1<<b)-1)==low
            lowwords=[s%U for s in accepted]
            if orientation=='lsf':lowwords.reverse()
            raw=0
            for limb in lowwords:raw=(raw<<26)+limb
            is_match=(raw%P)==GX
            source_guard=(rejected>=BOUND and all(s<BOUND for s in accepted))
            allstates[current]=(is_match,source_guard)
        assert len(allstates)==case['box_state_count']
        assert sorted(str(x) for x in allstates)==sorted(case['box_firststates'])
        found=sum(int(x[0]) for x in allstates.values())
        valid=sum(int(x[0] and x[1]) for x in allstates.values())
        assert found==case['full_matches']==0 and valid==case['source_valid_matches']==0
        report.append({'skip_before_call':position,'packing':orientation,
                       'box_states':len(allstates),'nodes':nodes,'matching_full_p256_Gx':valid})

# Authentic source high-state rejection controls: rejected exactly M-1, no
# consecutive rejected values in the 11-output window. Multiple cases.
for skip in [1,7,10]:
    seed_state=(M-1)*pow(A,-skip,M)%M
    stream=[seed_state*pow(A,k,M)%M for k in range(12)]
    assert stream[skip]==M-1>=BOUND
    assert all(stream[time_of] < BOUND for time_of in (i+int(i>=skip) for i in range(11)))

print(json.dumps({'verdict':'INDEPENDENT_EXACT_SOURCE_FREELIP_11x26_EXCLUDED',
 'rejection_gap_d_1_through_22':'ALL_NO_SECOND_REJECTION',
 'original_no_rejection_11_limb':'REUSE_V12_INDEPENDENT_CI',
 'all_2^30_q_covered_by_106_exact_invariant_bits':True,
 'single_rejection_cases':len(report),
 'candidate_hidden_state_count':sum(x['box_states'] for x in report),
 'valid_source_P256_Gx_matches':sum(x['matching_full_p256_Gx'] for x in report),
 'historical_NSA_G_generator':'UNKNOWN',
 'scope':'FreeLIP 26-bit exact source sampler only'},indent=2))
