#!/usr/bin/env python3
"""V11 held-out verifier. Source policy frozen in GitHub before this module was run.

Independent exhaustive reference, exact hereditary/exchange applicability guards,
plus equal-information stateless exact branch-bound control and ablations.
"""
import hashlib, importlib.util, json, random
from pathlib import Path
from itertools import permutations
from protected_oracles import protected_families, frozen_changed_objectives
ROOT=Path(__file__).resolve().parent
EXPECTED='1200898dfafa0c431c49f4eeab23f500e8dca92d0fdebfa72d6aca2ec9861506'
assert hashlib.sha256((ROOT/'learned_repair.py').read_bytes()).hexdigest()==EXPECTED
spec=importlib.util.spec_from_file_location('qualified_frozen_source',ROOT/'learned_repair.py')
L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
assert L.POLICY=={'bound': True, 'include_first': True, 'mode':'both_branches','prune':False}

class Count:
    def __init__(self, table):self.table=table;self.calls=0
    def __call__(self,mask):self.calls+=1;return self.table[mask]

def guard(table,n):
    if not table[0]:return 'UNKNOWN_NONHEREDITARY',{'empty_set':False},0
    for m in range(1<<n):
        if table[m]:
            for i in range(n):
                if (m>>i&1) and not table[m^(1<<i)]:
                    return 'UNKNOWN_NONHEREDITARY',{'hereditary_witness':[m,m^(1<<i)]},0
    independent=[m for m in range(1<<n) if table[m]]
    trials=0
    for a in independent:
        for b in independent:
            if a.bit_count()>=b.bit_count():continue
            trials+=1
            if not any(table[a|(1<<i)] for i in range(n) if (b>>i&1) and not (a>>i&1)):
                return 'HEREDITARY_NONMATROID',{'exchange_witness':[a,b]},trials
    return 'MATROID',{},trials

def reference(table,allowed):
    best=0;m=allowed;checks=0
    while True:
        checks+=1
        if table[m]:best=max(best,m.bit_count())
        if not m:break
        m=(m-1)&allowed
    return best,checks

def source_matroid_greedy(oracle,order):
    chosen=0
    for i in order:
        test=chosen|(1<<i)
        if oracle(test):chosen=test
    return chosen.bit_count()

def strong_stateless_branch_and_bound(order,oracle):
    best=0;stack=[(0,0)]
    while stack:
        mask,i=stack.pop()
        if mask.bit_count()+len(order)-i<=best:continue
        if i==len(order):
            if oracle(mask):best=max(best,mask.bit_count())
            continue
        # Stack is LIFO; include path is visited first, matching frozen V11.
        stack.append((mask,i+1));stack.append((mask|(1<<order[i]),i+1))
    return best

def chosen_orders(mask,n):
    elems=tuple(i for i in range(n) if mask>>i&1)
    if len(elems)<=4:return tuple(permutations(elems))
    rng=random.Random(12701+31*mask)
    ans=[elems,tuple(reversed(elems))]
    for _ in range(4):
        e=list(elems);rng.shuffle(e);ans.append(tuple(e))
    return ans

def check_family(fam):
    n=fam.n
    table=tuple(bool(fam.independent(m)) for m in range(1<<n))
    typ,negative,exchange_trials=guard(table,n)
    if fam.category=='matroid':assert typ=='MATROID',(fam.name,typ,negative)
    elif fam.category=='hereditary_nonmatroid':assert typ=='HEREDITARY_NONMATROID',(fam.name,typ,negative)
    else:assert typ=='UNKNOWN_NONHEREDITARY',(fam.name,typ,negative)
    result={'name':fam.name,'ground_size':n,'kind':typ,'guard_oracle_calls':1<<n,
            'guard_exchange_pairs_examined':exchange_trials,'negative_certificate':negative}
    if typ=='UNKNOWN_NONHEREDITARY':
        result['status']='UNKNOWN_UNSUPPORTED_CONTRACT'
        result['generated_policy_invoked']=False
        return result
    reference_checks=0;generated_calls=0;strong_calls=0;greedy_calls=0
    source_cases=0;greedy_failures=[];synth_vs_stateless=[]
    for mask in range(1<<n):
        expected,checks=reference(table,mask)
        reference_checks+=checks
        for order in chosen_orders(mask,n):
            source_cases+=1
            q=Count(table)
            greedy=source_matroid_greedy(q,order);greedy_calls+=q.calls
            if greedy!=expected and len(greedy_failures)<3:
                greedy_failures.append({'subset':mask,'order':list(order),'greedy':greedy,'optimal':expected})
            if typ=='HEREDITARY_NONMATROID':
                q=Count(table)
                got=L.learned_exact_rank(n,q,order)
                generated_calls+=q.calls
                q=Count(table)
                strong=strong_stateless_branch_and_bound(order,q)
                strong_calls+=q.calls
                if got!=strong:synth_vs_stateless.append((mask,order,got,strong))
                assert got==strong==expected,(fam.name,mask,order,got,strong,expected)
            else:
                # Reusing the previous matroid capability is strictly sufficient.
                assert greedy==expected,(fam.name,mask,order,greedy,expected)
    assert not synth_vs_stateless
    if typ=='HEREDITARY_NONMATROID':
        assert greedy_failures,(fam.name,'no ablation witness')
        assert generated_calls==strong_calls,(fam.name,'same-program-cost mismatch',generated_calls,strong_calls)
    result.update(status='PASS_HELDOUT_EXACT',
        evaluation_cases=source_cases,reference_subset_lookups=reference_checks,
        learned_execution_calls=generated_calls,matched_stateless_execution_calls=strong_calls,
        prior_greedy_calls=greedy_calls,prior_greedy_failure_witnesses=greedy_failures,
        learned_equal_strong=True)
    return result

