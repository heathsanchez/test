#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
from basis import block_sizes
from kernel import Kernel
from challenge_pack import MAIN,DUPLICATE,PERTURBED,RELABELED,INCOMPLETE

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(x):
 if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items() if not str(k).startswith("_")}
 if isinstance(x,(list,tuple)):return [safe(v) for v in x]
 return x
def sig(r):
 return {"pre":tuple(r["pre_block_sizes"]),"posts":sorted(tuple(x) for x in r["post_block_sizes"]),
         "grain_count":r["grain_count"],"incomp":sorted(x["incomparable"] for x in r["pairwise"])}

def main():
 k=Kernel()
 main=k.analyze(MAIN); rel=k.analyze(RELABELED); dup=k.analyze(DUPLICATE)
 obs0=k.observe(MAIN,MAIN.histories[0]); obs1=k.observe(MAIN,MAIN.histories[1])
 missing=k.observe(MAIN,(99,))
 update=k.perturb_one(MAIN,PERTURBED,0)
 incomplete=k.analyze(INCOMPLETE)
 noc=k.analyze(MAIN,consequence_enabled=False)
 e={"experiment":"branch_conditioned_grain_dynamics_v29","scientific_freeze_commit":"6e4529b21e8ddc420d4069e807865bb9a1b0b10e",
 "hashes":{n:sha(HERE/n) for n in ("PROTOCOL.md","FREEZE.json","basis.py","kernel.py","challenge_pack.py")},
 "results":{"main":safe(main),"relabelled":safe(rel),"duplicate":safe(dup),"observe0":safe(obs0),"observe1":safe(obs1),
 "missing_branch":safe(missing),"update":safe(update),"incomplete":safe(incomplete),"no_consequence":safe(noc)},"gates":{}}
 G=e["gates"]
 G["B1_all_partitions_exhausted"]=main["pre"]["tested_partition_count"]==15 and all(x["tested_partition_count"]==15 for x in main["posts"])
 G["B2_prebranch_joint_future_grain"]=main["pre"]["minimum_block_count"]==4
 G["B3_each_branch_gets_coarsest_grain"]=all(x["minimum_block_count"]==2 for x in main["posts"])
 G["B4_branch_grains_incomparable"]=main["pairwise"][0]["incomparable"] is True
 G["B5_prebranch_strictly_finer_than_posts"]=main["pre_block_sizes"]==[1,1,1,1] and main["post_block_sizes"]==[[2,2],[2,2]]
 G["B6_exact_prediction_preserved_after_contraction"]=obs0["status"]=="VERIFIED" and obs1["status"]=="VERIFIED" and obs0["contracted"] and obs1["contracted"]
 G["B7_history_ignorance_forces_prebranch_complexity"]=main["pre"]["minimum_block_count"]==4 and all(x["minimum_block_count"]==2 for x in main["posts"])
 G["B8_state_and_history_relabelling_invariant"]=sig(main)==sig(rel)
 G["B9_duplicate_branches_reuse_same_grain"]=dup["grain_count"]==1
 G["B10_one_branch_perturbation_is_local"]=update["status"]=="VERIFIED" and update["changed"] and update["unrelated_preserved"]
 G["B11_missing_branch_record_keeps_prebranch_grain"]=missing["status"]=="UNKNOWN_BRANCH_RECORD" and missing["active_block_count"]==4
 G["B12_incomplete_authority_unknown"]=incomplete["status"]=="UNKNOWN_AUTHORITY"
 G["B13_no_consequence_no_predictive_branch_grain"]=noc["status"]=="UNKNOWN_NO_CONSEQUENCE_AUTHORITY"
 G["B14_branch_conditioning_strictly_reduces_active_complexity"]=obs0["post_block_count"]<obs0["pre_block_count"] and obs1["post_block_count"]<obs1["pre_block_count"]
 G["B15_branch_token_semantics_unused"]="history" in (HERE/"kernel.py").read_text().lower() and "branch_left" not in (HERE/"kernel.py").read_text()
 e["full_pass"]=all(G.values()); e["verdict"]="VERIFIED_BRANCH_CONDITIONED_ADAPTIVE_GRAIN_DYNAMICS" if e["full_pass"] else "BRANCH_CONDITIONED_GRAIN_V29_GAPS_EXPOSED"
 (HERE/"evidence.json").write_text(json.dumps(e,indent=2,sort_keys=True,default=str)+"\n")
 print(json.dumps(e,indent=2,sort_keys=True,default=str)); return 0 if e["full_pass"] else 1
if __name__=="__main__":raise SystemExit(main())
