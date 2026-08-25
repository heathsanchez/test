#!/usr/bin/env python3
"""Behavioral-object persistence separator.

Purpose: test whether the V1 binary-residual persistence failure was specific to
verbal-rule compression. Acquisition verifier outcomes select a compact,
non-verbal comparative object from a frozen generic relation grammar. The object
is then frozen and applied with zero verifier feedback to source-distinct mod-5
held-out tasks.

This is a bounded separator of retention FORM, not a claim of autonomous grammar
invention: the candidate relation grammar is researcher-declared in advance.
"""
import json, math, random
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

SEED=2026082516
RNG=random.Random(SEED)
PREFIXES='ABCD'; SUFFIXES='XYZ'
ACQ_FAMILIES=[2,3]; HELD_FAMILIES=[5]
ACQ_PER_FAMILY=36; HELD_PER_FAMILY=48
OUT=Path('artifacts/behavioral_object_persistence_v1'); OUT.mkdir(parents=True,exist_ok=True)

def all_hypotheses(m):
    return [(dict(zip(PREFIXES,v[:4])),{'X':0,'Y':v[4],'Z':v[5]}) for v in product(range(m),repeat=6)]
def pred(h,p,m): return (h[0][p[0]]+h[1][p[1]])%m
def entropy(vals):
    if not vals: return 0.0
    c=Counter(vals); n=len(vals)
    return -sum((v/n)*math.log2(v/n) for v in c.values())
def survivors(H,obs,m): return [h for h in H if all(pred(h,p,m)==a for p,a in obs.items())]
def expected_target_entropy(H,q,t,m):
    groups=defaultdict(list)
    for h in H: groups[pred(h,q,m)].append(h)
    n=len(H)
    return sum(len(g)/n*entropy([pred(h,t,m) for h in g]) for g in groups.values())
def target_partition(H,q,t,m):
    by=defaultdict(list)
    for h in H: by[pred(h,q,m)].append(h)
    return {o:{pred(h,t,m) for h in hs} for o,hs in by.items()}
def query_entropy(H,q,m): return entropy([pred(h,q,m) for h in H])

def build_tasks(families,n_each,label):
    tasks=[]; pairs=[a+b for a in PREFIXES for b in SUFFIXES]
    for m in families:
        H0=all_hypotheses(m); made=0; attempts=0
        while made<n_each and attempts<300000:
            attempts+=1; truth=RNG.choice(H0); sh=pairs[:]; RNG.shuffle(sh)
            k=RNG.choice([4,5,6]); obs_pairs=sh[:k]; rem=[p for p in pairs if p not in obs_pairs]
            if len(rem)<5: continue
            target=rem[0]; queries=rem[1:5]; obs={p:pred(truth,p,m) for p in obs_pairs}; H=survivors(H0,obs,m)
            if len(H)<4 or len(H)>5000: continue
            scores={q:expected_target_entropy(H,q,target,m) for q in queries}
            best=min(scores.values()); worst=max(scores.values())
            if best>1e-12 or worst-best<0.25: continue
            optimal=sorted(queries,key=lambda q:(scores[q],q))[0]
            tasks.append({'id':f'{label}_m{m}_{made:03d}','m':m,'truth':truth,'obs':obs,'target':target,'queries':queries,'H':H,'true_scores':scores,'optimal':optimal}); made+=1
        assert made==n_each,(m,made)
    return tasks

# Frozen generic candidate grammar. Every object maps task/query -> scalar; lower is preferred.
# The grammar deliberately includes target-relative and non-target-relative alternatives.
def features(t,q):
    H=t['H']; m=t['m']; target=t['target']; part=target_partition(H,q,target,m)
    targetset_sizes=[len(v) for v in part.values()]
    outcome_counts=Counter(pred(h,q,m) for h in H)
    n=len(H)
    weighted_setsize=sum(outcome_counts[o]/n*len(part[o]) for o in part)
    weighted_logset=sum(outcome_counts[o]/n*math.log2(max(1,len(part[o]))) for o in part)
    singleton_mass=sum(outcome_counts[o] for o in part if len(part[o])==1)/n
    return {
        'true_target_entropy': expected_target_entropy(H,q,target,m),
        'unweighted_target_ambiguity': sum(math.log2(max(1,s)) for s in targetset_sizes)/len(targetset_sizes),
        'weighted_target_setsize': weighted_setsize,
        'negative_singleton_mass': -singleton_mass,
        'max_target_setsize': max(targetset_sizes),
        'negative_query_entropy': -query_entropy(H,q,m),
        'query_outcome_count': len(part),
        'lexical_index': t['queries'].index(q),
    }

