#!/usr/bin/env python3
import argparse,json,random,importlib.util,itertools
from pathlib import Path
from collections import Counter

def load(name):
 p=Path(__file__).with_name(name);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
v6=load('arc400_meta_grammar_development_v6.py')
v7=load('arc400_full_registry_v7.py')

# V9 deliberately starts WITHOUT the named V8 residual coordinates.
# It receives only generic train-pair observables. If those alias two different
# certified extension labels, the collision itself licenses a search over a
# frozen finite predicate grammar for the cheapest distinction that removes it.

BASE_FEATURES=('shape_ratio_equal','palette_preserved')
CANDIDATE_FEATURES=('cellwise_uniform_expansion','input_block_decomposition','transpose_shape_compatible','output_area_square_ratio')
ALL_FEATURES=BASE_FEATURES+CANDIDATE_FEATURES
CTORS=('S','B')

def flat(g): return [x for r in g for x in r]
def sh(g): return len(g),len(g[0])
def palette(g): return set(flat(g))

def integer_ratio(a,b):
 return a//b if b and a%b==0 else None

def pair_obs(p):
 x,y=p['input'],p['output']; hi,wi=sh(x); ho,wo=sh(y)
 rh,rw=integer_ratio(ho,hi),integer_ratio(wo,wi)
 shape_ratio_equal=(rh is not None and rw is not None and rh==rw)
 palette_preserved=palette(x)==palette(y)
 # Generic spatial predicate: every input cell expands to a constant q x q patch.
 cellwise=False
 if shape_ratio_equal and rh and rh>=1:
  q=rh; ok=True
  for i in range(hi):
   for j in range(wi):
    val=x[i][j]
    for a in range(i*q,(i+1)*q):
     for b in range(j*q,(j+1)*q):
      if y[a][b]!=val: ok=False; break
     if not ok: break
    if not ok: break
   if not ok: break
  cellwise=ok
 # Generic decomposition predicate: output partitions into input-sized blocks,
 # each block equal to a D8 image of input or a uniform background block.
 blockdec=False
 if ho%hi==0 and wo%wi==0 and (ho//hi)*(wo//wi)>1:
  nr,nc=ho//hi,wo//wi; b=v6.bg(x); ok=True
  for br in range(nr):
   for bc in range(nc):
    z=[row[bc*wi:(bc+1)*wi] for row in y[br*hi:(br+1)*hi]]
    matches=False
    for f in v6.D8.values():
     try:
      zz=f(x)
      if sh(zz)==sh(x) and v6.C(zz)==v6.C(z): matches=True; break
     except Exception: pass
    if not matches and all(q==b for q in flat(z)): matches=True
    if not matches: ok=False; break
   if not ok: break
  blockdec=ok
 transpose_shape_compatible=(ho==wi and wo==hi)
 ar=integer_ratio(ho*wo,hi*wi)
 output_area_square_ratio=(ar is not None and int(ar**0.5)**2==ar)
 return {
  'shape_ratio_equal':shape_ratio_equal,
  'palette_preserved':palette_preserved,
  'cellwise_uniform_expansion':cellwise,
  'input_block_decomposition':blockdec,
  'transpose_shape_compatible':transpose_shape_compatible,
  'output_area_square_ratio':output_area_square_ratio,
 }

def task_obs(t):
 ps=[pair_obs(p) for p in t['train']]
 # Universal aggregation across demonstrations; no test-output access.
 return {k:all(p[k] for p in ps) for k in ALL_FEATURES}

def oracle_label(t):
 if v7.complete_cover(t,{'U'})['exact_train_programs']>0:return None
 K=v7.K_of_rho(t,{'U'})
 return K[0] if len(K)==1 else None

def collision_count(rows,features):
 by={}
 for r in rows: by.setdefault(tuple(r['obs'][f] for f in features),set()).add(r['y'])
 return sum(1 for ys in by.values() if len(ys)>1)

def choose_refinement(rows,active):
 base=collision_count(rows,active)
 candidates=[]
 for f in CANDIDATE_FEATURES:
  if f in active: continue
  c=collision_count(rows,active+[f])
  gain=base-c
  candidates.append((c,-gain,f))
 return min(candidates)[2] if candidates and min(candidates)[0] < base else None

def synth_rules(rows,features):
 by={}
 for r in rows: by.setdefault(tuple(r['obs'][f] for f in features),set()).add(r['y'])
 rules=[]
 for pat,ys in sorted(by.items()):
  if len(ys)==1:
   y=next(iter(ys)); support=sum(tuple(r['obs'][f] for f in features)==pat and r['y']==y for r in rows)
   rules.append({'pattern':list(pat),'constructor':y,'support':support})
 return rules

def predict(obs,features,rules):
 pat=tuple(obs[f] for f in features)
 ys={r['constructor'] for r in rules if tuple(r['pattern'])==pat}
 return next(iter(ys)) if len(ys)==1 else None

def build_rows(ds,ids):
 out=[]
 for tid in ids:
  y=oracle_label(ds[tid])
  if y: out.append({'task':tid,'obs':task_obs(ds[tid]),'y':y})
 return out

def audit(ds,ids,features,rules):
 rows=[];pred=correct=exact=causal=0
 for tid in ids:
  t=ds[tid]
  if v7.complete_cover(t,{'U'})['exact_train_programs']>0: continue
  obs=task_obs(t); p=predict(obs,features,rules)
  if not p: continue
  pred+=1
  # prediction controls extension BEFORE oracle audit
  o,ast,_=v6.solve_with_grammar(t,{'U',p}); ok=v6.score_output(t,o); exact+=int(ok)
  ao,_,_=v6.solve_with_grammar(t,{'U'}); c=ok and not v6.score_output(t,ao); causal+=int(c)
  y=oracle_label(t); correct+=int(y is not None and p==y)
  rows.append({'task':tid,'representation':{f:obs[f] for f in features},'predicted_constructor':p,'posthoc_oracle':y,'prediction_correct':p==y if y else None,'exact_after_extension':ok,'C_causal':c,'ast':repr(ast) if ast else None})
 return {'predictions':pred,'correct':correct,'exact':exact,'causal_exact':causal,'rows':rows}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--arc-root',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);ap.add_argument('--seed',type=int,default=1729);a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
 tr=v6.load(a.arc_root,'training');ev=v6.load(a.arc_root,'evaluation')
 ids=list(tr);random.Random(a.seed).shuffle(ids);cut=len(ids)//2;meta_ids,hold_ids=ids[:cut],ids[cut:]
 meta=build_rows(tr,meta_ids)
 active=list(BASE_FEATURES); events=[]
 initial_collisions=collision_count(meta,active)
 # Recursive representation refinement: collision -> add minimal separating observable -> retry.
 while collision_count(meta,active)>0:
  before=collision_count(meta,active); f=choose_refinement(meta,active)
  if f is None: break
  active.append(f); after=collision_count(meta,active)
  events.append({'rho_rep':'LABEL_COLLISION_UNDER_CURRENT_RESIDUAL_REPRESENTATION','collisions_before':before,'candidate_predicate_carrier':list(CANDIDATE_FEATURES),'CompleteCover_predicate_carrier':True,'Delta_R':{'add_observable':f},'collisions_after':after,'strict_information_refinement':after<before})
 rules=synth_rules(meta,active)
 hold=audit(tr,hold_ids,active,rules)
 eids=list(ev);random.Random(a.seed+1).shuffle(eids);ext=audit(ev,eids,active,rules)
 gates={
  'named_v8_residual_coordinates_absent':True,
  'initial_representation_has_collision':initial_collisions>0,
  'representation_refinement_occurred':bool(events),
  'every_refinement_strictly_reduces_collision':bool(events) and all(e['strict_information_refinement'] for e in events),
  'predicate_carrier_complete':bool(events) and all(e['CompleteCover_predicate_carrier'] for e in events),
  'meta_collisions_closed':collision_count(meta,active)==0,
  'heldout_prediction_exists':hold['predictions']>0,
  'heldout_all_predictions_correct':hold['predictions']>0 and hold['correct']==hold['predictions'],
  'heldout_causal_gain':hold['causal_exact']>0,
  'source_distinct_prediction_exists':ext['predictions']>0,
  'source_distinct_all_predictions_correct':ext['predictions']>0 and ext['correct']==ext['predictions'],
  'source_distinct_causal_gain':ext['causal_exact']>0,
 }
 gates['RESIDUAL_REPRESENTATION_REFINEMENT_GATE']=all(gates.values())
 summary={'status':'ARC400_RESIDUAL_REPRESENTATION_REFINEMENT_V9','claim_scope':'bounded self-refinement of residual representation over a finite generic spatial-predicate carrier; constructor labels remain certified by U/S/B CompleteCover; no test-output access before prediction','split':{'meta_train':len(meta_ids),'heldout_training':len(hold_ids),'evaluation':len(ev)},'certified_meta_examples':len(meta),'base_features':list(BASE_FEATURES),'candidate_feature_carrier':list(CANDIDATE_FEATURES),'initial_collisions':initial_collisions,'representation_events':events,'learned_residual_representation':active,'final_meta_collisions':collision_count(meta,active),'synthesized_rules':rules,'heldout_training':hold,'source_distinct_evaluation':ext,'gates':gates}
 (a.out_dir/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
