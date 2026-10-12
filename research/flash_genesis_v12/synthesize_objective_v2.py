#!/usr/bin/env python3
"""V12 source-only objective-grammar refiner, optionally using V11 topology.
The SOURCE tasks from V11 are no longer claimed heldout in V12.
This file does not import V12 protected_weighted. Only finite typed candidates.
"""
from __future__ import annotations
import hashlib,json,random
from pathlib import Path
from source_weighted import families
ROOT=Path(__file__).resolve().parent

class Query:
    def __init__(self, table):self.t=table;self.calls=0
    def __call__(self,m):self.calls+=1;return self.t[m]

def all_scores(f,n):
    return tuple(f.score(m) for m in range(1<<n))

def max_truth(feasible,score,mask):
    sub=mask;best=float('-inf')
    while True:
        if feasible[sub]:best=max(best,score[sub])
        if sub==0:break
        sub=(sub-1)&mask
    return best

def candidates(warm):
    topology=['both'] if warm else ['greedy','rotate_greedy','only_include','both']
    out=[]
    for t in topology:
        for obj in ('count','sum_weights','callback','max_singleton'):
            for bound in ('none','count','positive_weights'):
                for inc_first in (True,False):
                    if t!='both' and inc_first is False:continue
                    out.append({'topology':t,'objective':obj,'bound':bound,'include_first':inc_first})
    # Deterministic syntactic order, identical for warm and cold subsequences.
    return sorted(out,key=lambda p:(len(str(p['topology'])),p['objective'],p['bound'],int(p['include_first'])))

def mode_score(mask,policy,weights,score):
    obj=policy['objective']
    if obj=='count':return mask.bit_count()
    if obj=='sum_weights':return sum(w for i,w in enumerate(weights) if mask>>i&1)
    if obj=='max_singleton':return max([weights[i] for i in range(len(weights)) if mask>>i&1],default=0)
    return score(mask)

def run(p,order,weights,feasible,score):
    def objective(mask):return mode_score(mask,p,weights,score)
    n=len(order)
    if p['topology'] in ('greedy','rotate_greedy'):
        arrs=[order] if p['topology']=='greedy' else [order[k:]+order[:k] for k in range(n)]
        best=0
        for arr in arrs:
            mask=0
            for i in arr:
                if feasible(mask|(1<<i)):mask|=1<<i
            best=max(best,objective(mask))
        return best
    if p['topology']=='only_include':
        mask=sum(1<<i for i in order)
        return objective(mask) if feasible(mask) else 0
    best=0
    def branch(i,chosen):
        nonlocal best
        if p['bound']!='none':
            if p['bound']=='count':ub=chosen.bit_count()+n-i
            else:ub=objective(chosen)+sum(max(weights[j],0) for j in order[i:])
            if ub<=best:return
        if i==n:
            if feasible(chosen):best=max(best,objective(chosen))
            return
        bit=1<<order[i]
        states=(chosen|bit,chosen) if p['include_first'] else (chosen,chosen|bit)
        for state in states:branch(i+1,state)
    branch(0,0)
    return best

def source_examples(mask,n):
    elems=tuple(i for i in range(n) if mask>>i&1)
    if len(elems)<=4:
        # Two reverse directions plus special first-element ordering; not full
        # factorial because complete independent exact heldout remains separate.
        return [elems,tuple(reversed(elems))]
    rng=random.Random(20261012+31*mask)
    shuffled=list(elems);rng.shuffle(shuffled)
    return [elems,tuple(reversed(elems)),tuple(shuffled)]

def test_source(policy,fs,stats):
    for f,n,indep,score,truth in fs:
        for allowed in range(1<<n):
            for order in source_examples(allowed,n):
                q=Query(indep)
                s=Query(score)
                prediction=run(policy,order,f.weights,q,s)
                stats['cases']+=1
                stats['feasibility_calls']+=q.calls
                stats['score_callback_calls']+=s.calls
                if prediction!=truth[allowed]:
                    return False,{'source':f.name,'allowed':allowed,'order':order,
                                  'predicted':prediction,'true':truth[allowed]}
    return True,None

