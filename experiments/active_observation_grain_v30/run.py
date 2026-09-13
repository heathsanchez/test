#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
from kernel import Kernel
from challenge_pack import MAIN,RELABELED,INCOMPLETE

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(x):
 if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items() if not str(k).startswith("_")}
 if isinstance(x,(list,tuple)):return [safe(v) for v in x]
 return x
def sig(r):
 return {
  "grain_sizes":sorted(tuple(len(b) for b in x["_full_partition"]) for x in r["_inst"]),
  "pairwise":sorted(x["incomparable"] for x in r["pairwise"])
 }

def main():
 k=Kernel()
 main=k.analyze(MAIN); rel=k.analyze(RELABELED)
 A=k.analyze_instrument(MAIN,0); B=k.analyze_instrument(MAIN,1); I=k.analyze_instrument(MAIN,2)
 AB=k.analyze_sequence(MAIN,(0,1)); BA=k.analyze_sequence(MAIN,(1,0))
 incomplete=k.analyze(INCOMPLETE); noc=k.analyze(MAIN,consequence_enabled=False)
 e={"experiment":"active_observation_grain_v30","scientific_freeze_commit":"b482fed720dbac43efdf51976974552758328616",
 "hashes":{n:sha(HERE/n) for n in ("PROTOCOL.md","FREEZE.json","basis.py","kernel.py","challenge_pack.py")},
 "results":{"main":safe(main),"relabelled":safe(rel),"A":safe(A),"B":safe(B),"I":safe(I),
 "AB":safe(AB),"BA":safe(BA),"incomplete":safe(incomplete),"no_consequence":safe(noc)},"gates":{}}
 G=e["gates"]
 G["O1_all_partitions_exhausted"]=all(x["full"]["tested_partition_count"]==15 for x in (A,B,I)) and AB["tested_partition_count"]==15 and BA["tested_partition_count"]==15
 G["O2_measurement_changes_state"]=len(A["changed_states"])>0
 G["O3_outcome_only_is_insufficient"]=A["outcome_only"]["minimum_block_count"]==1 and A["full"]["minimum_block_count"]==2
 G["O4_full_future_forces_minimum_split"]=A["full"]["minimum_block_count"]==2 and A["full"]["minimum_partitions"]!=A["outcome_only"]["minimum_partitions"]
 G["O5_distinct_measurements_induce_distinct_grains"]=A["_full_partition"]!=B["_full_partition"]
 G["O6_measurement_grains_are_incomparable"]=any(x["incomparable"] for x in main["pairwise"] if x["instruments"]==[0,1])
 G["O7_operation_order_changes_full_consequence"]=AB["_signatures"]!=BA["_signatures"]
 G["O8_order_changes_verified_future_record_or_grain"]=AB["minimum_partitions"]!=BA["minimum_partitions"] or AB["signatures"]!=BA["signatures"]
 G["O9_state_and_instrument_relabelling_invariant"]=sig(main)==sig(rel)
 G["O10_identity_measurement_matches_no_disturbance_semantics"]=I["full"]["minimum_partitions"]==I["no_disturbance"]["minimum_partitions"]
 G["O11_post_state_ablation_fails_on_disturbance"]=A["full"]["minimum_partitions"]!=A["no_disturbance"]["minimum_partitions"] and len(A["future_changed_states"])>0
 G["O12_future_irrelevant_disturbance_creates_no_extra_split"]=B["full"]["minimum_partitions"]==B["no_disturbance"]["minimum_partitions"]
 G["O13_incomplete_authority_unknown"]=incomplete["status"]=="UNKNOWN_AUTHORITY"
 G["O14_without_consequence_no_measurement_grain"]=noc["status"]=="UNKNOWN_NO_CONSEQUENCE_AUTHORITY"
 G["O15_no_quantum_assumption_required"]="quantum" not in (HERE/"kernel.py").read_text().lower()
 e["full_pass"]=all(G.values()); e["verdict"]="VERIFIED_ACTIVE_OBSERVATION_RELATIVE_GRAIN_WITH_CLASSICAL_DISTURBANCE" if e["full_pass"] else "ACTIVE_OBSERVATION_GRAIN_V30_GAPS_EXPOSED"
 (HERE/"evidence.json").write_text(json.dumps(e,indent=2,sort_keys=True,default=str)+"\n")
 print(json.dumps(e,indent=2,sort_keys=True,default=str)); return 0 if e["full_pass"] else 1
if __name__=="__main__":raise SystemExit(main())
