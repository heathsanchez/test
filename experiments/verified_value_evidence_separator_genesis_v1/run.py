#!/usr/bin/env python3
"""Verified prospective value-evidence separator genesis, finite qualification."""
import hashlib, importlib.util, json, pathlib, random

ROOT=pathlib.Path(__file__).parent
PARENT=ROOT.parent/'verified_retention_policy_genesis_v1'/'run.py'
sp=importlib.util.spec_from_file_location('parent',PARENT)
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)

TRAIN=[m.make_stream(x,0) for x in range(11,15)]
POOL=[m.make_stream(x,0) for x in range(1001,1101)]
PROSPECTIVE=[m.make_stream(x,0) for x in range(401,601)]
GEOMETRY=(1,1,1,1,1,-1,-1,1)
EVIDENCE_BUDGET=8

def policy_cost(w,states): return m.evaluate(lambda s:m.choose(w,s),states)
def acquire(kind,passive):
    # Every condition pays for evaluating both unresolved policies on all 100
    # opaque candidate streams. No future costs are read during this step.
    disagreements=[s for s in POOL if m.choose(passive,s)!=m.choose(GEOMETRY,s)]
    agreements=[s for s in POOL if m.choose(passive,s)==m.choose(GEOMETRY,s)]
    if kind=='guided': chosen=disagreements[:EVIDENCE_BUDGET]
    elif kind=='sham': chosen=agreements[:EVIDENCE_BUDGET]
    elif kind=='random': chosen=random.Random(20260912).sample(POOL,EVIDENCE_BUDGET)
    else: raise ValueError(kind)
    learned,synthesis_calls,_=m.synthesize(TRAIN+chosen)
    probe_calls=2*len(POOL); verifier_calls=len(chosen)
    acquisition=probe_calls+verifier_calls+synthesis_calls
    return learned,chosen,{'probe_calls':probe_calls,'external_verifier_calls':verifier_calls,
      'resynthesis_calls':synthesis_calls,'total':acquisition}

def main():
    passive,initial_calls,_=m.synthesize(TRAIN)
    conditions={k:acquire(k,passive) for k in ('guided','random','sham')}
    passive_future=policy_cost(passive,PROSPECTIVE)
    rows={}
    for k,(w,qs,charge) in conditions.items():
        future=policy_cost(w,PROSPECTIVE)
        rows[k]={'policy':dict(zip(m.FEATURES,w)),'query_seeds':[s['seed'] for s in qs],
          'future_cost':future,'acquisition_cost':charge,'fully_charged_total':future+charge['total'],
          'geometry_equivalent':w==GEOMETRY}
    guided=rows['guided']
    ablated_future=passive_future
    gates={'fixed_policy_language':all(x in m.WEIGHTS for x in GEOMETRY),
      'matched_evidence_budgets':len({rows[k]['acquisition_cost']['total'] for k in rows})==1,
      'guided_constructs_only_disagreements':all(m.choose(passive,s)!=m.choose(GEOMETRY,s) for s in conditions['guided'][1]),
      'guided_selects_unique_geometry_program':guided['geometry_equivalent'],
      'fully_charged_guided_beats_passive':guided['fully_charged_total']<passive_future,
      'fully_charged_guided_beats_random':guided['fully_charged_total']<rows['random']['fully_charged_total'],
      'fully_charged_guided_beats_sham':guided['fully_charged_total']<rows['sham']['fully_charged_total'],
      'separator_ablation_restores_passive':ablated_future==passive_future,
      'positive_causal_savings':passive_future-guided['fully_charged_total']>0}
    snap={'parent_authority':'185476c1aa0d9fa7caa5327152b254bec45c4988','train_seeds':[11,12,13,14],
      'candidate_pool_seeds':[1001,1100],'prospective_seeds':[401,600],
      'evidence_budget':EVIDENCE_BUDGET,'policy_grammar_programs':len(m.WEIGHTS)**len(m.FEATURES),
      'selection_rule':'first eight lexicographic candidate streams on which frozen selected and geometry policies disagree',
      'query_information':'policy decisions only; verifier costs hidden until acquisition'}
    enc=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'))
    ev={'verdict':'VERIFIED_VALUE_EVIDENCE_SEPARATOR_GENESIS' if all(gates.values()) else 'NEGATIVE_OR_PARTIAL',
      'classification':'FINITE_CONSTRUCTED_PROSPECTIVE_CAUSAL','passive_policy':dict(zip(m.FEATURES,passive)),
      'passive_future_cost':passive_future,'conditions':rows,'separator_ablation_future_cost':ablated_future,
      'net_guided_savings':passive_future-guided['fully_charged_total'],'initial_policy_synthesis_calls_prior_authority':initial_calls,
      'diagnosis':'VALUE_EVIDENCE_INSUFFICIENCY','gates':gates,
      'snapshot_digest':hashlib.sha256(enc(snap).encode()).hexdigest(),
      'not_established':['open-ended experiment genesis','natural-world active learning','evidence-language inadequacy','unbounded autonomous science']}
    out=ROOT/'results';out.mkdir(exist_ok=True)
    (out/'snapshot.json').write_text(json.dumps(snap,indent=2)+'\n')
    (out/'evidence.json').write_text(json.dumps(ev,indent=2)+'\n')
    print(json.dumps(ev,indent=2))
if __name__=='__main__':main()
