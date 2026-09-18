"""Exact direct-descent cylinder compiler with explicit unresolved partition."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import time


def require(ok, message):
    if not ok: raise ValueError(message)


def verify(s):
    # Independent forward affine replay on the entire source cylinder.
    k, b = s['k'], s['b']
    require(type(k) is int and 0 <= k <= 64 and 0 <= b < 2**k, 'source domain')
    a, d, c = 2**k, b, 0
    for _ in range(k):
        require(a % 2 == 0, 'parity not constant on cylinder')
        if d % 2: a, d, c = 3*a, 3*d+1, c+1
        a, d = a//2, d//2
    require((a, c, d) == (3**s['c'], s['c'], s['d']), 'affine mismatch')
    if 'Q' in s:
        gap = 2**k - a
        require(gap > 0, 'no tail contraction')
        require(s['Q'] == max(0, (d-b)//gap+1), 'incorrect strict threshold')
        require(gap*s['Q']+b-d > 0, 'tail does not descend')
    return True


def compile_frontier(depth):
    require(1 <= depth <= 24, 'bounded compiler depth')
    frontier = [dict(k=0,b=0,c=0,d=0)]
    bank, exceptions = [], set()
    for _ in range(depth):
        pending = []
        for s in frontier:
            k,b,c,d = (s[x] for x in ('k','b','c','d'))
            for bit in (0,1):
                r = d + bit*3**c
                child = dict(k=k+1,b=b+bit*2**k,
                    c=c+(r%2),d=r//2 if r%2==0 else (3*r+1)//2)
                gap = 2**child['k']-3**child['c']
                if gap > 0:
                    child['Q'] = max(0,(child['d']-child['b'])//gap+1)
                    verify(child)
                    bank.append(child)
                    exceptions.update(2**child['k']*q+child['b']
                        for q in range(child['Q']) if 2**child['k']*q+child['b']>1)
                else:
                    pending.append(child)
        frontier = pending
    return bank, frontier, sorted(exceptions)


def classify(n, bank):
    if n <= 1: return None
    for s in bank:
        if n % 2**s['k'] == s['b'] and n//2**s['k'] >= s['Q']: return s
    return None


def scalar(n, budget):
    x = n
    for t in range(1,budget+1):
        x = x//2 if x%2==0 else (3*x+1)//2
        if 0 < x < n: return dict(n=n,t=t,y=x)
    return None


def verify_cover(bank, residual):
    seen = set()
    for s in sorted(bank+residual,key=lambda s:s['k']):
        verify(s)
        k,b=s['k'],s['b']
        require((k,b) not in seen, 'duplicate cylinder')
        require(all((j,b%2**j) not in seen for j in range(k)), 'overlapping cylinders')
        seen.add((k,b))
    require(sum((Fraction(1,2**s['k']) for s in bank+residual),Fraction())==1,
            'partition missing a cylinder')


def propagate(bank, low, high):
    # Each newly admitted certificate visits only its residue progression.
    admitted = {}
    guard_checks = 0
    for index,s in enumerate(bank):
        verify(s)
        modulus=2**s['k']
        first=max(s['Q'],(low-s['b']+modulus-1)//modulus)
        for n in range(modulus*first+s['b'], high+1, modulus):
            guard_checks += 1
            require(n not in admitted, 'overlapping admitted consequences')
            admitted[n]=index
    return admitted,guard_checks


def run(depth, output):
    start=time.perf_counter()
    bank,residual,exceptions=compile_frontier(depth)
    verify_cover(bank,residual)
    exception_proofs={n:scalar(n,10000) for n in exceptions}
    admitted,checks=propagate(bank,65537,131072)
    # Independently replay application claims; excluded from runtime reuse only,
    # but explicitly counted in this qualification's evidence.
    replay_steps=0
    for n,index in admitted.items():
        s=bank[index]; x=n
        for _ in range(s['k']):
            x=x//2 if x%2==0 else (3*x+1)//2
            replay_steps+=1
        require(x<n, 'invalid propagated descent')
    unresolved=[n for n in range(65537,131073) if n not in admitted]
    # Ablate all certificates: no symbolic obligation is discharged.
    empty,_=propagate([],65537,131072)
    require(not empty, 'ablation did not remove consequences')
    for n in unresolved:
        require(n in exceptions or any(n%2**s['k']==s['b'] for s in residual),
                'untracked evaluation residual')
    result=dict(depth=depth,certificates=len(bank),unresolved_cylinders=len(residual),
        unresolved_density=str(sum((Fraction(1,2**s['k']) for s in residual),Fraction())),
        scalar_exceptions=len(exceptions),exception_unknown=sum(v is None for v in exception_proofs.values()),
        evaluation_sources=65536,symbolically_closed=len(admitted),evaluation_unresolved=len(unresolved),
        application_guard_checks=checks,application_forward_steps=0,
        qualification_replay_steps=replay_steps,ablation_closed=len(empty),
        seconds=time.perf_counter()-start,
        verdict='PASS_EXACT_PARTITION_WITH_EXPLICIT_RESIDUAL',
        scope='direct descent only; no universal termination; no end-to-end speed claim')
    output.mkdir(parents=True,exist_ok=True)
    for name,obj in [('summary',result),('bank',bank),('residual',residual),
                     ('exception_proofs',exception_proofs),('evaluation_unresolved',unresolved)]:
        (output/(name+'.json')).write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n')
    # Canonical restart must preserve all symbolic applications.
    restored=json.loads((output/'bank.json').read_text())
    require(propagate(restored,65537,131072)[0]==admitted,'restart mismatch')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--depth',type=int,default=18)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.depth,a.output)
