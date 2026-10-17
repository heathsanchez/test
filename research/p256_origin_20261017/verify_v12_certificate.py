#!/usr/bin/env python3
"""Verify V12 complete 11-limb state exclusion with ONLY Python standard library.

Checks the asserted invariant bit slices over ALL q by integer inequalities,
unimodular basis equality, rational 5D lattice enumeration, full source PRNG
replay, and that the exact candidate list does not contain the published Gx.
SymPy and LLL are NOT used by this verifier.
"""
import json
import math
from pathlib import Path
from fractions import Fraction as F

HERE=Path(__file__).parent
D=json.loads((HERE/'V12_CERTIFICATE.json').read_text())
M=(1<<107)-1
A=pow(3,121,M)
P=(1<<256)-(1<<224)+(1<<192)+(1<<96)-1
GX=int('6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296',16)
U=1<<26; N=11; DIM=5; Q=(1<<30)-1
assert D['protocol_commit']=='9578ccae67a49f68c4e85ebe0103f46733e8125e'
assert D['parameters']=={'M':str(M),'A':str(A),'P':hex(P),'GX':hex(GX),'U':U,'N':N,'DIM':DIM,'qmax':Q}

# Whole-domain algebraic invariant proof, no q enumeration:
assert P%(1<<96)==(1<<96)-1
assert P%(1<<192)==(1<<96)-1
assert GX%(1<<52)>Q
s0=GX%(1<<192)
end=s0+Q*((1<<96)-1)
assert end<(1<<192)
assert s0>>130==end>>130
masks=[(2,26),(3,18),(5,26),(6,26),(7,10)]
fixed={i:((GX>>(26*i))&((1<<b)-1)) for i,b in masks}
assert sum(b for _,b in masks)==106
assert len(D['orientation_certificates'])==2
assert set(x['orientation'] for x in D['orientation_certificates'])=={'msf','lsf'}
for i,b in masks:
    assert D['q_invariant_guards']['invariant_digit_lowbits'][str(i)]=={'known_low_bits':b,'value':fixed[i]}


def det(m):
    if len(m)==1:return m[0][0]
    return sum((-1)**j*m[0][j]*det([row[:j]+row[j+1:] for row in m[1:]]) for j in range(len(m)))


def dot(x,y):return sum(a*b for a,b in zip(x,y))


def mulmat(a,b):return [[sum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]


def integer_envelope(center,remaining,norm):
    if remaining<0:return []
    rat=remaining/norm
    assert rat>=0
    above=math.isqrt(rat.numerator//rat.denominator)+1
    floorcenter=center.numerator//center.denominator
    # The interval encloses EVERY integer z with (z-center)^2<=remaining/norm.
    return range(floorcenter-above-1,floorcenter+above+3)

report=[]
for claimed in D['orientation_certificates']:
    orientation=claimed['orientation']
    obs=sorted((i if orientation=='lsf' else N-1-i,b,fixed[i]) for i,b in masks)
    assert claimed['observations']==[list(x) for x in obs]
    i0=obs[0][0];t0=obs[0][2]
    weights=[1<<b for _,b,_ in obs]
    H=[(M-1)//w for w in weights]
    ai=[pow(A,i-i0,M) for i,_,_ in obs]
    Cs=[1]+[(ai[k]*weights[0]*pow(weights[k],-1,M))%M for k in range(1,DIM)]
    cs=[0]+[((obs[k][2]-ai[k]*t0)*pow(weights[k],-1,M))%M for k in range(1,DIM)]
    basis=[[weights[0]]+[weights[k]*Cs[k] for k in range(1,DIM)]]+[[weights[j]*M if j==k else 0 for j in range(DIM)] for k in range(1,DIM)]
    T=claimed['unimodular_transform'];B=claimed['reduced_basis']
    assert abs(det(T))==1
    assert mulmat(T,basis)==B
    # Exact rational GS: only the source-provided certificate transform is used.
    gs=[];nu=[[F(0)]*DIM for _ in range(DIM)];norm=[]
    for i in range(DIM):
        v=[F(z) for z in B[i]]
        current=v[:]
        for j in range(i):
            nu[i][j]=dot(v,gs[j])/norm[j]
            current=[x-nu[i][j]*y for x,y in zip(current,gs[j])]
        gs.append(current);norm.append(dot(current,current))
        assert norm[i]>0
    assert all(dot(gs[i],gs[j])==0 for i in range(DIM) for j in range(i))
    center=[F(weights[k]*H[k],2)+(weights[k]*cs[k] if k else 0) for k in range(DIM)]
    beta=[dot(center,gs[k])/norm[k] for k in range(DIM)]
    radius=sum(F((weights[k]*H[k])**2,4) for k in range(DIM))
    z=[0]*DIM; nodes=0; leaves=0; states=set(); any_p256=False
    def search(k,consumed):
        global nodes,leaves,any_p256
        nodes+=1
        assert nodes<=2_000_000,'UNKNOWN_RESOURCE_EXACT_ENUMERATION_INCOMPLETE'
        if k==-1:
            leaves+=1
            vector=[int(sum(z[j]*B[j][i] for j in range(DIM))) for i in range(DIM)]
            assert all(vector[i]%weights[i]==0 for i in range(DIM))
            hs=[vector[0]//weights[0]]+[(vector[i]//weights[i])-cs[i] for i in range(1,DIM)]
            if any(hs[i]<0 or hs[i]>H[i] for i in range(DIM)):return
            targets=[obs[i][2]+weights[i]*hs[i] for i in range(DIM)]
            if any(s<0 or s>=M for s in targets):return
            st=targets[0]
            assert all(ai[i]*st%M==targets[i] for i in range(DIM))
            states.add(st)
            temporal_first=st*pow(A,-i0,M)%M
            temporal=[temporal_first*pow(A,k,M)%M for k in range(N)]
            output=[s%U for s in temporal]
            if orientation=='lsf':output.reverse()
            raw=0
            for word in output:raw=(raw<<26)+word
            if raw%P==GX:any_p256=True
            return
        offset=sum(F(z[j])*nu[j][k] for j in range(k+1,DIM))
        middle=beta[k]-offset
        for value in integer_envelope(middle,radius-consumed,norm[k]):
            diff=(F(value)-middle)**2*norm[k]
            if diff+consumed<=radius:
                z[k]=value
                search(k-1,consumed+diff)
    search(DIM-1,F(0))
    assert nodes==claimed['expected_exact_nodes']
    assert leaves==claimed['expected_sphere_leaves']
    assert len(states)==claimed['expected_box_states']
    assert sorted(str(s) for s in states)==sorted(claimed['expected_first_observation_states'])
    assert not any_p256 and claimed['expected_no_matching_full_x']
    report.append({'packing':orientation,'states_compatible_with_106_bits':len(states),
                   'examined_lattice_nodes':nodes,'sphere_leaves':leaves,
                   'published_P256_full_Gx_matches':0})
print(json.dumps({'verdict':'WARRANTED_11_LIMB_EXACT_NO_REJECTION_MODEL',
 'boundedness':'not historical provenance; skip/rejection variants NOT covered',
 'full_2^30_q_domain_invariants_verified':True,
 'all_state_candidates_complete':True,
 'orientation_tests':report},indent=2))
