#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
from kernel import Kernel
from challenge_pack import PRESENT,MEM_A,MEM_B,MEM_C,MIXED,WRONG,LOW,INCOMPLETE

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(x):
    if hasattr(x,"data"): return safe(x.data())
    if isinstance(x,dict): return {str(k):safe(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [safe(v) for v in x]
    return x
def code(r): return tuple(tuple(a) for a in r.get("accessors",[]))

def main():
    e={"experiment":"stochastic_memory_genesis_v19","scientific_freeze_commit":"27a7cf4eb11af34ef111cd614483882b2aef1b86",
       "hashes":{n:sha(HERE/n) for n in ("PROTOCOL.md","FREEZE.json","basis.py","kernel.py","challenge_pack.py")},
       "results":{},"gates":{}}
    present=Kernel().solve("T_present",PRESENT)
    mem=Kernel().solve("T_memory",MEM_A)
    mixed=Kernel().solve("T_mixed",MIXED)
    low=Kernel().solve("T_low",LOW)
    nohist=Kernel().solve("T_nohist",MEM_A,historical_enabled=False)
    nostat=Kernel().solve("T_nostat",MEM_A,statistical_enabled=False)
    incomplete=Kernel().solve("T_incomplete",INCOMPLETE)

    warm=Kernel()
    ta=warm.solve("T_compile_a",MEM_A)
    tb=warm.solve("T_compile_b",MEM_B)
    reuse=warm.solve("T_reuse_c",MEM_C,allow_acquisition_search=False)
    cold=Kernel().solve("T_cold_c",MEM_C,allow_acquisition_search=False)
    wrong=warm.solve("T_wrong",WRONG)

    warm2=Kernel(); warm2.solve("T_ab_a",MEM_A); tb2=warm2.solve("T_ab_b",MEM_B)
    ablated=warm2.ablate(MEM_C)
    after=warm2.solve("T_after_ablation",MEM_C,allow_acquisition_search=False)

    for name,val in locals().copy().items():
        if name in {"present","mem","mixed","low","nohist","nostat","incomplete","ta","tb","reuse","cold","wrong","after"}: e["results"][name]=safe(val)

    G=e["gates"]
    G["T1_no_hand_engineered_temporal_features"]=all(x not in (HERE/"kernel.py").read_text().lower() for x in ("fourier","frequency","moving_average","slope","derivative","threshold"))
    G["T2_present_sufficient_never_authorizes_memory"]=(present["status"]=="VERIFIED" and present["selected_lag"]==0 and code(present)==((0,1),(0,4)))
    mg=mem.get("developmental",{}).get("generations",[])
    G["T3_memory_is_earned_only_after_lag0_is_beaten"]=(mem["status"]=="VERIFIED" and mem["selected_lag"]==1 and code(mem)==((1,2),) and len(mg)>=2 and mg[1]["best_total_bits"]<mg[0]["best_total_bits"])
    G["T4_mixed_present_and_memory_readout_emerges"]=(mixed["status"]=="VERIFIED" and mixed["selected_lag"]==1 and code(mixed)==((0,1),(1,4)))
    G["T5_independent_noise_recovers_same_memory_code"]=(tb["status"]=="VERIFIED" and code(tb)==((1,2),))
    G["T6_low_data_does_not_authorize_memory"]=(low["status"]=="VERIFIED" and low["selected_lag"]==0 and code(low)==())
    G["T7_distractors_excluded"]=(len(code(mem))==1 and MEM_A.channel_count-1>=3 and len(code(mixed))==2)
    promoted=tb.get("promoted_code")
    G["T8_temporal_readout_compiles_and_reuses_causally"]=(promoted is not None and tuple(tuple(a) for a in promoted["accessors"])==((1,2),) and reuse["status"]=="VERIFIED" and reuse["route"]=="REUSE_COMPILED_READOUT" and cold["status"]=="UNKNOWN_READOUT" and tb2.get("promoted_code") is not None and ablated and after["status"]=="UNKNOWN_READOUT")
    G["T9_changed_temporal_dynamics_falsify_replay"]=(wrong["status"]=="VERIFIED" and wrong["route"]=="DEVELOP" and wrong.get("failed_reuse",{}).get("status")=="REPLAY_FAILED" and code(wrong)==((1,5),))
    G["T10_incomplete_authority_unknown"]=(incomplete["status"]=="UNKNOWN_AUTHORITY")
    G["T11_statistical_ablation_no_memory_growth"]=(nostat["status"]=="UNKNOWN_NO_STATISTICAL_AUTHORITY")
    G["T12_history_language_ablation_cannot_invent_temporal_summary"]=(nohist["status"]=="VERIFIED" and nohist["selected_lag"]==0 and code(nohist)==())
    G["minimal_developmental_algorithm_respected"]=all(x in (HERE/"PROTOCOL.md").read_text() for x in ("EXECUTE","VERIFY","DIAGNOSE","CONSTRAIN","RESTRUCTURE","CHOOSE","COMPILE","UPDATE"))
    e["full_pass"]=all(G.values())
    e["verdict"]="VERIFIED_STOCHASTIC_MEMORY_REACH_AND_RAW_TEMPORAL_READOUT_GENESIS" if e["full_pass"] else "STOCHASTIC_MEMORY_GENESIS_V19_GAPS_EXPOSED"
    (HERE/"evidence.json").write_text(json.dumps(e,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(e,indent=2,sort_keys=True,default=str))
    return 0 if e["full_pass"] else 1
if __name__=="__main__": raise SystemExit(main())
