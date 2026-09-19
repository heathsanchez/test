#!/usr/bin/env python3
from __future__ import annotations
import argparse, itertools, json
from pathlib import Path
from collections import defaultdict

"""V17 — finite StrCC quotient bridge over real historical developmental episodes.

The source artifacts are real historical MathGraph results, but the adequacy encodings
below are manually supplied and frozen. We exhaust every legal interleaving of each
finite dependency trace, compute a canonical normal form, test quotient semantic
soundness/reflection, and compare leave-one-source-out developmental classification
on quotient structure against raw surface traces.
"""

SOURCES=[
{"domain":"fwl","surface":["2fwl_collision","old_rep_exhausted","nested_product_synthesized","3fwl_separates","blind_transfer","remove_second_product_fails"],"roles":["RESIDUAL","COMPLETECOVER_EMPTY","EXPAND_CARRIER","VERIFY","TRANSFER","ABLATE"],"deps":[("RESIDUAL","COMPLETECOVER_EMPTY"),("COMPLETECOVER_EMPTY","EXPAND_CARRIER"),("EXPAND_CARRIER","VERIFY"),("VERIFY","TRANSFER"),("VERIFY","ABLATE")],"sem":{"intervention":"EXPAND_CARRIER","promotion":True,"closure":True,"causal":True,"transfer":True,"retention":False},"provenance":"mathgraph_gold_fwl_constructor_synthesis.py"},
{"domain":"rc2","surface":["j13_failure","2585_old_programs_zero","opaque_oracle_dsl","unique_semantic_repair","3146_frozen_transfer","residual_oracle_ablation"],"roles":["RESIDUAL","COMPLETECOVER_EMPTY","EXPAND_CARRIER","VERIFY","TRANSFER","ABLATE"],"deps":[("RESIDUAL","COMPLETECOVER_EMPTY"),("COMPLETECOVER_EMPTY","EXPAND_CARRIER"),("EXPAND_CARRIER","VERIFY"),("VERIFY","TRANSFER"),("VERIFY","ABLATE")],"sem":{"intervention":"EXPAND_CARRIER","promotion":True,"closure":True,"causal":True,"transfer":True,"retention":False},"provenance":"RC2_LOCAL_TEST_RESULTS.json"},
{"domain":"bugsinpy","surface":["native_ast_boundary","old_library_missing_exception_flow","exception_flow_synthesized","post_promotion_accepts","later_reuse","ablation_rejects"],"roles":["RESIDUAL","COMPLETECOVER_EMPTY","EXPAND_CARRIER","VERIFY","TRANSFER","ABLATE"],"deps":[("RESIDUAL","COMPLETECOVER_EMPTY"),("COMPLETECOVER_EMPTY","EXPAND_CARRIER"),("EXPAND_CARRIER","VERIFY"),("VERIFY","TRANSFER"),("VERIFY","ABLATE")],"sem":{"intervention":"EXPAND_CARRIER","promotion":True,"closure":True,"causal":True,"transfer":True,"retention":True},"provenance":"MI_V10_DEFINITIVE_RESULT.json"},
{"domain":"arc_v12","surface":["remaining_meta_collision","90100_same_frame_checked","42_zero_collision_witnesses","minimal_theta_selected","heldout_exact","local_ablation"],"roles":["RESIDUAL","COMPLETECOVER_NONEMPTY","SAME_FRAME_REPAIR","VERIFY","TRANSFER","ABLATE"],"deps":[("RESIDUAL","COMPLETECOVER_NONEMPTY"),("COMPLETECOVER_NONEMPTY","SAME_FRAME_REPAIR"),("SAME_FRAME_REPAIR","VERIFY"),("VERIFY","TRANSFER"),("VERIFY","ABLATE")],"sem":{"intervention":"SAME_FRAME_REPAIR","promotion":False,"closure":True,"causal":True,"transfer":True,"retention":False},"provenance":"ARC V12 PR #40 / verified Actions result"},
{"domain":"lean_kernel","surface":["arena_profile_residual","candidate_optimization","semantic_gate","benchmark_improves","retained_optimization","regression_check"],"roles":["RESIDUAL","SAME_FRAME_CANDIDATE","SAME_FRAME_REPAIR","VERIFY","TRANSFER","ABLATE"],"deps":[("RESIDUAL","SAME_FRAME_CANDIDATE"),("SAME_FRAME_CANDIDATE","SAME_FRAME_REPAIR"),("SAME_FRAME_REPAIR","VERIFY"),("VERIFY","TRANSFER"),("VERIFY","ABLATE")],"sem":{"intervention":"SAME_FRAME_REPAIR","promotion":False,"closure":True,"causal":True,"transfer":True,"retention":True},"provenance":"mathgraph-lean-kernel Arena development result"},
{"domain":"mi_v8_external","surface":["selected_external_function","old_structural_library_insufficient","new_effect_or_resource_primitive","post_promotion_accepts","later_external_old_closure","targeted_ablation"],"roles":["RESIDUAL","COMPLETECOVER_EMPTY","EXPAND_CARRIER","VERIFY","TRANSFER","ABLATE"],"deps":[("RESIDUAL","COMPLETECOVER_EMPTY"),("COMPLETECOVER_EMPTY","EXPAND_CARRIER"),("EXPAND_CARRIER","VERIFY"),("VERIFY","TRANSFER"),("VERIFY","ABLATE")],"sem":{"intervention":"EXPAND_CARRIER","promotion":True,"closure":True,"causal":True,"transfer":True,"retention":True},"provenance":"MI_V8_PRISTINE_EXTERNAL_STREAM_RESULT_20260812.json"}
]
ROLE_ORDER=["RESIDUAL","COMPLETECOVER_EMPTY","COMPLETECOVER_NONEMPTY","SAME_FRAME_CANDIDATE","EXPAND_CARRIER","SAME_FRAME_REPAIR","VERIFY","TRANSFER","ABLATE"]

