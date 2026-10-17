#!/usr/bin/env python3
"""Source-grounded P-256 FreeLIP inverse-state census (V11, frozen 10x26 grammar).

Designed to be auditable and independently replayable: every one of the 107-bit
initial states is excluded if exact lattice sphere/box enumeration returns empty.
No assumptions about small seeds, clocks, or position, only 10 consecutive
accepted outputs (no FreeLIP rejection) at 26 bits, either limb order.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time
from fractions import Fraction as Q
from sympy import Matrix, Rational

M=(1 << 107)-1
A=pow(3,121,M)
U=1 << 26
H=(M-1)//U
N=10
DIM=5
P=int('FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF',16)
GX=int('6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296',16)
INV_U=pow(U,-1,M)
POWERS=tuple(pow(A,i,M) for i in range(N))
BASE=Path(__file__).resolve().parent


def states(seed, first, count):
    s=seed%M
    for _ in range(first):s=s*A%M
    out=[]
    for i in range(count):
        s=s*A%M
        out.append(s)
    return out


def pack(words, orientation):
    if orientation=='lsf': words=words[::-1]
    value=0
    for w in words:
        assert 0<=w<U
        value=(value<<26)+w
    return value


def split(value, orientation):
    assert 0<=value<(1<<(26*N))
    words=[(value>>(26*i)) & (U-1) for i in range(N)]
    if orientation=='msf':words.reverse()
    assert pack(words,orientation)==value
    return words


def dot(a,b):return sum(x*y for x,y in zip(a,b))


def gram_schmidt_exact(rows):
    gs=[]; mu=[[Q(0) for _ in rows] for _ in rows]; norms=[]
    for i,row in enumerate(rows):
        orth=[Q(int(x)) for x in row]
        for j in range(i):
            factor=dot(row,gs[j])/norms[j]
            mu[i][j]=factor
            orth=[a-factor*b for a,b in zip(orth,gs[j])]
        gs.append(orth)
        norm=dot(orth,orth)
        assert norm>0
        norms.append(norm)
    assert all(dot(gs[i],gs[j])==0 for i in range(len(rows)) for j in range(i))
    return gs,mu,norms


def row_lattice(words):
    c=[0]+[((words[i]-POWERS[i]*words[0])*INV_U)%M for i in range(1,DIM)]
    basis=Matrix([[1]+list(POWERS[1:DIM])] +
                 [[(M if i==j else 0) for i in range(DIM)] for j in range(1,DIM)])
    assert basis.det()==M**(DIM-1)
    # Independently verifiable unimodular change of lattice basis.
    reduced, transform=basis.lll_transform(delta=Rational(3,4))
    assert transform*basis==reduced
    assert abs(int(transform.det()))==1
    return [[Q(int(x)) for x in reduced.row(i)] for i in range(DIM)],c


def complete_hidden_state_census(words, max_nodes=50000):
    assert len(words)==N and all(0<=x<U for x in words)
    start=time.perf_counter()
    b,c=row_lattice(words)
    gs,mu,norms=gram_schmidt_exact(b)
    target=[Q(H,2)]+[Q(c[i])+Q(H,2) for i in range(1,DIM)]
    beta=[dot(target,gs[i])/norms[i] for i in range(DIM)]
    rad2=Q(DIM*H*H,4)
    coeff=[0]*DIM; explored=0; sphere_leaves=0; box_leaves=0; states_found=[]; maxima=[]
    def dfs(index, used):
        nonlocal explored,sphere_leaves,box_leaves
        explored+=1
        if explored>max_nodes:raise RuntimeError('RESOURCE_LIMIT_NOT_EXHAUSTIVE')
        if index<0:
            sphere_leaves+=1
            vector=[sum(coeff[j]*b[j][k] for j in range(DIM)) for k in range(DIM)]
            highs=[vector[0]]+[vector[i]-c[i] for i in range(1,DIM)]
            if not all(0<=x<=H for x in highs):return
            trial=[words[i]+U*highs[i] for i in range(DIM)]
            if not all(0<=x<M for x in trial):return
            box_leaves+=1
            s0=int(trial[0])
            assert all((POWERS[i]*s0)%M==trial[i] for i in range(DIM))
            seq=[int((POWERS[i]*s0)%M)%U for i in range(N)]
            states_found.append({'first_output_state':str(s0),
                                 'full_10_match':seq==words,
                                 'matched_prefix_limbs':DIM,
                                 'direct_generated_limbs':seq})
            return
        off=sum(Q(coeff[j])*mu[j][index] for j in range(index+1,DIM))
        center=beta[index]-off
        remainder=rad2-used
        if remainder<0:return
        ratio=remainder/norms[index]
        # Exact nonunderestimating integer bound, no floating-point/sqrt-
        # rounding heuristic can discard a legitimate lattice coefficient.
        floor_width=math.isqrt(ratio.numerator//ratio.denominator)
        radius_upper=floor_width+1
        middle=center.numerator//center.denominator
        lo=middle-radius_upper-1
        hi=middle+radius_upper+2
        maxima.append(hi-lo+1)
        for integer in range(lo,hi+1):
            term=(Q(integer)+off-beta[index])**2*norms[index]
            if used+term<=rad2:
                coeff[index]=integer
                dfs(index-1,used+term)
    dfs(DIM-1,Q(0))
    return {'exhaustive':True,'sphere_nodes':explored,'sphere_leaves':sphere_leaves,
            'box_feasible_states':box_leaves,'full_matches':sum(int(x['full_10_match']) for x in states_found),
            'states':states_found,'max_exact_integer_interval':max(maxima or [0]),
            'elapsed_seconds':round(time.perf_counter()-start,5),
            'gram_schmidt_norm_floor_log2':[(n.numerator.bit_length()-n.denominator.bit_length()) for n in norms]}


def run():
    p=argparse.ArgumentParser();p.add_argument('--out',default=str(BASE/'V11_RESULTS.json'))
    args=p.parse_args()
    # Two synthetic-known-source 107-bit positive controls. Both use real
    # original FreeLIP modular arithmetic and P-256 modulus for observability.
    controls=[]
    for seed,skip in [(20000,7),(20420,29),(123456789011,3)]:
        all_states=states(seed,skip,N)
        words=[int(s)%U for s in all_states]
        for orientation in ('msf','lsf'):
            original=pack(words,orientation)
            x=original%P
            q=(original-x)//P
            recovered=split(x+q*P,orientation)
            assert recovered==words
            proof=complete_hidden_state_census(recovered)
            assert proof['full_matches']>=1, (seed,skip,orientation,proof)
            assert any(int(z['first_output_state'])==all_states[0] and z['full_10_match'] for z in proof['states'])
            controls.append({'seed':seed,'skip':skip,'orientation':orientation,'q':q,
                             'actual_first_state':str(all_states[0]),
                             'matched_states':proof['full_matches'],
                             'enumerated_box_states':proof['box_feasible_states'],
                             'complete_exact_lattice_enumeration':proof['exhaustive']})
    # All modular quotients; raw representation constraint is exact and finite.
    q_max=((U**N-1-GX)//P)
    assert q_max==15, q_max
    runs=[]
    for q in range(q_max+1):
        raw=GX+q*P
        assert raw < U**N
        for orientation in ('msf','lsf'):
            words=split(raw,orientation)
            result=complete_hidden_state_census(words)
            runs.append({'q':q,'orientation':orientation,
                         'candidate_raw_hex':hex(raw),
                         'exact_lattice_census':{k:v for k,v in result.items() if k not in ('elapsed_seconds','states')},
                         'direct_full_10_matches':result['full_matches'],
                         'seconds':result['elapsed_seconds']})
    total_matches=sum(r['direct_full_10_matches'] for r in runs)
    status=('BOUNDED_10_LIMB_107_BIT_NO_STATE_EXACT' if total_matches==0 else 'NUMERICAL_MATCH_CANDIDATE_ONLY')
    outcome={'title':'V11 FreeLIP all-107bit-state inverse exact lattice census',
        'status':status,'scope':'exact 10 consecutive zrandom(2^26) low-bit draws, no rejection, msf or lsf, reduced modulo P256 prime; not 11-limb historical zrandomb(p)',
        'source':'FreeLIP v1.1 1997 mirror commit 00898a4814d2cc1244bf348682be6ed10dda35f0 (lip.c/h); no original NSA call path',
        'frozen_protocol_commit':'9d4f248ed15dfe0cff2d11e3db83e5d20f5a0834',
        'parameters':{'M':str(M),'A':str(A),'u':U,'N':N,'GS_dim':DIM,'Q_max_inclusive':q_max,
                      'target_Gx_hex':hex(GX),'p_hex':hex(P)},
        'synthetic_known_state_positive_controls':controls,
        'quotient_orientation_cases':runs,
        'all_quotient_cases':len(runs),'total_state_hits':total_matches,
        'every_case_exactly_exhaustive':all(r['exact_lattice_census']['exhaustive'] for r in runs),
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'implementation_note':'Exact rational Gram-Schmidt; lattice basis verified unimodular; integer bounds overestimate true Euclidean radius without floats; every candidate independently replayed',
        'epistemic':{'historical_P256_G_origin':'UNKNOWN', '11_limb_original_freelip_path':'UNTESTED','search_failure':'EXACT_SCOPE_RELATIVE_FOR_10_LIMBS_ONLY','all_107_bit_initial_states':'INCLUDED_FOR_THIS_GRAMMAR','independent_external_CI':'NOT_YET_QUALIFIED','security_vulnerability':'NOT_CLAIMED'}}
    Path(args.out).write_text(json.dumps(outcome,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':status,'exact_cases':len(runs),'total_state_hits':total_matches,
                      'max_nodes':max(r['exact_lattice_census']['sphere_nodes'] for r in runs),
                      'controls':len(controls),'file':args.out},indent=2))
    assert total_matches==0

if __name__=='__main__':run()
