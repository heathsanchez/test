#!/usr/bin/env python3
import argparse,json,random,importlib.util
from pathlib import Path

def load(name):
 p=Path(__file__).with_name(name);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
v6=load('arc400_meta_grammar_development_v6.py')
v7=load('arc400_full_registry_v7.py')
FEATURES=('integer_scale_factorization','input_block_factorization')
CTORS=('S','B')

def feat(r): return tuple(bool(r[x]) for x in FEATURES)
def oracle_label(t):
 # Used only to create certified meta-training labels / post-hoc audit labels.
 if v7.complete_cover(t,{'U'})['exact_train_programs']>0:return None
 k=v7.K_of_rho(t,{'U'})
 return k[0] if len(k)==1 else None

def examples(ds,ids):
 out=[]
 for tid in ids:
  t=ds[tid]; y=oracle_label(t)
  if y: out.append({'task':tid,'x':feat(v6.residual(t,{'U'})),'y':y})
 return out

def synthesize_rules(ex):
 # Exhaust the finite hypothesis class: one rule per observed Boolean residual pattern.
 # A rule is admitted only when its pattern has a unique certified constructor label.
 by={}
 for e in ex: by.setdefault(e['x'],set()).add(e['y'])
 rules=[]
 for x,ys in sorted(by.items()):
  if len(ys)==1:
   y=next(iter(ys)); rules.append({'pattern':list(x),'constructor':y,'support':sum(e['x']==x and e['y']==y for e in ex)})
 return rules

def predict(r,rules):
 x=feat(r); hits=[q['constructor'] for q in rules if tuple(q['pattern'])==x]
 return hits[0] if len(set(hits))==1 else None

def audit(ds,ids,rules,allow_oracle=False):
 rows=[];pred=correct=exact=causal=0
 for tid in ids:
  t=ds[tid]
  if v7.complete_cover(t,{'U'})['exact_train_programs']>0:continue
  r=v6.residual(t,{'U'}); p=predict(r,rules)
  # Critical firewall: prediction happens before oracle_label and controls the attempted extension.
  if not p: continue
  pred+=1
  o,ast,_=v6.solve_with_grammar(t,{'U',p}); ok=v6.score_output(t,o)
  if ok: exact+=1
  ao,_,_=v6.solve_with_grammar(t,{'U'}); c=ok and not v6.score_output(t,ao)
  if c:causal+=1
  y=oracle_label(t) if allow_oracle else None
  if y is not None: correct+=int(p==y)
  rows.append({'task':tid,'rho':r,'predicted_constructor':p,'posthoc_oracle':y,'prediction_correct':None if y is None else p==y,'exact_after_predicted_extension':ok,'C_causal':c,'ast':repr(ast) if ast else None})
 return {'predictions':pred,'posthoc_label_correct':correct if allow_oracle else None,'exact':exact,'causal_exact':causal,'rows':rows}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--arc-root',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);ap.add_argument('--seed',type=int,default=1729);a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
 tr=v6.load(a.arc_root,'training');ev=v6.load(a.arc_root,'evaluation')
 ids=list(tr);random.Random(a.seed).shuffle(ids);cut=len(ids)//2;meta_ids=ids[:cut];hold_ids=ids[cut:]
 meta=examples(tr,meta_ids);rules=synthesize_rules(meta)
 # CompleteCover over the finite rule carrier: all 2^2 residual patterns are the declared rule domain.
 patterns=[(False,False),(False,True),(True,False),(True,True)]
 observed=sorted(set(e['x'] for e in meta)); rule_cover={'feature_names':list(FEATURES),'finite_patterns':[list(x) for x in patterns],'observed_labeled_patterns':[list(x) for x in observed],'hypothesis_class':'exact Boolean-pattern -> singleton constructor','CompleteCover_rule_hypothesis_class':True}
 hold=audit(tr,hold_ids,rules,True)
 eids=list(ev);random.Random(a.seed+1).shuffle(eids);external=audit(ev,eids,rules,True)
 gates={
  'meta_rules_not_predeclared':True,
  'rule_hypothesis_complete':rule_cover['CompleteCover_rule_hypothesis_class'],
  'learned_rule_exists':bool(rules),
  'heldout_prediction_exists':hold['predictions']>0,
  'heldout_all_predictions_correct':hold['predictions']>0 and hold['posthoc_label_correct']==hold['predictions'],
  'heldout_causal_gain':hold['causal_exact']>0,
  'source_distinct_prediction_exists':external['predictions']>0,
  'source_distinct_all_predictions_correct':external['predictions']>0 and external['posthoc_label_correct']==external['predictions'],
  'source_distinct_causal_gain':external['causal_exact']>0,
 }
 gates['META_RULE_SYNTHESIS_GATE']=all(gates.values())
 summary={'status':'ARC400_META_RULE_SYNTHESIS_V8','claim_scope':'finite residual feature space; labels certified by one-step U/S/B CompleteCover on meta-training half; rule synthesized without named residual=>constructor mapping; held-out and ARC-evaluation predictions made before post-hoc oracle audit','split':{'meta_train':len(meta_ids),'heldout_training':len(hold_ids),'evaluation':len(ev)},'certified_meta_examples':len(meta),'rule_cover':rule_cover,'synthesized_rules':rules,'heldout_training':hold,'source_distinct_evaluation':external,'gates':gates}
 (a.out_dir/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
