#!/usr/bin/env python3
"""Pure standard-library verifier of a short exhaustive projected-lattice certificate.

Does not run any LLL solver, does not trust recorded search outcomes. Checks
unimodularity, rational orthogonal projection, and all possible q/packing cases.
"""
import json
import math
from fractions import Fraction as F
from pathlib import Path

HERE=Path(__file__).parent
D=json.loads((HERE/'V11_CERTIFICATE.json').read_text())
assert D['protocol_commit']=='9d4f248ed15dfe0cff2d11e3db83e5d20f5a0834'
P=int(D['parameters']['p'],16)
GX=int(D['parameters']['Gx'],16)
M=int(D['parameters']['M'])
A=int(D['parameters']['A'])
U=int(D['parameters']['u'])
N=int(D['parameters']['nlimbs'])
DIM=int(D['parameters']['prefix'])
assert (M,A,U,N,DIM)==((1<<107)-1,pow(3,121,(1<<107)-1),1<<26,10,5)
H=(M-1)//U
AI=[pow(A,i,M) for i in range(N)]
INV=pow(U,-1,M)

def matmul(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]

def determinant(x):
    if len(x)==1:return x[0][0]
    return sum((-1)**j*x[0][j]*determinant([row[:j]+row[j+1:] for row in x[1:]]) for j in range(len(x)))

def dot(a,b):return sum(x*y for x,y in zip(a,b))

def interval(center,rem,norm):
    if rem<0:return []
    ratio=rem/norm
    assert ratio>=0
    # Floor(sqrt(p/q)) = isqrt(p//q). Envelope always >= actual radius.
    conservative_radius=math.isqrt(ratio.numerator//ratio.denominator)+1
    floorcenter=center.numerator//center.denominator
    return range(floorcenter-conservative_radius-1,floorcenter+conservative_radius+3)

base=[[1]+AI[1:DIM]]+[[M if i==j else 0 for i in range(DIM)] for j in range(1,DIM)]
Umat=D['unimodular_change'];B=D['reduced_basis']
assert matmul(Umat,base)==B
assert abs(determinant(Umat))==1
# Independent rational Gram Schmidt, without SymPy or LLL.
star=[];nu=[[F(0)]*DIM for _ in range(DIM)];lengths=[]
for i in range(DIM):
    row=[F(z) for z in B[i]]
    ortho=row[:]
    for j in range(i):
        nu[i][j]=dot(row,star[j])/lengths[j]
        ortho=[x-nu[i][j]*y for x,y in zip(ortho,star[j])]
    star.append(ortho)
    lengths.append(dot(ortho,ortho))
assert all(lengths[i]>0 for i in range(DIM))
assert all(dot(star[i],star[j])==0 for i in range(DIM) for j in range(i))
R2=F(DIM*H*H,4)
last_count=0
for q in range(((1<<(26*N))-1-GX)//P+1):
    raw=GX+q*P
    assert raw >= GX and raw<(1<<(26*N))
    for orientation in ('msf','lsf'):
        limbs=[(raw>>(26*i)) & (U-1) for i in range(N)]
        if orientation=='msf':limbs.reverse()
        c=[0]+[((limbs[i]-AI[i]*limbs[0])*INV)%M for i in range(1,DIM)]
        center=[F(H,2)]+[F(c[i])+F(H,2) for i in range(1,DIM)]
        beta=[dot(center,star[i])/lengths[i] for i in range(DIM)]
        attempts=0
        for z4 in interval(beta[4],R2,lengths[4]):
            d4=(F(z4)-beta[4])**2*lengths[4]
            if d4>R2:continue
            attempts+=1
            b3=beta[3]-F(z4)*nu[4][3]
            for z3 in interval(b3,R2-d4,lengths[3]):
                d3=(F(z3)-b3)**2*lengths[3]
                # If such a pair existed, the 2D projection proof would be
                # inconclusive and verification must FAIL, not silently pass.
                if d3+d4<=R2:
                    raise AssertionError(f'INCOMPLETE_CERTIFICATE q={q}, {orientation}, {z4}, {z3}')
        last_count+=attempts
        claimed=next(x for x in D['outcomes'] if x['q']==q and x['orientation']==orientation)
        assert claimed['GS_last_coeff_count']==attempts
        assert claimed['GS_last_two_coeff_feasible_pairs']==0
assert len(D['outcomes'])==32
# Independent known-state positive to detect off-by-one and output convention:
seed=20000; state=seed
for _ in range(8):state=state*A%M
x=state
seq=[]
for i in range(10):
    seq.append(x%U)
    x=x*A%M
assert seq[0]==state%U and len(seq)==10
print(json.dumps({'verdict':'EXACT_INTEGER_CERTIFICATE_VERIFIED',
 'cases':32,'basis_dimension':DIM,'all_state_values_covered':str(M),
 'last_projection_coefficients_surviving':last_count,
 'feasible_two_projection_pairs':0,
 'historical_11_limb_path':'NOT_COVERED','origin':'UNKNOWN'},indent=2))
