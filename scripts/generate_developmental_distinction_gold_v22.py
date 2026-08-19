#!/usr/bin/env python3
from pathlib import Path
import subprocess
subprocess.run(['python3','scripts/generate_developmental_distinction_quotient_v21.py'],check=True)
src=Path('scripts/run_developmental_distinction_quotient_v21.py')
dst=Path('scripts/run_developmental_distinction_gold_v22.py')
s=src.read_text()
s=s.replace('developmental-distinction-quotient-v21','developmental-distinction-gold-v22')
s=s.replace('fault-v21-','fault-v22-')
s=s.replace('DEV_PER_FAMILY=3','SEEN_PER_FAMILY=4\nGOLD_PER_FAMILY=5\nDEV_PER_FAMILY=0')
s=s.replace('HOLDOUT_PER_FAMILY=1','HOLDOUT_PER_FAMILY=GOLD_PER_FAMILY')
s=s.replace("need=DEV_PER_FAMILY+HOLDOUT_PER_FAMILY", "need=SEEN_PER_FAMILY+GOLD_PER_FAMILY")
s=s.replace("selected[fam]=[r for _,r in pool[:need]]", "selected[fam]=[r for _,r in pool[SEEN_PER_FAMILY:SEEN_PER_FAMILY+GOLD_PER_FAMILY]]")
s=s.replace("rows.append({'family':fam,'case':rel,'split':'dev' if j<DEV_PER_FAMILY else 'holdout','features':feature_row(ferr)})", "rows.append({'family':fam,'case':rel,'split':'gold','features':feature_row(ferr)})")
start=s.find("dev=[r for r in rows")
if start<0: raise SystemExit('V22 evaluation tail anchor missing')
new_tail=r'''# V22 sealed gold evaluation: no fitting, no quotient search, no adaptation.
# Frozen from V21 before these gold cases were inspected.
FROZEN_RULE={'NONE':'INFER_APP','U':'PROJECTION','F':'IOTA'}

def frozen_predict(row):
    return FROZEN_RULE.get(row['features']['final_depth_step'],'INFER_APP')

gold=rows
preds=[frozen_predict(r) for r in gold]
acc=sum(p==r['family'] for p,r in zip(preds,gold))/len(gold)
per_family={}
heldout_rows=[]
learned_calls=[]; binary_calls=[]
for fam in FAMILIES:
    rs=[(r,p) for r,p in zip(gold,preds) if r['family']==fam]
    per_family[fam]={'n':len(rs),'accuracy':sum(p==r['family'] for r,p in rs)/len(rs)}
for r,pred in zip(gold,preds):
    fam=r['family']; case=ARENA/r['case']
    la=verifier_calls_for_prediction(fault_bins[fam],trace_bin,case,fam,pred)
    ba=verifier_calls_for_prediction(fault_bins[fam],trace_bin,case,fam,FIXED_ORDER[0])
    learned_calls.append(len(la)); binary_calls.append(len(ba))
    heldout_rows.append({**r,'prediction':pred,'learned_calls':len(la),'binary_calls':len(ba),'learned_attempts':la,'binary_attempts':ba})
mean_l=sum(learned_calls)/len(learned_calls); mean_b=sum(binary_calls)/len(binary_calls)
summary={
  'status':'SEALED_GOLD_V22',
  'semantic_mismatches':0,
  'common_native_boundary':locs[0],
  'families':FAMILIES,
  'frozen_rule':FROZEN_RULE,
  'frozen_feature':'final_depth_step',
  'seen_cases_skipped_per_family':SEEN_PER_FAMILY,
  'gold_cases_per_family':GOLD_PER_FAMILY,
  'gold_episodes':len(gold),
  'gold_accuracy':acc,
  'per_family':per_family,
  'learned_mean_verifier_calls':mean_l,
  'binary_mean_verifier_calls':mean_b,
  'call_reduction_factor':mean_b/mean_l,
  'selected_cases':selected,
  'heldout_rows':heldout_rows,
  'rows':rows,
}
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if acc!=1.0: raise SystemExit('frozen V21 quotient failed sealed gold transfer')
if any(v['accuracy']!=1.0 for v in per_family.values()): raise SystemExit('frozen quotient failed a gold family')
if mean_l>=mean_b: raise SystemExit('frozen quotient did not reduce verifier search on gold')
'''
s=s[:start]+new_tail
s=s.replace("'status':'LIVE_MINIMAL_RELATIONAL_QUOTIENT_V21'", "'status':'SEALED_GOLD_V22'")
dst.write_text(s)
print('generated V22 sealed gold evaluation: frozen V21 rule, 5 unseen cases per family')
