#!/usr/bin/env python3
"""Package the unimodular coordinate transforms for independent V12 verification."""
import json,hashlib, pathlib
from sympy import Matrix, Rational
from v12_inverse import M,A,P,GX,U,DIM,N,QMAX,PROTO,invariants,observed_from_invariants
ROOT=pathlib.Path(__file__).parent
V=json.loads((ROOT/'V12_RESULTS.json').read_text())
assert V['protocol_commit']==PROTO
inv=invariants()
cert={'name':'V12 exact full-state 11x26 source-native FreeLIP obstruction certificate',
      'protocol_commit':PROTO,
      'parameters':{'M':str(M),'A':str(A),'P':hex(P),'GX':hex(GX),'U':U,'N':N,'DIM':DIM,'qmax':QMAX},
      'q_invariant_guards':inv,
      'orientation_certificates':[],
      'claim':'no full 11-word P256 Gx match across any 107-bit state / 2^30 quotients for no-rejection FreeLIP 26-bit grammar'}
for orientation in ('msf','lsf'):
    obs=observed_from_invariants(orientation,inv)
    i0,b0,t0=obs[0]
    w=[1<<b for _,b,_ in obs]
    a=[pow(A,i-i0,M) for i,_,_ in obs]
    C=[1]+[(a[k]*w[0]*pow(w[k],-1,M))%M for k in range(1,DIM)]
    basis=Matrix([[w[0]]+[w[k]*C[k] for k in range(1,DIM)]]+
                 [[w[j]*M if j==k else 0 for j in range(DIM)] for k in range(1,DIM)])
    reduced,T=basis.lll_transform(delta=Rational(3,4))
    assert reduced==T*basis and abs(int(T.det()))==1
    rr=next(x for x in V['target_orientations'] if x['orientation']==orientation)
    cert['orientation_certificates'].append({
        'orientation':orientation,
        'observations':[list(z) for z in obs],
        'unimodular_transform':[[int(x) for x in T.row(i)] for i in range(DIM)],
        'reduced_basis':[[int(x) for x in reduced.row(i)] for i in range(DIM)],
        'expected_exact_nodes':rr['exact_total_nodes'],
        'expected_sphere_leaves':rr['exact_sphere_leaves'],
        'expected_box_states':rr['true_box_hidden_states'],
        'expected_first_observation_states':[x['first_observation_state'] for x in rr['states']],
        'expected_no_matching_full_x':all(not x['matches_P256_Gx'] for x in rr['states'])})
out=ROOT/'V12_CERTIFICATE.json'
out.write_text(json.dumps(cert,sort_keys=True,indent=2)+'\n')
print('V12 certificate',out.stat().st_size,'bytes,',len(cert['orientation_certificates']),'orientations')
