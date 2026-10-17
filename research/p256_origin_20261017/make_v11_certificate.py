#!/usr/bin/env python3
"""Produce tiny standalone-checkable 2D projected-lattice exclusion witnesses."""
from sympy import Matrix, Rational
from fractions import Fraction as F
import json, pathlib, hashlib
from v11_full_state import M,A,P,GX,U,H,DIM,N,POWERS,INV_U,split,gram_schmidt_exact,dot

B=Matrix([[1]+list(POWERS[1:DIM])]+[[M if i==j else 0 for i in range(DIM)] for j in range(1,DIM)])
red,T=B.lll_transform(delta=Rational(3,4))
assert T*B==red and abs(int(T.det()))==1
result={
    'title':'Unimodular exact 2D projection certificate for 107-bit P256 hidden-state exclusion (10x26 no reject)',
    'formulation':'For each q in full range and both limb orders, every feasible 5-word state lies in a Euclidean ball of square radius 5H²/4 about the target affine lattice point; two final GS coefficient projections have no feasible integer pair.',
    'protocol_commit':'9d4f248ed15dfe0cff2d11e3db83e5d20f5a0834',
    'parameters':{'M':str(M),'A':str(A),'u':U,'nlimbs':N,'prefix':DIM,'p':hex(P),'Gx':hex(GX)},
    'unimodular_change':[[int(v) for v in T.row(i)] for i in range(DIM)],
    'reduced_basis':[[int(v) for v in red.row(i)] for i in range(DIM)],
    'claim':'NO_SOLUTION_FOR_ALL_STATES_AND_ALL_16_MODULAR_QUOTIENTS_BOTH_ORDERS',
    'source':'FreeLIP v1.1 1997, precise low26 output grammar WITHOUT rejection; not native historical 11-limb zrandomb(p)',
    'outcomes':[],
}
for q in range(((U**N-1-GX)//P)+1):
    for orientation in ('msf','lsf'):
        words=split(GX+q*P,orientation)
        c=[0]+[((words[i]-POWERS[i]*words[0])*INV_U)%M for i in range(1,DIM)]
        b=[[F(int(v)) for v in red.row(i)] for i in range(DIM)]
        gs,mu,norm=gram_schmidt_exact(b)
        center=[F(H,2)]+[F(c[i])+F(H,2) for i in range(1,DIM)]
        beta=[dot(center,gs[i])/norm[i] for i in range(DIM)]
        radius2=F(DIM*H*H,4)
        # Enumerate only the LAST two GS coefficients. Bracketing by exact +/-
        # integers rather than floating point yields rigorous exhaustion.
        from math import isqrt
        def bounds(mid,rem,denom):
            if rem<0:return []
            ratio=rem/denom
            rad=isqrt(ratio.numerator//ratio.denominator)+1
            base=mid.numerator//mid.denominator
            return range(base-rad-1,base+rad+3)
        feasible_z4=[];feasible_pairs=[]
        for z4 in bounds(beta[4],radius2,norm[4]):
            cost4=(F(z4)-beta[4])**2*norm[4]
            if cost4>radius2:continue
            feasible_z4.append(z4)
            b3=beta[3]-F(z4)*mu[4][3]
            for z3 in bounds(b3,radius2-cost4,norm[3]):
                cost3=(F(z3)-b3)**2*norm[3]
                if cost3+cost4<=radius2:feasible_pairs.append([z4,z3])
        assert not feasible_pairs,(q,orientation,feasible_pairs)
        result['outcomes'].append({'q':q,'orientation':orientation,
          'GS_last_coeff_count':len(feasible_z4),'GS_last_two_coeff_feasible_pairs':0})
out=pathlib.Path(__file__).parent/'V11_CERTIFICATE.json'
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('certificate bytes',out.stat().st_size,'cases',len(result['outcomes']), 'last-coeff survivors',sum(r['GS_last_coeff_count'] for r in result['outcomes']))