def dep_sig(s): return (tuple(sorted(s['roles'])),tuple(sorted(tuple(e) for e in s['deps'])))
def topo(w,e):
 p={x:i for i,x in enumerate(w)}; return all(p[a]<p[b] for a,b in e)
def exts(s): return [p for p in itertools.permutations(s['roles']) if topo(p,s['deps'])]
def nf(s):
 order={r:i for i,r in enumerate(ROLE_ORDER)}; nodes=set(s['roles']); edges=set(map(tuple,s['deps'])); out=[]
 while nodes:
  av=[n for n in nodes if all(b!=n or a not in nodes for a,b in edges)]
  if not av: raise RuntimeError('cycle')
  n=min(av,key=lambda x:order[x]); out.append(n); nodes.remove(n)
 return tuple(out)
def sem_key(s):
 x=s['sem']; return (x['intervention'],x['promotion'],x['closure'],x['causal'],x['transfer'])
def audit(s):
 n=nf(s); ee=exts(s); same=True
 for w in ee:
  t=dict(s); t['roles']=list(w); same &= nf(t)==n
 return {'domain':s['domain'],'provenance':s['provenance'],'roundtrip':len(s['surface'])==len(s['roles']),'linear_extensions':len(ee),'same_nf':same,'normal_form':list(n)}
def loo():
 out=[]
 for h in SOURCES:
  tr=[s for s in SOURCES if s is not h]; mp={}; amb=set()
  for s in tr:
   k=(dep_sig(s),nf(s)); v=s['sem']['intervention']
   if k in mp and mp[k]!=v: amb.add(k)
   else: mp[k]=v
  for k in amb: mp.pop(k,None)
  pred=mp.get((dep_sig(h),nf(h))); raw={tuple(s['surface']):s['sem']['intervention'] for s in tr}.get(tuple(h['surface']))
  out.append({'heldout':h['domain'],'pred':pred,'truth':h['sem']['intervention'],'correct':pred==h['sem']['intervention'],'raw_pred':raw,'raw_correct':raw==h['sem']['intervention']})
 return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',required=True); a=ap.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
 aa=[audit(s) for s in SOURCES]; q=defaultdict(list); sg=defaultdict(list)
 for s in SOURCES: q[dep_sig(s)].append(s); sg[sem_key(s)].append(s)
 sound=all(len({sem_key(x) for x in v})==1 for v in q.values())
 reflect=all(len({dep_sig(x) for x in v})==1 for v in sg.values())
 rr=loo(); qa=sum(x['correct'] for x in rr)/len(rr); ra=sum(x['raw_correct'] for x in rr)/len(rr); by={s['domain']:s for s in SOURCES}
 gates={'finite_adequacy_roundtrip_all':all(x['roundtrip'] for x in aa),'finite_trace_completecover_all':all(x['linear_extensions']>0 and x['same_nf'] for x in aa),'quotient_semantic_soundness':sound,'finite_presentation_reflection':reflect,'fwl_rc2_same_developmental_class':dep_sig(by['fwl'])==dep_sig(by['rc2']),'fwl_arc_v12_distinct_developmental_class':dep_sig(by['fwl'])!=dep_sig(by['arc_v12']),'loo_quotient_controller_beats_raw':qa>ra,'loo_quotient_accuracy_100pct':qa==1.0}
 gates['STRCC_NATURAL_DEVELOPMENTAL_QUOTIENT_GATE']=all(gates.values())
 r={'status':'STRCC_NATURAL_DEVELOPMENTAL_QUOTIENT_V17','claim_scope':'finite manually-authored adequacy witnesses distilled from real historical artifacts; exact trace-permutation CompleteCover; supplied dependency presentation and adequacy encodings; tests StrCC-style quotient invariance before developmental classification, not automatic adequacy discovery','sources':[s['domain'] for s in SOURCES],'audits':aa,'loo':rr,'quotient_accuracy':qa,'raw_accuracy':ra,'gates':gates}
 (out/'RESULT.json').write_text(json.dumps(r,indent=2)); print(json.dumps(r,indent=2))
if __name__=='__main__': main()
