#!/usr/bin/env python3
"""Behavioral-object equivalence-class separator V2.

Parent: Behavioral Object Persistence V1, run 32807496896.
That run was non-evidentiary for unique-object retention because five frozen
relations tied 72/72 on acquisition. This test does not break that tie post hoc.
It freezes the entire five-member winner set and asks whether the members are
observationally equivalent on the original held-out panel and on a new,
independently seeded stress panel.
"""
import json, math, random
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

PARENT_SEED=2026082516
STRESS_SEED=2026082517
PREFIXES='ABCD'; SUFFIXES='XYZ'
OUT=Path('artifacts/behavioral_object_equivalence_class_v2'); OUT.mkdir(parents=True,exist_ok=True)

TIED=(
 'true_target_entropy',
 'unweighted_target_ambiguity',
 'weighted_target_setsize',
 'negative_singleton_mass',
 'max_target_setsize',
)
NEGATIVE='negative_query_entropy'

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

def build_tasks(rng,families,n_each,label):
    tasks=[]; pairs=[a+b for a in PREFIXES for b in SUFFIXES]
    for m in families:
        H0=all_hypotheses(m); made=0; attempts=0
        while made<n_each and attempts<500000:
            attempts+=1; truth=rng.choice(H0); sh=pairs[:]; rng.shuffle(sh)
            k=rng.choice([4,5,6]); obs_pairs=sh[:k]; rem=[p for p in pairs if p not in obs_pairs]
            if len(rem)<5: continue
            target=rem[0]; queries=rem[1:5]
            obs={p:pred(truth,p,m) for p in obs_pairs}; H=survivors(H0,obs,m)
            if len(H)<4 or len(H)>5000: continue
            scores={q:expected_target_entropy(H,q,target,m) for q in queries}
            best=min(scores.values()); worst=max(scores.values())
            if best>1e-12 or worst-best<0.25: continue
            optimal=sorted(queries,key=lambda q:(scores[q],q))[0]
            tasks.append({'id':f'{label}_m{m}_{made:03d}','m':m,'truth':truth,'obs':obs,'target':target,'queries':queries,'H':H,'true_scores':scores,'optimal':optimal}); made+=1
        assert made==n_each,(m,made)
    return tasks

def features(t,q):
    H=t['H']; m=t['m']; target=t['target']; part=target_partition(H,q,target,m)
    targetset_sizes=[len(v) for v in part.values()]
    outcome_counts=Counter(pred(h,q,m) for h in H); n=len(H)
    weighted_setsize=sum(outcome_counts[o]/n*len(part[o]) for o in part)
    singleton_mass=sum(outcome_counts[o] for o in part if len(part[o])==1)/n
    return {
        'true_target_entropy': expected_target_entropy(H,q,target,m),
        'unweighted_target_ambiguity': sum(math.log2(max(1,s)) for s in targetset_sizes)/len(targetset_sizes),
        'weighted_target_setsize': weighted_setsize,
        'negative_singleton_mass': -singleton_mass,
        'max_target_setsize': max(targetset_sizes),
        'negative_query_entropy': -query_entropy(H,q,m),
    }

def choose(t,obj):
    vals={q:features(t,q)[obj] for q in t['queries']}; b=min(vals.values())
    return min([q for q,v in vals.items() if abs(v-b)<1e-12],key=lambda q:t['queries'].index(q))

def panel_report(tasks):
    choices={g:[choose(t,g) for t in tasks] for g in TIED}
    signatures={g:[t['queries'].index(q) for t,q in zip(tasks,choices[g])] for g in TIED}
    acc={g:sum(q==t['optimal'] for q,t in zip(choices[g],tasks)) for g in TIED}
    same_actions=all(signatures[g]==signatures[TIED[0]] for g in TIED[1:])
    neg=[choose(t,NEGATIVE) for t in tasks]
    neg_acc=sum(q==t['optimal'] for q,t in zip(neg,tasks))
    neg_signature=[t['queries'].index(q) for t,q in zip(tasks,neg)]
    return {
        'n':len(tasks),
        'same_actions_all_five':same_actions,
        'accuracies':acc,
        'all_five_perfect':all(v==len(tasks) for v in acc.values()),
        'negative_control_accuracy':neg_acc,
        'negative_control_same_signature':neg_signature==signatures[TIED[0]],
        'pairwise_disagreements':{
            f'{a}__{b}':sum(x!=y for x,y in zip(signatures[a],signatures[b]))
            for i,a in enumerate(TIED) for b in TIED[i+1:]
        },
    }

# Recreate the exact parent acquisition and held-out panels by preserving the same RNG stream.
prng=random.Random(PARENT_SEED)
acq=build_tasks(prng,[2,3],36,'acq')
held=build_tasks(prng,[5],48,'held')
acq_scores={g:sum(choose(t,g)==t['optimal'] for t in acq) for g in TIED}

# New panel is frozen independently of the parent panel and uses a fresh seed.
srng=random.Random(STRESS_SEED)
stress=build_tasks(srng,[5],96,'stress')

held_report=panel_report(held)
stress_report=panel_report(stress)
out={
 'schema':'behavioral.object.equivalence.class.v2',
 'parent_run':32807496896,
 'parent_seed':PARENT_SEED,
 'stress_seed':STRESS_SEED,
 'frozen_tied_class':TIED,
 'negative_control':NEGATIVE,
 'acquisition_n':len(acq),
 'acquisition_scores':acq_scores,
 'original_heldout':held_report,
 'new_stress_panel':stress_report,
}
(OUT/'summary.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

# Frozen gates: reproduce the tie, then test class identity rather than selecting a representative.
assert all(acq_scores[g]==72 for g in TIED), acq_scores
assert held_report['same_actions_all_five']
assert held_report['all_five_perfect']
assert stress_report['same_actions_all_five']
assert stress_report['all_five_perfect']
assert not held_report['negative_control_same_signature']
assert not stress_report['negative_control_same_signature']
assert held_report['negative_control_accuracy'] < held_report['n']
assert stress_report['negative_control_accuracy'] < stress_report['n']
print('PASS_BEHAVIORAL_OBJECT_EQUIVALENCE_CLASS_V2')
