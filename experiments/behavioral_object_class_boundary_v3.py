#!/usr/bin/env python3
"""Behavioral Object Equivalence Class Boundary V3.

Parent: V2 run 32808248132 established that five literal target-relative
relations induce identical actions on 216 affine-family tasks.

This test asks whether that class is regime-relative. It moves to a frozen,
generic finite hypothesis-table regime with nonuniform query-outcome masses,
where the five measures are not assumed to be monotone transforms of one
another. The generator is fixed before results and searches only for valid
decision tasks, not for a preferred winner.

Success for the boundary hypothesis: find a nontrivial panel on which at least
two of the five formerly equivalent relations choose different actions, while
the exact expected-target-entropy criterion remains the declared verifier.
Failure: no split after the frozen exhaustive/random search budget.
"""
import json, math, random
from collections import Counter, defaultdict
from pathlib import Path

SEED=2026082518
RNG=random.Random(SEED)
OUT=Path('artifacts/behavioral_object_class_boundary_v3'); OUT.mkdir(parents=True,exist_ok=True)
TIED=(
 'true_target_entropy','unweighted_target_ambiguity','weighted_target_setsize',
 'negative_singleton_mass','max_target_setsize'
)
N_WORLDS=12
N_QUERIES=4
TARGET_VALUES=3
QUERY_VALUES=3
SEARCH_BUDGET=200000
PANEL_TARGET=64

def entropy(vals):
    c=Counter(vals); n=len(vals)
    return -sum((v/n)*math.log2(v/n) for v in c.values()) if n else 0.0

def features(task,q):
    target=task['target']; out=task['queries'][q]; n=len(target)
    by=defaultdict(list)
    for i,o in enumerate(out): by[o].append(i)
    targetsets={o:{target[i] for i in idxs} for o,idxs in by.items()}
    sizes=[len(s) for s in targetsets.values()]
    counts={o:len(idxs) for o,idxs in by.items()}
    exp_ent=sum(counts[o]/n*entropy([target[i] for i in by[o]]) for o in by)
    weighted_setsize=sum(counts[o]/n*len(targetsets[o]) for o in by)
    singleton_mass=sum(counts[o] for o in by if len(targetsets[o])==1)/n
    return {
      'true_target_entropy':exp_ent,
      'unweighted_target_ambiguity':sum(math.log2(max(1,s)) for s in sizes)/len(sizes),
      'weighted_target_setsize':weighted_setsize,
      'negative_singleton_mass':-singleton_mass,
      'max_target_setsize':max(sizes),
    }

def choose(task,obj):
    vals=[features(task,q)[obj] for q in range(N_QUERIES)]
    b=min(vals)
    return min(i for i,v in enumerate(vals) if abs(v-b)<1e-12)

def random_task(idx):
    # Ensure each target value occurs and each query has >=2 outcomes.
    while True:
        target=[RNG.randrange(TARGET_VALUES) for _ in range(N_WORLDS)]
        if len(set(target))<TARGET_VALUES: continue
        queries=[]
        for _ in range(N_QUERIES):
            a=[RNG.randrange(QUERY_VALUES) for _ in range(N_WORLDS)]
            if len(set(a))<2: break
            queries.append(a)
        if len(queries)!=N_QUERIES: continue
        t={'id':f'generic_{idx:04d}','target':target,'queries':queries}
        true=[features(t,q)['true_target_entropy'] for q in range(N_QUERIES)]
        # Require a unique exact optimum and meaningful spread.
        order=sorted(range(N_QUERIES),key=lambda q:(true[q],q))
        if abs(true[order[1]]-true[order[0]])<0.05: continue
        t['optimal']=order[0]
        return t

panel=[]; attempts=0; first_split=None
while attempts<SEARCH_BUDGET and len(panel)<PANEL_TARGET:
    attempts+=1
    t=random_task(attempts)
    actions={g:choose(t,g) for g in TIED}
    if len(set(actions.values()))>1:
        panel.append(t)
        if first_split is None:
            first_split={'task':t,'actions':actions,'features':{g:[features(t,q)[g] for q in range(N_QUERIES)] for g in TIED}}

summary={
 'schema':'behavioral.object.class.boundary.v3',
 'parent_run':32808248132,
 'seed':SEED,
 'search_budget':SEARCH_BUDGET,
 'attempts':attempts,
 'panel_target':PANEL_TARGET,
 'split_tasks_found':len(panel),
 'class_members':TIED,
 'first_split':first_split,
}
if panel:
    disagreements={}
    accuracies={g:0 for g in TIED}
    for t in panel:
        acts={g:choose(t,g) for g in TIED}
        for g,a in acts.items(): accuracies[g]+=int(a==t['optimal'])
        for i,a in enumerate(TIED):
            for b in TIED[i+1:]:
                k=f'{a}__{b}'; disagreements[k]=disagreements.get(k,0)+int(acts[a]!=acts[b])
    summary['panel_n']=len(panel)
    summary['accuracies_vs_exact_entropy']=accuracies
    summary['pairwise_disagreements']=disagreements
    summary['all_five_still_equivalent']=all(v==0 for v in disagreements.values())
else:
    summary['panel_n']=0
    summary['accuracies_vs_exact_entropy']={}
    summary['pairwise_disagreements']={}
    summary['all_five_still_equivalent']=True

(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))

# Frozen separator: the old five-member class must split in the new regime.
assert len(panel)>=16, ('NO_ROBUST_SPLIT_PANEL',len(panel),attempts)
assert not summary['all_five_still_equivalent']
# Exact expected target entropy is the declared verifier and must be perfect by construction.
assert summary['accuracies_vs_exact_entropy']['true_target_entropy']==len(panel)
# Require at least one formerly tied surrogate to disagree with exact entropy on >=25% of split panel.
assert any(summary['pairwise_disagreements'].get('true_target_entropy__'+g, summary['pairwise_disagreements'].get(g+'__true_target_entropy',0)) >= len(panel)//4 for g in TIED[1:])
print('PASS_BEHAVIORAL_OBJECT_CLASS_BOUNDARY_V3')
