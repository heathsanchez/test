#!/usr/bin/env python3
"""V11 finite typed-program synthesis. Reads ONLY source_oracles, never protected.

Derives admissibility by complete finite oracle checks, exhausts source evidence,
and emits a new Python program chosen from the given, finite recursion grammar.
It does not invent recursion or a matroid theorem: these are supplied primitives.
"""
from __future__ import annotations
import hashlib, json, sys
from itertools import permutations
from pathlib import Path
from source_oracles import source_families
ROOT=Path(__file__).resolve().parent

class Query:
    def __init__(self,table):self.table=table;self.calls=0
    def __call__(self,mask):self.calls+=1;return self.table[mask]


def rank_truth(table,n,allowed):
    sub=allowed;best=0
    while True:
        if table[sub]: best=max(best,sub.bit_count())
        if sub==0:break
        sub=(sub-1)&allowed
    return best


def validate_kind(table,n):
    if not table[0]: return 'UNKNOWN_NONHEREDITARY',{'empty_set':False}
    for mask in range(1<<n):
        if table[mask]:
            for i in range(n):
                if (mask>>i&1) and not table[mask^(1<<i)]:
                    return 'UNKNOWN_NONHEREDITARY',{'failed_heredity':[mask,mask^(1<<i)]}
    independent=[m for m in range(1<<n) if table[m]]
    for a in independent:
        for b in independent:
            if a.bit_count()>=b.bit_count():continue
            if not any(table[a|(1<<i)] for i in range(n) if (b>>i&1) and not (a>>i&1)):
                return 'HEREDITARY_NONMATROID',{'exchange_counterexample':[a,b]}
    return 'MATROID',{}


def candidates():
    return [{'mode':'greedy','prune':False,'bound':False,'include_first':True},
            {'mode':'rotated_greedy','prune':False,'bound':False,'include_first':True}]+[
        {'mode':'both_branches','prune':prune,'bound':bound,'include_first':include}
        for prune in (False,True) for bound in (False,True) for include in (False,True)
    ]


def run(policy,order,oracle):
    n=len(order)
    if policy['mode'] in ('greedy','rotated_greedy'):
        rotations=(order,) if policy['mode']=='greedy' else tuple(order[k:]+order[:k] for k in range(n))
        best=0
        for arrangement in rotations:
            chosen=0
            for i in arrangement:
                next_mask=chosen|(1<<i)
                if oracle(next_mask):chosen=next_mask
            best=max(best,chosen.bit_count())
        return best
    best=0
    def branch(i,chosen):
        nonlocal best
        if policy['prune'] and not oracle(chosen): return
        if policy['bound'] and chosen.bit_count()+n-i<=best:return
        if i==n:
            if oracle(chosen):best=max(best,chosen.bit_count())
            return
        b=1<<order[i]
        nextstates=((chosen|b,chosen) if policy['include_first'] else (chosen,chosen|b))
        for nxt in nextstates: branch(i+1,nxt)
    branch(0,0)
    return best


def order_cases(mask,n):
    elems=tuple(i for i in range(n) if mask>>i&1)
    if len(elems)<=6:return list(permutations(elems))
    return [elems,tuple(reversed(elems)),elems[1:]+elems[:1]]


def complete_source_test(policy,families):
    checks=0;calls=0;first_failure=None
    for name,n,table,rank in families:
        for mask in range(1<<n):
            target=rank[mask]
            for order in order_cases(mask,n):
                oracle=Query(table)
                got=run(policy,order,oracle)
                calls+=oracle.calls;checks+=1
                if got!=target:
                    first_failure={'family':name,'mask':mask,'order':order,'got':got,'want':target}
                    return False,checks,calls,first_failure
    return True,checks,calls,None


def source_generated(policy):
    """Write a portable qualified repair procedure, no hidden family dispatch."""
    x=json.dumps(policy,sort_keys=True)
    # The selected policy is compiled into a source file; an independent process
    # imports that file after its SHA is frozen. This is a typed AST-like program
    # of recursion parameters, not unconstrained program synthesis.
    return f'''# Source-compiled by V11 source-only structural repair search.\nPOLICY = {x.replace('true','True').replace('false','False')}\n\ndef learned_exact_rank(n, independent, order=None):\n    if order is None: order=tuple(range(n))\n    order=tuple(order)\n    best=0\n    def branch(i,chosen):\n        nonlocal best\n        if POLICY["prune"] and not independent(chosen):return\n        if POLICY["bound"] and chosen.bit_count()+len(order)-i<=best:return\n        if i==len(order):\n            if independent(chosen):best=max(best,chosen.bit_count())\n            return\n        bit=1<<order[i]\n        states=(chosen|bit,chosen) if POLICY["include_first"] else (chosen,chosen|bit)\n        for state in states:branch(i+1,state)\n    branch(0,0)\n    return best\n'''


def main():
    families=[];truth_queries=0;source_guards=[];source_old_failures=[]
    for s in source_families():
        table=tuple(bool(s.independent(m)) for m in range(1<<s.n));truth_queries+=len(table)
        kind,witness=validate_kind(table,s.n)
        assert (kind=='MATROID')==(s.kind=='matroid'),(s.name,kind)
        ranks=tuple(rank_truth(table,s.n,m) for m in range(1<<s.n))
        families.append((s.name,s.n,table,ranks))
        source_guards.append({'name':s.name,'kind':kind,'witness':witness})
        witness_mask=next((m for m in range(1<<s.n) if m.bit_count()>ranks[m]),None)
        assert witness_mask is not None
        source_old_failures.append({'family':s.name,'mask':witness_mask})
    # Finite grammar synthesis with explicit source-level negative evidence.
    reports=[];passing=[]
    for policy in candidates():
        ok,cases,calls,failure=complete_source_test(policy,families)
        report={'policy':policy,'pass':ok,'source_cases':cases,'source_oracle_calls':calls,'first_failure':failure}
        reports.append(report)
        if ok and policy['mode']=='both_branches':passing.append(report)
    assert passing, 'No source-qualified two-branch repair'
    # Prefer exactness and measured SOURCE query cost, then syntactic simplicity.
    selected=min(passing,key=lambda x:(x['source_oracle_calls'],int(x['policy']['prune'])+int(x['policy']['bound']),json.dumps(x['policy'],sort_keys=True)))
    code=source_generated(selected['policy'])
    file=ROOT/'learned_repair.py';file.write_text(code)
    compile(code,str(file),'exec')
    # Preserve source policy + source candidate exhaustion and full acquisition cost.
    data={'status':'SOURCE_RULE_FROZEN','parent_v10':'cd6a5ea393dd286290d3e5f037754af767d798d5',
      'source_guard_checks':source_guards,'source_old_obstructions':source_old_failures,
      'old_matroid_greedy_witness':{'A':1,'B':6},
      'source_truth_oracle_calls':truth_queries,'source_candidates':reports,
      'selected':selected,'source_total_candidate_calls':sum(q['source_oracle_calls'] for q in reports),
      'source_total_candidate_cases':sum(q['source_cases'] for q in reports),
      'source_sha256':hashlib.sha256(code.encode()).hexdigest(),
      'boundary':'source-only finite typed branch-policy grammar; no unrestricted invention'}
    (ROOT/'source_receipt.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    (ROOT/'qualified_policy.json').write_text(json.dumps(selected['policy'],indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k!='source_candidates'},sort_keys=True))

if __name__=='__main__':main()