def future_objective_control():
    result=[]
    for name,n,indep,weights in frozen_changed_objectives():
        assert len(weights)==n and all(w>=0 for w in weights)
        table=[bool(indep(m)) for m in range(1<<n)]
        k,w=0,-1;winner=0
        for m in range(1<<n):
            if not table[m]:continue
            score=sum(weights[i] for i in range(n) if m>>i&1)
            if score>w:w=score;winner=m
            k=max(k,m.bit_count())
        assert w>=0
        # V11 emits rank only: no certificate of weighted witness or score.
        result.append({'name':name,'protected_weighted_optimum':w,
                       'witness':winner,'ordinary_rank':k,
                       'old_generator_objective_supported':False,
                       'status':'UNKNOWN_OBJECTIVE_LANGUAGE_NOT_SUPPORTED'})
    return result

def main():
    rs=[check_family(s) for s in protected_families()]
    resolved=[x for x in rs if x['status']=='PASS_HELDOUT_EXACT']
    rejected=[x for x in rs if x['status']=='UNKNOWN_UNSUPPORTED_CONTRACT']
    assert len(resolved)==7 and len(rejected)==2
    assert sum(x['kind']=='HEREDITARY_NONMATROID' for x in resolved)==5
    assert sum(x['kind']=='MATROID' for x in resolved)==2
    assert all(x['learned_equal_strong'] for x in resolved)
    frozen_source_sha=hashlib.sha256((ROOT/'learned_repair.py').read_bytes()).hexdigest()
    future=future_objective_control()
    out={'status':'PASS_EXACT_FINITE_PROTECTED_TRANSFER',
         'qualified_source_sha256':frozen_source_sha,
         'source_synthesis_calls':json.loads((ROOT/'source_receipt.json').read_text())['source_total_candidate_calls'],
         'source_selected_policy':L.POLICY,'protected_families':rs,
         'third_generation_changed_objective':future,
         'total':{'protected_valid':len(resolved),'protected_invalid':len(rejected),
          'protected_case_comparisons':sum(x['evaluation_cases'] for x in resolved),
          'protected_guard_calls':sum(x['guard_oracle_calls'] for x in rs),
          'protected_generated_calls':sum(x['learned_execution_calls'] for x in resolved),
          'protected_matched_stateless_calls':sum(x['matched_stateless_execution_calls'] for x in resolved),
          'protected_reference_lookups':sum(x['reference_subset_lookups'] for x in resolved)},
         'verdict':{'warranted':'Source-synthesized complete fallback transfers unchanged to hereditary nonmatroids with guards; old greedy ablation fails; strong stateless ties.',
          'rejected':'Any strict advantage over equally informed stateless branch-and-bound.',
          'unknown':'Third-generation weighted objective requires new schema; no recursive generator improvement; costs not advantageous; all semantics designer-supplied.'}}
    (ROOT/'results.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'total':out['total'],
      'families':[(r['name'],r['kind'],r['status'],r.get('evaluation_cases'),bool(r.get('prior_greedy_failure_witnesses'))) for r in rs],
      'future':future},indent=2))

if __name__=='__main__':main()