GRAMMAR=(
 'true_target_entropy','unweighted_target_ambiguity','weighted_target_setsize',
 'negative_singleton_mass','max_target_setsize','negative_query_entropy',
 'query_outcome_count','lexical_index'
)

def choose(t,obj):
    vals={q:features(t,q)[obj] for q in t['queries']}; b=min(vals.values())
    return min([q for q,v in vals.items() if abs(v-b)<1e-12],key=lambda q:t['queries'].index(q))

def eval_obj(tasks,obj): return sum(choose(t,obj)==t['optimal'] for t in tasks)

acq=build_tasks(ACQ_FAMILIES,ACQ_PER_FAMILY,'acq')
held=build_tasks(HELD_FAMILIES,HELD_PER_FAMILY,'held')

# Verifier-supported acquisition: select relation object solely by exact acquisition action labels.
acq_scores={g:eval_obj(acq,g) for g in GRAMMAR}
best=max(acq_scores.values()); winners=[g for g,v in acq_scores.items() if v==best]
retained=sorted(winners)[0]

# Require the acquisition evidence to identify a unique best behavioral object; otherwise no retention claim.
unique=(len(winners)==1)

# Matched sham: same one-symbol object size, but selected using a wrong-pair permutation of verifier labels.
perm=list(range(len(acq))); RNG.shuffle(perm)
wrong_labels=[acq[j]['optimal'] for j in perm]
def wrong_score(obj):
    return sum(choose(t,obj)==lab for t,lab in zip(acq,wrong_labels))
sham_scores={g:wrong_score(g) for g in GRAMMAR}; sham=max(GRAMMAR,key=lambda g:(sham_scores[g],-GRAMMAR.index(g)))
if sham==retained:
    # Predeclared deterministic fallback to best non-retained wrong-label object.
    sham=max([g for g in GRAMMAR if g!=retained],key=lambda g:(sham_scores[g],-GRAMMAR.index(g)))

# Baselines: lexical cold and non-target query-entropy heuristic; ablation removes retained object back to cold.
cold='lexical_index'; recheck='negative_query_entropy'; ablation='lexical_index'
summary={}
for name,obj in [('COLD',cold),('RECHECK_HEURISTIC',recheck),('RETAINED_BEHAVIORAL_OBJECT',retained),('SHAM_OBJECT',sham),('ABLATION',ablation)]:
    k=eval_obj(held,obj); summary[name]={'object':obj,'optimal':k,'n':len(held),'optimal_rate':k/len(held)}

# Stronger causal profile: count tasks where retained succeeds while ablation fails, and vice versa.
r_plus=sum(choose(t,retained)==t['optimal'] and choose(t,ablation)!=t['optimal'] for t in held)
r_harm=sum(choose(t,retained)!=t['optimal'] and choose(t,ablation)==t['optimal'] for t in held)

out={'seed':SEED,'grammar':GRAMMAR,'acquisition_n':len(acq),'heldout_n':len(held),'acquisition_families':ACQ_FAMILIES,'heldout_families':HELD_FAMILIES,'acquisition_scores':acq_scores,'retained_object':retained,'unique_acquisition_winner':unique,'sham_scores':sham_scores,'sham_object':sham,'summary':summary,'retained_help_only':r_plus,'retained_harm_only':r_harm}
(OUT/'summary.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

# Frozen gates.
assert unique, ('NO_UNIQUE_RETAINED_OBJECT',winners,acq_scores)
v=summary['RETAINED_BEHAVIORAL_OBJECT']['optimal_rate']
assert v>summary['COLD']['optimal_rate']
assert v>summary['RECHECK_HEURISTIC']['optimal_rate']
assert v>summary['SHAM_OBJECT']['optimal_rate']
assert v>summary['ABLATION']['optimal_rate']
assert r_plus>r_harm
print('PASS_BEHAVIORAL_OBJECT_PERSISTENCE_V1')
