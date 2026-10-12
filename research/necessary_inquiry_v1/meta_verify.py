#!/usr/bin/env python3
"""Construct a missing observation rule from source evidence, then transfer it.
Supplied meta-language: point queries, XOR, affine-basis tests and GF(2) frame transport.
Neither a four-point difference nor a quadratic program is given to the inducer.
This is bounded rule induction, NOT autonomous invention of its primitive language.
"""
from itertools import combinations
from random import Random
import json
import verify as v

def induce(get,n=3):
    old=[lambda x:1]+[lambda x,i=i:(x>>i)&1 for i in range(n)]
    attempts=0
    for count in range(1,5):
        for group in combinations(range(1<<n),count):
            attempts+=1
            if any(sum(f(x) for x in group)%2 for f in old):continue
            if sum(get(x) for x in group)%2:
                assert len(group)==4
                a,b,c,d=group
                assert a^b^c==d
                return {'frame':(0,a^b,a^c,(a^b)^(a^c)),
                        'weights':(1,1,1,1),
                        'source_witness':group,'programs_examined':attempts}
    return None

def transported_signal(rule,o,a,b):
    p,q,r,s=rule['frame']
    assert p==0 and q and r and q!=r and s==(q^r)
    assert a and b and (a&b)==0
    assert len(rule['weights'])==4 and sum(rule['weights'])%2==0
    # Every probe is obtained by transporting the learned frame.
    mapping={p:0,q:a,r:b,s:a^b}
    assert len(mapping)==4
    return sum(w*o.get(mapping[x]) for w,x in zip(rule['weights'],rule['frame']))%2

def developed_solver(n,o,design,rule):
    masks,columns=design
    signal=sum(transported_signal(rule,o,a,b)<<k for k,(a,b) in enumerate(masks))
    idx_by_sig={s:i for i,s in enumerate(columns)}
    if signal==0:support=()
    elif signal in idx_by_sig:support=(idx_by_sig[signal],)
    else:
        support=None
        for i,x in enumerate(columns):
            j=idx_by_sig.get(signal^x)
            if j is not None and i<j:
                support=(i,j);break
    if support is None:return None
    c=o.get(0)
    a=sum((o.get(1<<i)^c)<<i for i in range(n))
    return c,a,tuple(v.edges(n)[i] for i in support)

def main():
    source=v.Oracle(3,1,0b101,((0,1),))
    rule=induce(source.get)
    assert rule and rule['source_witness']==(0,1,2,3)
    assert len(source.cache)==4
    # A corrupted rule cannot pass its own source-frame qualification.
    forged=dict(rule);forged['frame']=(0,1,2,7)
    try:transported_signal(forged,source,1,2)
    except AssertionError:pass
    else:raise AssertionError('forged rule accepted')
    broken=dict(rule);broken['weights']=(0,1,1,1)
    try:transported_signal(broken,source,1,2)
    except AssertionError:pass
    else:raise AssertionError('parity mutant accepted')
    summary=[]
    for n in (8,16,32,64):
        D=v.design(n)
        count=old_count=0
        queries=0
        for k in (0,1,2):
            for j in range(2 if n==8 else 6):
                seed=(100000 if n==8 else 700000)+n*1000+k*100+j
                _,c,a,ee=v.task(n,k,seed)
                o=v.Oracle(n,c,a,ee)
                learned=developed_solver(n,o,D,rule)
                assert learned==(c,a,ee)
                # Read source through a second independent meaning interpreter.
                rng=Random(seed+5151)
                xs=range(1<<n) if n==8 else (rng.getrandbits(n) for _ in range(512))
                assert all(v.truth(x,n,*learned)==v.truth(x,n,c,a,ee) for x in xs)
                queries+=len(o.cache);count+=1;old_count+=k==0
        expected={8:82,16:113,32:153,64:233}[n]
        assert queries==count*expected
        # Three-edge out-of-grammar controls fail closed.
        out=v.Oracle(n,1,0,((0,1),(0,2),(1,2)))
        assert developed_solver(n,out,D,rule) is None
        summary.append({'n':n,'cases':count,'solved':count,
                        'old_affine_solved':old_count,'queries_per_task':expected})
    assert sum(r['solved'] for r in summary if r['n']>8)==54
    assert sum(r['old_affine_solved'] for r in summary if r['n']>8)==18
    print(json.dumps({'status':'PASS_BOUNDED_SOURCE_INDUCED_RULE',
                      'source_rule':rule,'source_queries':len(source.cache),
                      'protected_54_of_54':True,
                      'summary':summary,
                      'stateless_equal_information_baseline':'TIES_BY_CONSTRUCTION',
                      'scope':'query/XOR and GF2 transport primitives supplied'},indent=2))

if __name__=='__main__':main()
