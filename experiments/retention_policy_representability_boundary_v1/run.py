#!/usr/bin/env python3
"""Exhaustive representability fork for the frozen retention-policy result."""
import hashlib, importlib.util, itertools, json, pathlib

ROOT=pathlib.Path(__file__).parent
PARENT=ROOT.parent/'verified_retention_policy_genesis_v1'/'run.py'
spec=importlib.util.spec_from_file_location('parent',PARENT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

GEOMETRY=(1,1,1,1,1,-1,-1,1)
TRAIN=[m.make_stream(x,0) for x in range(11,15)]
HELD=[m.make_stream(x,0) for x in range(101,121)]
SHIFT_CAL=[m.make_stream(x,1) for x in range(201,205)]
SHIFT_TEST=[m.make_stream(x,1) for x in range(301,321)]
ALL=TRAIN+HELD+SHIFT_CAL+SHIFT_TEST

def signature(w,states): return tuple(tuple(sorted(m.choose(w,s))) for s in states)
def main():
    selected,calls,train_cost=m.synthesize(TRAIN)
    geo_sig=signature(GEOMETRY,ALL)
    equivalents=[]; evaluated=0
    for w in itertools.product(m.WEIGHTS,repeat=len(m.FEATURES)):
        evaluated+=1
        if signature(w,ALL)==geo_sig: equivalents.append(w)
    diffs=[]
    for cohort,states in [('train',TRAIN),('heldout',HELD),('shift_calibration',SHIFT_CAL),('shift_test',SHIFT_TEST)]:
        for s in states:
            a=m.choose(selected,s);b=m.choose(GEOMETRY,s)
            if a!=b:
                diffs.append({'cohort':cohort,'seed':s['seed'],'selected':sorted(a),'geometry':sorted(b),
                  'selected_cost':s['costs'][a],'geometry_cost':s['costs'][b],'geometry_advantage':s['costs'][a]-s['costs'][b]})
    train_selected=m.evaluate(lambda s:m.choose(selected,s),TRAIN)
    train_geometry=m.evaluate(lambda s:m.choose(GEOMETRY,s),TRAIN)
    held_selected=m.evaluate(lambda s:m.choose(selected,s),HELD)
    held_geometry=m.evaluate(lambda s:m.choose(GEOMETRY,s),HELD)
    representable=bool(equivalents)
    fork='REPRESENTABLE_BUT_UNSELECTED' if representable else 'NOT_REPRESENTABLE_UNKNOWN_EXPRESSIVITY'
    gates={'complete_grammar_enumeration':evaluated==len(m.WEIGHTS)**len(m.FEATURES),
      'geometry_coefficients_in_grammar':all(x in m.WEIGHTS for x in GEOMETRY),
      'behavioral_representative_exists':representable,
      'selected_policy_training_preferred':train_selected<train_geometry,
      'geometry_heldout_preferred':held_geometry<held_selected,
      'nonempty_decision_residual':bool(diffs)}
    snap={'parent_authority':'44557424b7b9002ed6e17e54bc645f13772edff1','features':m.FEATURES,'weights':m.WEIGHTS,
      'state_seeds':[s['seed'] for s in ALL],'grammar_size':len(m.WEIGHTS)**len(m.FEATURES),'decision_states':len(ALL)}
    enc=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),default=list)
    ev={'verdict':fork,'classification':'FINITE_EXHAUSTIVE_POLICY_REPRESENTABILITY_BOUNDARY',
      'selected_policy':dict(zip(m.FEATURES,selected)),'geometry_policy':dict(zip(m.FEATURES,GEOMETRY)),
      'grammar_programs_evaluated':evaluated,'decision_states_evaluated':len(ALL),'behaviorally_equivalent_program_count':len(equivalents),
      'canonical_equivalent':dict(zip(m.FEATURES,min(equivalents))) if equivalents else None,
      'costs':{'training_selected':train_selected,'training_geometry':train_geometry,'heldout_selected':held_selected,'heldout_geometry':held_geometry},
      'decision_divergence_count':len(diffs),'minimal_divergence':diffs[0] if diffs else None,'divergences':diffs,
      'diagnosis':'SELECTION_OBJECTIVE_OR_VALUE_EVIDENCE_RESIDUAL' if representable else 'POLICY_LANGUAGE_EXPRESSIVITY_RESIDUAL',
      'gates':gates,'snapshot_digest':hashlib.sha256(enc(snap).encode()).hexdigest(),
      'not_established':['improved value estimator','natural-world policy induction','open-ended retention policy genesis']}
    out=ROOT/'results';out.mkdir(exist_ok=True)
    (out/'snapshot.json').write_text(json.dumps(snap,indent=2,default=list)+'\n')
    (out/'evidence.json').write_text(json.dumps(ev,indent=2)+'\n')
    print(json.dumps(ev,indent=2))
if __name__=='__main__':main()
