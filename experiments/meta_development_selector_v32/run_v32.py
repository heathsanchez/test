from __future__ import annotations
import json
from kernel import Kernel
from basis import World
from challenge_pack import *

def safe(x):
    if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items() if not str(k).startswith('_')}
    if isinstance(x,(list,tuple)):return [safe(v) for v in x]
    return x

def add_record(w,r,y):return World(w.world_id+"_plus",w.records+(r,),w.targets+(int(y),),w.complete,w.current_signature)

def main():
    K=Kernel(); evidence={"experiment":"meta_development_selector_v32","frozen_core":"d7a47aad98e3915a12b9ee5cd1ef9801b7f2381d","results":{},"gates":{}}
    pa=K.solve(TRAIN_PAIR_A); pb=K.solve(TRAIN_PAIR_B); pc=K.compile_from("pair",(("w01",pa),("w02",pb)))
    la=K.solve(TRAIN_LAG_A); lb=K.solve(TRAIN_LAG_B); lc=K.compile_from("lag",(("w03",la),("w04",lb)))
    evidence["results"].update(pair_train_a=safe(pa),pair_train_b=safe(pb),pair_compile=safe(pc),lag_train_a=safe(la),lag_train_b=safe(lb),lag_compile=safe(lc))

    hidden={n:K.solve(w) for n,w in HIDDEN.items()}
    evidence["results"]["hidden"]={n:safe(r) for n,r in hidden.items()}

    held_pair=HIDDEN["joint_carrier"]
    warm_pair=K.solve(held_pair,compiled_key="pair",allow_acquisition=False)
    cold_zero_pair=Kernel().solve(held_pair,allow_acquisition=False)
    cold_full_pair=Kernel().solve(held_pair,allow_acquisition=True)
    warm_lag=K.solve(HIDDEN["historical_access"],compiled_key="lag",allow_acquisition=False)
    cold_zero_lag=Kernel().solve(HIDDEN["historical_access"],allow_acquisition=False)
    cold_full_lag=Kernel().solve(HIDDEN["historical_access"],allow_acquisition=True)
    ab=Kernel(); ab_pair=ab.solve(held_pair,compiled_key="pair",allow_acquisition=False)
    evidence["results"].update(warm_pair=safe(warm_pair),cold_zero_pair=safe(cold_zero_pair),cold_full_pair=safe(cold_full_pair),warm_lag=safe(warm_lag),cold_zero_lag=safe(cold_zero_lag),cold_full_lag=safe(cold_full_lag),after_memory_ablation=safe(ab_pair))

    active0=K.solve(ACTIVE)
    sel=K.select_intervention(ACTIVE,active0,ACTIVE_POOL)
    chosen=ACTIVE_POOL[sel["selected_index"]]
    revealed=active_oracle(chosen)
    active1=K.solve(add_record(ACTIVE,chosen,revealed))
    evidence["results"].update(active_before=safe(active0),selected_encounter=safe(sel),revealed_consequence=revealed,active_after=safe(active1))

    contraction=K.contraction(HIDDEN["contraction"],hidden["contraction"])
    incomplete=K.solve(INCOMPLETE)
    evidence["results"].update(contraction=safe(contraction),incomplete=safe(incomplete))

    G=evidence["gates"]
    G["M1_same_frozen_kernel_solves_all_hidden_worlds"]=all(r.get("status")=="VERIFIED" for r in hidden.values())
    G["M2_hidden_structural_classes_match_posthoc_expectation"]=all(hidden[n].get("minimum_cost")==c for n,c in EXPECTED_COST.items())
    kernel_text=open(__file__.replace('run_v32.py','kernel.py')).read().lower()
    forbidden=("memory","relation","context","intervention","joint","quantum","symmetry","grain")
    G["M3_no_named_repair_classes_in_executable_kernel"]=all(x not in kernel_text for x in forbidden)
    G["M4_pair_development_compiles_only_after_recurrence"]=pc.get("status")=="VERIFIED" and pc.get("skeleton_count",0)>=1 and pc.get("provenance")==["w01","w02"]
    G["M5_lag_development_compiles_only_after_recurrence"]=lc.get("status")=="VERIFIED" and lc.get("skeleton_count",0)>=1 and lc.get("provenance")==["w03","w04"]
    G["M6_warm_pair_replay_same_minimum_less_search"]=warm_pair.get("status")=="VERIFIED" and warm_pair.get("route")=="REUSE_COMPILED_DEVELOPMENT" and warm_pair.get("minimum_cost")==cold_full_pair.get("minimum_cost") and warm_pair.get("tested_candidate_count",10**18)<cold_full_pair.get("tested_candidate_count",0) and warm_pair.get("acquisition_search_count")==0
    G["M7_warm_lag_replay_same_minimum_less_search"]=warm_lag.get("status")=="VERIFIED" and warm_lag.get("minimum_cost")==cold_full_lag.get("minimum_cost") and warm_lag.get("tested_candidate_count",10**18)<cold_full_lag.get("tested_candidate_count",0) and warm_lag.get("acquisition_search_count")==0
    G["M8_cold_zero_search_without_compiled_memory_unknown"]=cold_zero_pair.get("status")=="UNKNOWN_DEVELOPMENT" and cold_zero_lag.get("status")=="UNKNOWN_DEVELOPMENT"
    G["M9_developmental_memory_ablation_restores_unknown"]=ab_pair.get("status")=="UNKNOWN_DEVELOPMENT"
    G["M10_noncanonical_frontier_preserved"]=active0.get("status")=="VERIFIED" and len(active0.get("frontier",[]))>=2
    G["M11_selected_encounter_discriminates_without_oracle_preuse"]=sel.get("status")=="VERIFIED" and sel.get("prediction_groups",0)>=2
    G["M12_revealed_encounter_strictly_contracts_frontier"]=active1.get("status")=="VERIFIED" and len(active1.get("frontier",[]))<len(active0.get("frontier",[]))
    G["M13_consequence_preserving_contraction"]=contraction.get("status")=="VERIFIED" and contraction.get("contracted") is True and contraction.get("current_blocks")==4 and contraction.get("selected_blocks")==2
    G["M14_incomplete_authority_stays_unknown"]=incomplete.get("status")=="UNKNOWN_AUTHORITY"
    pair_names=("context_conditioned","intervention_conditioned","joint_carrier")
    G["M15_semantically_different_axes_collapse_to_same_generic_structure"]=all(hidden[n].get("minimum_cost")==[2,2,1,1,0] for n in pair_names)
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]="VERIFIED_OBSTRUCTION_DIRECTED_META_DEVELOPMENT_SELECTION_AND_COMPILED_SELF_REPAIR" if evidence["full_pass"] else "META_DEVELOPMENT_V32_RESIDUAL_EXPOSED"
    open("evidence.json","w").write(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True))
    return 0 if evidence["full_pass"] else 1
if __name__=="__main__":raise SystemExit(main())
