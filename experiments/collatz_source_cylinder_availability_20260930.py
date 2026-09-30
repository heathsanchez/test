"""Compile actual original-source exits into universally admitted cylinders.

The finite ray union is not asserted complete. No new source search is used.
"""
import argparse,hashlib,json,pickle
from collections import Counter
from fractions import Fraction
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--cached-local',action='store_true');args=parser.parse_args()
if args.cached_local:
    parent,rows=pickle.load(open('v53-rows-local-cache.pickle','rb'))
else:
    from contextlib import redirect_stdout
    import io
    with redirect_stdout(io.StringIO()):
        import collatz_crystal_protected_reclosure_20260930 as audit
    parent=audit.parent;rows=audit.rows
assert parent=='16bc1fafea228c441faa11cd5c19b14a82df7739dba89673fc18127dcfceaecc'
N0=38911100780481085467; NC=3782158995862761504768
assert NC==2**59*3**8

def T(n):return (3*n+1)//2 if n%2 else n//2
sources=sorted({r['source'] for r in rows});certs=[];counts=Counter()
for n in sources:
    y=n;q=0;found=False
    for k in range(1601):
        kind=None;p=None;K=k;Y=y;Q=q
        if 0<y<n:kind='D'
        elif y%8==5 and y<=4*n:
            kind='S';p=(y-1)//4
            for _ in range(3):
                Q+=Y%2;Y=T(Y)
            K+=3
        elif y%3==2:
            p=(2*y-1)//3
            if 0<p<n:kind='M1'
        if kind:
            assert n<2**K and K>=59
            if kind=='D':assert 3**Q<=2**K
            else:
                assert 0<p<n and p%2==1 and T(p)==Y and Q>=1
                assert 2*3**(Q-1)<=2**K
            t=(n-N0)//NC;assert n==N0+NC*t
            mod=2**(K-59);assert 0<=t<mod
            cert={'n':str(n),'k':K,'y':str(Y),'q':Q,'kind':kind,
                  'p':None if kind=='D' else str(p),'t':str(t),'t_modulus':str(mod)}
            # Independent affine replay, retaining the actual original source.
            for u in (1,2,3,17,257):
                z=n+2**K*u;qq=0
                for _ in range(K):qq+=z%2;z=T(z)
                assert z==Y+3**Q*u and qq==Q
                if kind=='D':assert 0<z<n+2**K*u
                else:
                    lower=p+2*3**(Q-1)*u
                    assert 0<lower<n+2**K*u and T(lower)==z
            certs.append(cert);counts[kind]+=1;found=True;break
        q+=y%2;y=T(y)
    assert found
# The full positive residue class is represented, not just a ray threshold:
# n < 2^k and t < 2^(k-59) were independently checked above.
# Disjoint antichain of binary parameter cylinders gives exact Haar density.
minimal=[]
for c in sorted(certs,key=lambda c:(c['k'],int(c['t']))):
    t=int(c['t']);m=int(c['t_modulus'])
    if any(t%int(d['t_modulus'])==int(d['t']) for d in minimal):continue
    minimal.append(c)
density=sum((Fraction(1,int(c['t_modulus'])) for c in minimal),Fraction())
assert len(minimal)==len(certs)
# Find a small explicit parameter outside this finite union, without claiming
# its orbit is nonterminating or outside every earlier constructor.
uncovered_t=0
while any(uncovered_t%int(c['t_modulus'])==int(c['t']) for c in minimal):uncovered_t+=1
assert density<1
result={'schema':'COLLATZ_SOURCE_CYLINDER_AVAILABILITY_20260930','parent_certificate':parent,
        'sources':len(sources),'certificates':len(certs),'certificate_kinds':dict(counts),
        'minimum_steps':min(c['k'] for c in certs),'maximum_steps':max(c['k'] for c in certs),
        'parameter_cylinder_antichain':len(minimal),'parameter_union_density_numerator':str(density.numerator),
        'parameter_union_density_denominator':str(density.denominator),
        'first_parameter_outside_this_bank':str(uncovered_t),
        'first_source_outside_this_bank':str(N0+NC*uncovered_t),
        'certificate_bank_sha256':hashlib.sha256(json.dumps(certs,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'actual_availability':'Actual parity-word availability and source-bound exit on each emitted cylinder; requires hosted Lean qualification',
        'universal_bank_completeness':'REJECTED_BY_EXACT_UNCOVERED_PARAMETER',
        'global_collatz':'UNKNOWN',
        'boundary':'Every certificate preserves the original source and proves an actual fixed finite orbit word for all nonnegative cylinder parameters. This finite union is not complete. Outside-bank is not an infinite recurrent witness or a Collatz counterexample.'}
result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
Path('source-cylinder-result.json').write_text(json.dumps(result,indent=2,sort_keys=True))
Path('source-cylinder-certificates.json').write_text(json.dumps(certs,sort_keys=True))
print(json.dumps(result,indent=2,sort_keys=True),flush=True)

with open('GeneratedSourceCylinders.lean','w') as f:
    f.write('import Collatz.SourceCylinderExit\nset_option maxRecDepth 100000\nset_option maxHeartbeats 0\nnamespace CollatzFinal.SourceProduct\n')
    for i,c in enumerate(certs):
        n,k,y,q,p=(c[a] for a in ('n','k','y','q','p'))
        f.write(f'theorem source_cylinder_exit_{i} (u : Nat) : OrdinaryExit ({n} + 2 ^ {k} * u) (iter shortcut {k} ({n} + 2 ^ {k} * u)) := by\n')
        if c['kind']=='D':
            f.write(f'  exact ordinary_exit_of_source_cylinder_direct (q := {q}) (y := {y}) (by decide) (by decide) (by decide) (by decide) u\n')
        else:
            f.write(f'  exact ordinary_exit_of_source_cylinder_odd_merge (q := {q-1}) (y := {y}) (p := {p}) (by decide) (by decide) (by decide) (by decide) (by decide) (by decide) u\n')
        f.write(f'#print axioms source_cylinder_exit_{i}\n')
    pairs=', '.join('('+c['t']+', '+c['t_modulus']+')' for c in certs)
    f.write('def compiledParameterCylinders : List (Nat × Nat) := ['+pairs+']\n')
    f.write('def compiledParameterBankCovers (t : Nat) : Bool := compiledParameterCylinders.any (fun c => decide (t % c.2 = c.1))\n')
    f.write('theorem parameter_zero_outside_compiled_bank : compiledParameterBankCovers 0 = false := by decide\n#print axioms parameter_zero_outside_compiled_bank\n')
    f.write('end CollatzFinal.SourceProduct\n')
