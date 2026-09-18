"""Symbolic direct descent plus inverse-odd lower merges; explicit residuals."""
import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import collatz_symbolic_frontier as base


def source(s):
    return {key:s[key] for key in ('k','b','c','d')}


def reconstruction(s):
    if s['kind']=='descent': return 3**s['c'],s['d']
    base.require(s['kind']=='inverse_odd','unknown constructor')
    base.require(s['c']>=1 and s['d']%3==2,'nonintegral predecessor family')
    return 2*3**(s['c']-1),(2*s['d']-1)//3


def verify_merge(s):
    base.verify(source(s))
    a,b=reconstruction(s)
    gap=2**s['k']-a
    base.require(gap>0,'no tail improvement')
    base.require(s['Q']==max(0,(b-s['b'])//gap+1),'incorrect strict threshold')
    base.require(a*s['Q']+b>0,'nonpositive reconstructed predecessor')
    if s['kind']=='inverse_odd':
        base.require(a%2==0 and b%2==1,'predecessor is not uniformly odd')
        base.require(3*a==2*3**s['c'] and 3*b+1==2*s['d'],'inverse identity')


def compile_portfolio(depth):
    base.require(1<=depth<=24,'bounded depth')
    frontier=[dict(k=0,b=0,c=0,d=0)]
    bank=[];exceptions=set()
    for _ in range(depth):
        pending=[]
        for s in frontier:
            k,b,c,d=(s[x] for x in ('k','b','c','d'))
            for bit in (0,1):
                r=d+bit*3**c
                child=dict(k=k+1,b=b+bit*2**k,c=c+r%2,
                           d=r//2 if r%2==0 else (3*r+1)//2)
                selected=None
                for kind in ('descent','inverse_odd'):
                    if kind=='inverse_odd' and (child['c']==0 or child['d']%3!=2): continue
                    candidate=dict(child,kind=kind)
                    a,offset=reconstruction(candidate)
                    gap=2**child['k']-a
                    if gap<=0: continue
                    candidate['Q']=max(0,(offset-child['b'])//gap+1)
                    if a*candidate['Q']+offset<=0: continue
                    verify_merge(candidate);selected=candidate;break
                if selected is None: pending.append(child)
                else:
                    bank.append(selected)
                    exceptions.update(2**child['k']*q+child['b'] for q in range(selected['Q'])
                                      if 2**child['k']*q+child['b']>1)
        frontier=pending
    return bank,frontier,sorted(exceptions)


def verify_partition(bank,residual):
    for s in bank: verify_merge(s)
    base.verify_cover([source(s) for s in bank],residual)


def applications(bank,low,high):
    result={}
    for i,s in enumerate(bank):
        modulus=2**s['k']
        first=max(s['Q'],(low-s['b']+modulus-1)//modulus)
        for n in range(modulus*first+s['b'],high+1,modulus):
            base.require(n not in result,'overlapping consequences')
            result[n]=i
    return result


def run(depth,output):
    bank,residual,exceptions=compile_portfolio(depth)
    verify_partition(bank,residual)
    old,old_residual,old_exceptions=base.compile_frontier(depth)
    base.verify_cover(old,old_residual)
    low,high=65537,131072
    admitted=applications(bank,low,high)
    baseline=applications(old,low,high)
    # Direct-descent coverage must be retained in this evaluation cohort.
    base.require(set(baseline)<=set(admitted),'portfolio lost protected coverage')
    replay_steps=0
    for n,index in admitted.items():
        s=bank[index];q=n//2**s['k'];x=n
        for _ in range(s['k']):
            x=x//2 if x%2==0 else (3*x+1)//2;replay_steps+=1
        a,b=reconstruction(s);p=a*q+b
        base.require(0<p<n,'not a lower merge')
        if s['kind']=='descent':base.require(p==x,'descent endpoint mismatch')
        else:
            base.require(p%2==1 and (3*p+1)//2==x,'coalescence replay mismatch')
            replay_steps+=1
    exception_proofs={n:base.scalar(n,10000) for n in exceptions}
    unknown_exceptions=[n for n,p in exception_proofs.items() if p is None]
    for n,p in exception_proofs.items():
        if p:
            x=n
            for _ in range(p['t']): x=x//2 if x%2==0 else (3*x+1)//2
            base.require(x==p['y'] and 0<x<n,'scalar exception proof invalid')
    unresolved=sorted(set(range(low,high+1))-set(admitted))
    residual_b={s['b'] for s in residual}
    base.require(residual_b <= {s['b'] for s in old_residual},
                 'portfolio introduced an uncovered cylinder')
    for n in unresolved:
        base.require(n in exceptions or n%2**depth in residual_b,'lost residual obligation')
    gain=sorted(set(admitted)-set(baseline))
    summary=dict(depth=depth,certificates=len(bank),constructors=dict(Counter(s['kind'] for s in bank)),
        baseline_residual_cylinders=len(old_residual),portfolio_residual_cylinders=len(residual),
        baseline_residual_density=str(Fraction(len(old_residual),2**depth)),
        portfolio_residual_density=str(Fraction(len(residual),2**depth)),
        baseline_closed=len(baseline),portfolio_closed=len(admitted),additional_closed=len(gain),
        evaluation_unresolved=len(unresolved),scalar_exceptions=len(exceptions),
        unknown_scalar_exceptions=len(unknown_exceptions),qualification_replay_steps=replay_steps,
        verdict='PASS_EXACT_LOWER_MERGE_PORTFOLIO_WITH_RESIDUAL',
        scope='same-depth constructor comparison; no universal termination or performance claim')
    output.mkdir(parents=True,exist_ok=True)
    for name,obj in [('summary',summary),('bank',bank),('residual',residual),
                     ('exception_proofs',exception_proofs),('newly_closed',gain),
                     ('evaluation_unresolved',unresolved)]:
        (output/(name+'.json')).write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n')
    restored=json.loads((output/'bank.json').read_text())
    verify_partition(restored,residual)
    base.require(applications(restored,low,high)==admitted,'restart changed consequences')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--depth',type=int,default=18)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.depth,a.output)
