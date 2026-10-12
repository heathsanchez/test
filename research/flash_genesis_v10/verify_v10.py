#!/usr/bin/env python3
"""Independent compact qualification of V10, relative to frozen protected_oracles.py.

This reproducer intentionally does not claim byte identity with the full local
source-only synthesizer. It derives a typed policy on source families, saves
and reloads it, and checks the protected oracle family with an independent
complete-subset reference. Python 3.11; no third-party dependencies.
"""
import itertools
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

def elements(mask,n):
    return [i for i in range(n) if (mask>>i)&1]

def bitrank(values):
    piv={}
    for v in values:
        while v:
            p=v.bit_length()-1
            if p in piv:v^=piv[p]
            else:piv[p]=v;break
    return len(piv)

def source_systems():
    labels=(0,0,1,2,1,3)
    vecs=(1,2,3,4,5,6)
    return [
      (6,lambda m:len({labels[i] for i in elements(m,6)})==m.bit_count()),
      (6,lambda m:bitrank([vecs[i] for i in elements(m,6)])==m.bit_count()),
    ]

def complete_ranks(n,ind):
    return [
      max(k.bit_count() for k in range(1<<n) if k&~s==0 and ind[k])
      for s in range(1<<n)
    ]

def options():
    arr=[{'term':t,'op':op,'negate':neg}
         for t in ('empty','chosen','singleton','join')
         for op in ('independent','nonempty','cardinality_at_most_1')
         for neg in (False,True)]
    arr += [{'term':'empty','op':'constant_true','negate':False},
            {'term':'empty','op':'constant_false','negate':False}]
    def complexity(p):
        if p['op'].startswith('constant'):return 1
        return 3+2*(p['term']=='join')+int(p['negate'])
    return sorted(arr,key=lambda p:(complexity(p),json.dumps(p,sort_keys=True)))

def check(p,acc,i,ind):
    t=p['term']
    x={'empty':0,'chosen':acc,'singleton':1<<i,'join':acc|(1<<i)}[t]
    op=p['op']
    if op=='independent':v=ind(x)
    elif op=='nonempty':v=x!=0
    elif op=='cardinality_at_most_1':v=x.bit_count()<=1
    elif op=='constant_true':v=True
    else:v=False
    return not v if p['negate'] else bool(v)

def program(p,order,ind):
    acc=0
    for i in order:
        if check(p,acc,i,ind):acc|=1<<i
    return acc.bit_count()

def source_synthesis():
    prepared=[]
    truth_calls=0
    checks=0
    for n,oracle in source_systems():
        ind=[oracle(i) for i in range(1<<n)]
        truth_calls+=1<<n
        rank=complete_ranks(n,ind)
        assert any(mask.bit_count()!=rank[mask] for mask in range(1<<n))
        prepared.append((n,ind,rank))
    passing=[]
    for p in options():
        good=True
        for n,tab,rank in prepared:
            for mask in range(1<<n):
                for order in itertools.permutations(elements(mask,n)):
                    checks+=1
                    if program(p,order,lambda m:tab[m])!=rank[mask]:
                        good=False;break
                if not good:break
            if not good:break
        if good:passing.append(p)
    assert len(passing)==1,passing
    # Correct expression is a measured result, not a preferred source candidate.
    chosen=passing[0]
    assert chosen=={'term':'join','op':'independent','negate':False}
    policy_file=HERE/'v10_induced_policy.json'
    policy_file.write_text(json.dumps(chosen,sort_keys=True)+'\n')
    reloaded=json.loads(policy_file.read_text())
    assert chosen==reloaded
    return reloaded,dict(source_truth_calls=truth_calls,
                         source_policy_comparisons=checks,
                         candidates_evaluated=len(options()))

def matroid_certificate(n,tab):
    assert tab[0], 'empty-set axiom failed'
    for a in range(1<<n):
        if not tab[a]:continue
        for i in elements(a,n):
            if not tab[a^(1<<i)]:
                return {'axiom':'hereditary','larger':a,'smaller':a^(1<<i)}
    independent=[i for i in range(1<<n) if tab[i]]
    for a in independent:
        for b in independent:
            if a.bit_count()>=b.bit_count():continue
            if not any(tab[a|(1<<i)] for i in elements(b&~a,n)):
                return {'axiom':'exchange','A':a,'B':b}
    return None

def strong_greedy(order,ind):
    acc=0
    for i in order:
        proposed=acc|(1<<i)
        if ind(proposed):acc=proposed
    return acc.bit_count()

def protected_test(policy):
    # Import AFTER source-only policy selection and serialization.
    from protected_oracles import systems
    rows=[]
    for system in systems():
        n=system.n
        independent=[bool(system.independent(mask)) for mask in range(1<<n)]
        witness=matroid_certificate(n,independent)
        if witness:
            assert system.name=='negative_nonmatroid_knapsack'
            expected=complete_ranks(n,independent)[(1<<n)-1]
            counter=next((order,strong_greedy(order,lambda m:independent[m]))
                 for order in itertools.permutations(range(n))
                 if strong_greedy(order,lambda m:independent[m])!=expected)
            rows.append(dict(name=system.name,status='REJECTED_APPLICABILITY',
                             witness=witness,greedy_counterexample=[list(counter[0]),counter[1],expected]))
            continue
        ranks=complete_ranks(n,independent)
        rng=random.Random(20261012+sum(map(ord,system.name)))
        trials=0
        count_old_fails=0
        mutation_fails=0
        calls_learned=0
        calls_strong=0
        for mask in range(1<<n):
            if mask.bit_count()!=ranks[mask]:count_old_fails+=1
            if sum(independent[1<<i] for i in elements(mask,n))!=ranks[mask]:mutation_fails+=1
            elems=elements(mask,n)
            if len(elems)<=6:orders=list(itertools.permutations(elems))
            else:
                orders=[tuple(elems),tuple(reversed(elems))]
                for _ in range(72):
                    e=elems[:];rng.shuffle(e);orders.append(tuple(e))
            for order in orders:
                def oracle1(m):
                    nonlocal calls_learned
                    calls_learned+=1
                    return independent[m]
                def oracle2(m):
                    nonlocal calls_strong
                    calls_strong+=1
                    return independent[m]
                developed=program(policy,order,oracle1)
                known=strong_greedy(order,oracle2)
                assert developed==known==ranks[mask],(system.name,mask,order,developed,known)
                trials+=1
        assert count_old_fails>0 and mutation_fails>0
        assert calls_learned==calls_strong
        rows.append(dict(name=system.name,status='PASS_CERTIFIED_MATROID_TRANSFER',
                         n=n,whole_rank=ranks[-1],subsets=1<<n,
                         orders_tested=trials,old_count_failures=count_old_fails,
                         mutation_failures=mutation_fails,
                         learned_oracle_lookups=calls_learned,
                         strong_stateless_oracle_lookups=calls_strong))
    assert len([r for r in rows if r['status']=='PASS_CERTIFIED_MATROID_TRANSFER'])==6
    assert len([r for r in rows if r['status']=='REJECTED_APPLICABILITY'])==1
    return rows

def main():
    learned,source=source_synthesis()
    protected=protected_test(learned)
    receipt=dict(status='PASS_INDEPENDENT_FINITE_REPLAY',
                 source=source,policy=learned,protected=protected,
                 verdict='Six qualified source-distinct matroids transfer; one nonmatroid fails closed; strong stateless greedy ties. Source supplied independence oracle and finite program grammar.')
    (HERE/'v10_ci_receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps(receipt,sort_keys=True))
if __name__=='__main__':main()
