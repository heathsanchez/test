"""Exhaustive symbolic parameter partition, with actual source admission.

A closed cell is an infinite arithmetic ray, not a sampled parameter.
No completeness claim is made for the surviving cells.
"""
import json,hashlib
from collections import Counter
from fractions import Fraction
N0=38911100780481085467;NC=3782158995862761504768

def T(n):return (3*n+1)//2 if n%2 else n//2

def cert(r,h):
    n=N0+NC*r;y=n;q=0;P=NC*2**h
    for k in range(59+h+1):
        # Parameter slope of the exact endpoint on this admitted cylinder.
        assert P%(2**k)==0
        C=3**q*(P//2**k)
        if 0<y<n and C<=P:
            return {'r':r,'h':h,'kind':'D','n':str(n),'k':k,'y':str(y),'q':q,'p':None,'source_slope':str(P)}
        if y%3==2 and C%3==0:
            p=(2*y-1)//3
            if 0<p<n and 2*C//3<=P:
                assert T(p)==y
                return {'r':r,'h':h,'kind':'M1','n':str(n),'k':k,'y':str(y),'q':q,'p':str(p),'source_slope':str(P)}
        if y%8==5 and y<=4*n and C%8==0 and C//4<=P:
            p=(y-1)//4;Y=y;Q=q
            for _ in range(3):Q+=Y%2;Y=T(Y)
            assert T(p)==Y and 0<p<n
            # Extra steps are admitted: C divisible by 8 fixes their parity.
            assert P%(2**(k+3))==0
            return {'r':r,'h':h,'kind':'S','n':str(n),'k':k+3,'y':str(Y),'q':Q,'p':str(p),'source_slope':str(P)}
        q+=y%2;y=T(y)
    return None
live=[0];closed=[];snapshots=[]
for h in range(19):
    residual=[];kinds=Counter()
    for r in live:
        c=cert(r,h)
        if c:
            # Independently replay far lift points on the parameter ray.
            for z in (0,1,17):
                n=N0+NC*(r+2**h*z);y=n;q=0
                for _ in range(c['k']):q+=y%2;y=T(y)
                assert q==c['q']
                C=3**q*(NC*2**h//2**c['k'])
                assert y==int(c['y'])+C*z
                if c['kind']=='D':assert 0<y<n
                else:
                    p=int(c['p'])+2*C//3*z
                    assert 0<p<n and T(p)==y
            closed.append(c);kinds[c['kind']]+=1
        else:residual.append(r)
    density=sum((Fraction(1,2**c['h']) for c in closed),Fraction())
    assert density+Fraction(len(residual),2**h)==1
    snapshots.append({'depth':h,'new_closed':dict(kinds),'closed_leaves':len(closed),'residual_cells':len(residual),'coverage_numerator':str(density.numerator),'coverage_denominator':str(density.denominator),'least_residual':min(residual,default=None)})
    print(json.dumps(snapshots[-1]),flush=True)
    if h<18:live=[x for r in residual for x in (r,r+2**h)]
result={'schema':'COLLATZ_BACKWARD_SYMBOLIC_SOURCE_COVER_20260930','family':{'N0':str(N0),'NC':str(NC)},'snapshots':snapshots,'closed_kinds':dict(Counter(c['kind'] for c in closed)),'unresolved_cells':residual,'global_collatz':'UNKNOWN','boundary':'Every depth partitions all natural parameters; closed cells have source-bound universally admitted exit words. Residual cells are not infinite orbits. This is one affine family, not a global least-bad-source cover.'}
result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
open('backward-cover-result.json','w').write(json.dumps(result,indent=2,sort_keys=True))
open('backward-cover-certificates.json','w').write(json.dumps(closed,sort_keys=True))
# The generator emits an actual certified tree, not a coverage assumption.
from pathlib import Path
with open('GeneratedBackwardCover.lean','w') as f:
    f.write('import Collatz.BackwardParameterCover\nset_option maxRecDepth 100000\nset_option maxHeartbeats 0\nnamespace CollatzFinal.SourceProduct\n')
    lookup={}
    for i,c in enumerate(closed):
        lookup[c['r'],c['h']]=i
        n,k,y,q,p=(c[a] for a in ('n','k','y','q','p'));r,h=c['r'],c['h']
        unit=int(c['source_slope'])//2**k
        assert int(c['source_slope'])==2**k*unit and unit>0
        f.write(f'theorem backward_cell_exit_{i} (u : Nat) : OrdinaryExit (familySource {r} {h} u) (iter shortcut {k} (familySource {r} {h} u)) := by\n')
        if c['kind']=='D':
            assert 3**q<=2**k
            f.write(f'  have hx := ordinary_exit_of_source_cylinder_direct (n := {n}) (k := {k}) (q := {q}) (y := {y}) (by decide) (by decide) (by decide) (by decide) ({unit} * u)\n')
        else:
            assert 2*3**(q-1)<=2**k
            f.write(f'  have hx := ordinary_exit_of_source_cylinder_odd_merge (n := {n}) (k := {k}) (q := {q-1}) (y := {y}) (p := {p}) (by decide) (by decide) (by decide) (by decide) (by decide) (by decide) ({unit} * u)\n')
        f.write('  simpa [familySource, Nat.mul_add, Nat.mul_assoc] using hx\n')
        f.write(f'#print axioms backward_cell_exit_{i}\n')
    def term(r,h):
        if (r,h) in lookup:
            i=lookup[r,h];return f'(.closed {closed[i]["k"]} backward_cell_exit_{i})'
        if h==18:
            assert r in residual
            return '.unresolved'
        return f'(.split {term(r,h+1)} {term(r+2**h,h+1)})'
    f.write('def backwardCertifiedCover : CertifiedParameterCover 0 0 := '+term(0,0)+'\n')
    f.write('theorem backward_closed_leaf_count : parameterCoverClosedLeaves backwardCertifiedCover = 3294 := by decide\n')
    f.write('theorem backward_residual_leaf_count : parameterCoverResidualLeaves backwardCertifiedCover = 22485 := by decide\n')
    f.write('theorem backward_covered_parameter_slots : parameterCoverClosedSlots backwardCertifiedCover 18 = 239659 := by decide\n')
    f.write('theorem backward_parameter_zero_closed : parameterCoverResidual backwardCertifiedCover 0 = false := by decide\n')
    f.write('theorem backward_parameter_one_unresolved : parameterCoverResidual backwardCertifiedCover 1 = true := by decide\n')
    f.write('theorem family_exit_outside_exact_residual (t : Nat) (hc : parameterCoverResidual backwardCertifiedCover t = false) : ∃ k, OrdinaryExit (familySource 0 0 t) (iter shortcut k (familySource 0 0 t)) := ordinary_exit_of_certified_parameter_cover backwardCertifiedCover t hc\n')
    for name in ('backward_closed_leaf_count','backward_residual_leaf_count','backward_covered_parameter_slots','backward_parameter_zero_closed','backward_parameter_one_unresolved','family_exit_outside_exact_residual'):
        f.write('#print axioms '+name+'\n')
    f.write('end CollatzFinal.SourceProduct\n')
print('GENERATED_EXACT_CERTIFIED_PARTIAL_PARAMETER_COVER',flush=True)