def emit(policy):
    """Emit a faithful interpreter of ANY selected finite typed policy.

    No target policy is privileged. Every constructor in the source
    meta-grammar is represented; the frozen policy determines actual behavior.
    """
    return """# Source-compiled by V12 unbiased source-only selector (v2).
POLICY = """+repr(policy)+"""

def developed_optimize(n, independent, weights, order=None, score_fn=None):
    if order is None:order=tuple(range(n))
    order=tuple(order)
    def value(mask):
        m=POLICY['objective']
        if m=='count':return mask.bit_count()
        if m=='sum_weights':return sum(weights[i] for i in range(n) if mask>>i&1)
        if m=='max_singleton':return max([weights[i] for i in range(n) if mask>>i&1],default=0)
        if score_fn is None:raise ValueError('callback score required')
        return score_fn(mask)
    typ=POLICY['topology']
    if typ in ('greedy','rotate_greedy'):
        rotations=[order] if typ=='greedy' else [order[k:]+order[:k] for k in range(len(order))]
        best=0
        for arrangement in rotations:
            chosen=0
            for element in arrangement:
                nextmask=chosen|(1<<element)
                if independent(nextmask):chosen=nextmask
            best=max(best,value(chosen))
        return best
    if typ=='only_include':
        chosen=sum(1<<e for e in order)
        return value(chosen) if independent(chosen) else 0
    if typ!='both':raise ValueError('unsupported policy topology')
    best=0
    def branch(i,chosen):
        nonlocal best
        if POLICY['bound']!='none':
            if POLICY['bound']=='count':ub=chosen.bit_count()+len(order)-i
            elif POLICY['bound']=='positive_weights':
                ub=value(chosen)+sum(max(0,weights[e]) for e in order[i:])
            else:raise ValueError('unknown bound')
            if ub<=best:return
        if i==len(order):
            if independent(chosen):best=max(best,value(chosen))
            return
        bit=1<<order[i]
        states=(chosen|bit,chosen) if POLICY['include_first'] else (chosen,chosen|bit)
        for m in states:branch(i+1,m)
    branch(0,0)
    return best
"""

def main():
    fs=[];source_truth_calls=0
    for f in families():
        n=f.n
        indep=tuple(bool(f.feasible(m)) for m in range(1<<n))
        score=all_scores(f,n)
        source_truth_calls+=2*(1<<n)
        assert indep[0] and score[0]==0 and all(x>=0 for x in f.weights)
        assert all(score[m]==sum(f.weights[i] for i in range(n) if m>>i&1) for m in range(1<<n))
        truths=tuple(max_truth(indep,score,mask) for mask in range(1<<n))
        fs.append((f,n,indep,score,truths))
    trials={}
    for warm in (True,False):
        table=[];passing=[]
        for pol in candidates(warm):
            stat={'cases':0,'feasibility_calls':0,'score_callback_calls':0}
            ok,failed=test_source(pol,fs,stat)
            item={'policy':pol,'pass':ok,'stats':stat,'first_failure':failed}
            table.append(item)
            if ok:
                passing.append(item)
        assert passing,(warm,'no qualified score-aware repair within frozen grammar')
        # Equal-information policy selection; prefer source calls first, then form.
        selected=min(passing,key=lambda q:(q['stats']['feasibility_calls']+q['stats']['score_callback_calls'],q['stats']['score_callback_calls'],str(q['policy'])))
        trials['warm' if warm else 'cold']={'candidate_count':len(table),'tested_candidates':table,
            'total_cases':sum(x['stats']['cases'] for x in table),
            'total_feasibility_calls':sum(x['stats']['feasibility_calls'] for x in table),
            'total_score_callback_calls':sum(x['stats']['score_callback_calls'] for x in table),
            'selected':selected}
    selected=trials['warm']['selected']['policy']
    # Correctness of emission is checked by running independently after freeze.
    assert any(item['policy']==selected for item in trials['warm']['tested_candidates'] if item['pass'])
    py=emit(selected)
    (ROOT/'learned_objective.py').write_text(py)
    import ast
    ast.parse(py)
    scope={}
    exec(compile(py,'<generated_v12_unbiased>','exec'),scope)
    for f,n,indep,score,truth in fs:
        for allowed in range(1<<n):
            order=tuple(i for i in range(n) if allowed>>i&1)
            got=scope['developed_optimize'](n,lambda m,t=indep:t[m],f.weights,order,lambda m,t=score:t[m])
            assert got==truth[allowed],(f.name,allowed,got,truth[allowed])
    rec={'status':'SOURCE_OBJECTIVE_REPAIR_FROZEN','v11_parent':'5b10a853240356b2b00258334ef378e0850eb42c',
         'parent_compiled_source_sha256':'1200898dfafa0c431c49f4eeab23f500e8dca92d0fdebfa72d6aca2ec9861506',
         'source_names':[f.name for f,_,_,_,_ in fs],
         'source_truth_table_calls':source_truth_calls,
         'cold':trials['cold'],'warm':trials['warm'],'selected':selected,
         'learned_source_sha256':hashlib.sha256(py.encode()).hexdigest(),
         'selector_version':'unbiased_v2_all_source_qualifying_candidates','v12a_retrospective_due_selector_filter':True,'limitations':'typed objective and additive bound grammar supplied; warm has structurally selected V11 topology; source weighted families had been opened in V11; no independent invention of new meta-grammar'}
    (ROOT/'source_receipt.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')
    (ROOT/'qualified_policy.json').write_text(json.dumps(selected,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':rec['status'],'warm':{k:v for k,v in rec['warm'].items() if k!='tested_candidates'},
        'cold':{k:v for k,v in rec['cold'].items() if k!='tested_candidates'},'selected':selected,'learned_source_sha256':rec['learned_source_sha256']},indent=2))

if __name__=='__main__':main()
