from __future__ import annotations
import json
from basis import World
from kernel import Kernel
from challenge_pack import *

def safe(x):
    if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items() if not str(k).startswith('_')}
    if isinstance(x,(list,tuple)):return [safe(v) for v in x]
    return x

def add_record(w,r,y):return World(w.world_id+'_plus',w.records+(r,),w.targets+(int(y),),w.complete,w.current_signature)
def ops_in_expr_data(x):
    if not isinstance(x,list) or not x:return set()
    if x[0]=='B':return {int(x[1])}|ops_in_expr_data(x[2])|ops_in_expr_data(x[3])
    return set()
def frontier_ops(r):
    out=set()
    for row in r.get('frontier',[]):out|=ops_in_expr_data(row.get('expr'))
    return out

def main():
    K=Kernel(); E={'experiment':'meta_development_selector_v33','frozen_core':'5f4b6b95137a2feccbb64603f5573ff2e555347f','results':{},'gates':{}}
    pa=K.solve(TRAIN_PAIR_A);pb=K.solve(TRAIN_PAIR_B);pc=K.compile_from('pair',(('t31',pa),('t32',pb)))
    la=K.solve(TRAIN_LAG_A);lb=K.solve(TRAIN_LAG_B);lc=K.compile_from('lag',(('t33',la),('t34',lb)))
    ma=K.solve(TRAIN_MIX_A);mb=K.solve(TRAIN_MIX_B);mc=K.compile_from('mixed',(('t35',ma),('t36',mb)))
    E['results']['training']={'pair_a':safe(pa),'pair_b':safe(pb),'pair_compile':safe(pc),'lag_a':safe(la),'lag_b':safe(lb),'lag_compile':safe(lc),'mix_a':safe(ma),'mix_b':safe(mb),'mix_compile':safe(mc)}

    hidden={n:K.solve(w) for n,w in HIDDEN.items()};E['results']['hidden']={n:safe(r) for n,r in hidden.items()}
    hp=HIDDEN['heldout_pair_xor'];hm=HIDDEN['heldout_mixed_xor'];hl=HIDDEN['historical_access']
    warm_pair=K.solve(hp,compiled_key='pair',allow_acquisition=False);cold_pair=Kernel().solve(hp);zero_pair=Kernel().solve(hp,allow_acquisition=False)
    warm_mix=K.solve(hm,compiled_key='mixed',allow_acquisition=False);cold_mix=Kernel().solve(hm);zero_mix=Kernel().solve(hm,allow_acquisition=False)
    warm_lag=K.solve(hl,compiled_key='lag',allow_acquisition=False);cold_lag=Kernel().solve(hl);zero_lag=Kernel().solve(hl,allow_acquisition=False)
    ablated=Kernel().solve(hp,compiled_key='pair',allow_acquisition=False)
    E['results']['transfer']={k:safe(v) for k,v in locals().copy().items() if k in {'warm_pair','cold_pair','zero_pair','warm_mix','cold_mix','zero_mix','warm_lag','cold_lag','zero_lag','ablated'}}

    before=K.solve(ACTIVE);probe=K.select_probe(before,ACTIVE_POOL);chosen=ACTIVE_POOL[probe['selected_index']];revealed=active_oracle(chosen);after=K.solve(add_record(ACTIVE,chosen,revealed))
    E['results']['active']={'before':safe(before),'probe':safe(probe),'revealed':revealed,'after':safe(after)}
    contraction=K.contraction(HIDDEN['contraction'],hidden['contraction']);incomplete=K.solve(INCOMPLETE)
    E['results']['contraction']=safe(contraction);E['results']['incomplete']=safe(incomplete)

    G=E['gates']
    G['V1_all_hidden_worlds_verified']=all(r.get('status')=='VERIFIED' for r in hidden.values())
    G['V2_posthoc_minimum_classes_exact']=all(hidden[n].get('minimum_cost')==c for n,c in EXPECTED_COST.items())
    text=open(__file__.replace('run_v33.py','kernel.py')).read().lower();forbidden=('memory','relation','context','intervention','joint','quantum','symmetry','grain')
    G['V3_executable_vocabulary_pure']=all(x not in text for x in forbidden)
    G['V4_pair_schema_recurs_across_different_training_laws']=pc.get('status')=='VERIFIED' and pc.get('schema_count',0)>=1 and frontier_ops(pa)!=frontier_ops(pb)
    G['V5_compiled_pair_operator_is_wildcard']=pc.get('status')=='VERIFIED' and any('*' in repr(s) for s in pc.get('schemas',[]))
    train_ops=frontier_ops(pa)|frontier_ops(pb);held_ops=frontier_ops(cold_pair)
    G['V6_heldout_pair_law_operator_disjoint_from_training']=bool(held_ops) and held_ops.isdisjoint(train_ops)
    G['V7_warm_pair_cross_law_same_minimum_zero_acquisition']=warm_pair.get('status')=='VERIFIED' and warm_pair.get('minimum_cost')==cold_pair.get('minimum_cost') and warm_pair.get('acquisition_search_count')==0 and warm_pair.get('tested_candidate_count',10**9)<cold_pair.get('tested_candidate_count',0)
    G['V8_warm_mixed_cross_law_same_minimum_zero_acquisition']=warm_mix.get('status')=='VERIFIED' and warm_mix.get('minimum_cost')==cold_mix.get('minimum_cost') and warm_mix.get('acquisition_search_count')==0 and warm_mix.get('tested_candidate_count',10**9)<cold_mix.get('tested_candidate_count',0)
    G['V9_warm_lag_same_minimum_zero_acquisition']=warm_lag.get('status')=='VERIFIED' and warm_lag.get('minimum_cost')==cold_lag.get('minimum_cost') and warm_lag.get('acquisition_search_count')==0 and warm_lag.get('tested_candidate_count',10**9)<cold_lag.get('tested_candidate_count',0)
    G['V10_cold_zero_search_unknown']=all(x.get('status')=='UNKNOWN_DEVELOPMENT' for x in (zero_pair,zero_mix,zero_lag))
    G['V11_store_ablation_restores_unknown']=ablated.get('status')=='UNKNOWN_DEVELOPMENT'
    G['V12_noncanonical_frontier_preserved']=len(before.get('frontier',[]))>=2
    G['V13_probe_selected_without_oracle_and_discriminates']=probe.get('status')=='VERIFIED' and probe.get('prediction_groups',0)>=2
    G['V14_revealed_probe_contracts_frontier']=after.get('status')=='VERIFIED' and len(after.get('frontier',[]))<len(before.get('frontier',[]))
    G['V15_verified_contraction']=contraction.get('status')=='VERIFIED' and contraction.get('current_blocks')==4 and contraction.get('selected_blocks')==2 and contraction.get('contracted') is True
    G['V16_incomplete_authority_unknown']=incomplete.get('status')=='UNKNOWN_AUTHORITY'
    G['V17_semantic_labels_not_needed_for_shared_pair_structure']=all(hidden[n].get('minimum_cost')==[2,2,1,1,0] for n in ('context_style','action_style','joint_style'))
    E['full_pass']=all(G.values());E['verdict']='VERIFIED_CROSS_LAW_STRUCTURAL_META_COMPILATION_AND_ACTIVE_DEVELOPMENT_V33' if E['full_pass'] else 'META_DEVELOPMENT_V33_RESIDUAL_EXPOSED'
    open('evidence.json','w').write(json.dumps(E,indent=2,sort_keys=True)+'\n');print(json.dumps(E,indent=2,sort_keys=True));return 0 if E['full_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
