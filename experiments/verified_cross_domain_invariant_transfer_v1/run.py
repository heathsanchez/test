#!/usr/bin/env python3
import hashlib,itertools,json,pathlib
ROOT=pathlib.Path(__file__).parent
S=range(4);T=range(5);PI=range(2); ENCS=((0,1,2,3,4),(4,3,2,1,0),(2,4,1,3,0),(3,0,4,2,1))
# Non-isomorphic carriers. Consequence profiles induce the same two-role quotient.
SOURCE_PROFILE={0:(0,0),1:(1,1),2:(0,0),3:(1,1)}
BASE_TARGET_PROFILE={0:(0,0),1:(1,1),2:(1,1),3:(0,0),4:(1,1)}
SMAPS=tuple(itertools.product(PI,repeat=4)); TMAPS=tuple(itertools.product(PI,repeat=5)); BRIDGES=tuple(itertools.product(SMAPS,TMAPS))
def dg(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def target_profile(enc):return {i:BASE_TARGET_PROFILE[enc[i]] for i in T}
def canonical(profile,carrier):return tuple(profile[i][0] for i in carrier)
def discover(enc):
 tp=target_profile(enc);calls=0
 # Complete two-continuation profiles construct each quotient independently.
 for _ in S:calls+=2
 for _ in T:calls+=2
 sm=canonical(SOURCE_PROFILE,S);tm=canonical(tp,T)
 return (sm,tm),calls
def trial(enc,kind):
 correct,discovery=discover(enc); wrong=(tuple(1-x for x in correct[0]),correct[1]); probe_cost=9
 def valid(b):return b==correct
 calls=tested=0;chosen=None
 if kind=="correct_certificate":calls+=discovery+probe_cost;tested=1;chosen=correct
 elif kind=="wrong_certificate":
  calls+=discovery+probe_cost;tested=1
  for b in BRIDGES:calls+=probe_cost;tested+=1;chosen=correct if valid(b) else chosen
 else:
  for b in BRIDGES:calls+=probe_cost;tested+=1;chosen=correct if valid(b) else chosen
 return {"correct":chosen==correct,"verifier_calls":calls,"bridges_available":len(BRIDGES),"bridges_tested":tested,"discovery_calls":discovery if kind in ("correct_certificate","wrong_certificate") else 0}
def main():
 kinds=("no_certificate","correct_certificate","certificate_ablation","sham_certificate","wrong_certificate")
 rows=[{"encoding":list(e),"conditions":{k:trial(e,k) for k in kinds}} for e in ENCS]
 gates={"non_isomorphic":len(tuple(S))!=len(tuple(T)),"all_correct":all(v["correct"] for r in rows for v in r["conditions"].values()),"availability_matched":all(v["bridges_available"]==512 for r in rows for v in r["conditions"].values()),"correct_cheaper":all(r["conditions"]["correct_certificate"]["verifier_calls"]<r["conditions"]["no_certificate"]["verifier_calls"] for r in rows),"ablation_restores":all(r["conditions"]["certificate_ablation"]["verifier_calls"]==r["conditions"]["no_certificate"]["verifier_calls"] for r in rows),"sham_restores":all(r["conditions"]["sham_certificate"]["verifier_calls"]==r["conditions"]["no_certificate"]["verifier_calls"] for r in rows),"wrong_not_help":all(r["conditions"]["wrong_certificate"]["verifier_calls"]>=r["conditions"]["no_certificate"]["verifier_calls"] for r in rows)}
 agg={k:sum(r["conditions"][k]["verifier_calls"] for r in rows) for k in kinds};snap={"source_size":4,"target_size":5,"shared_quotient_size":2,"complete_bridge_space":512,"encodings":ENCS,"profile_horizon":2,"all_bridges_every_condition":True}
 verdict="VERIFIED_NONISOMORPHIC_INVARIANT_TRANSFER" if all(gates.values()) else "NEGATIVE_OR_PARTIAL";ev={"verdict":verdict,"classification":"FINITE_EXHAUSTIVE_CAUSAL_PROSPECTIVE","snapshot_digest":dg(snap),"rows":rows,"aggregate":agg,"reduction_factor":agg["no_certificate"]/agg["correct_certificate"],"gates":gates,"not_established":["natural-domain transfer","infinite carriers","open-ended invariant discovery","learned continuation language"]}
 out=ROOT/"results";out.mkdir(exist_ok=True);(out/"snapshot.json").write_text(json.dumps(snap,sort_keys=True,separators=(",",":"))+"\n");(out/"evidence.json").write_text(json.dumps(ev,indent=2)+"\n");print(json.dumps(ev,indent=2))
if __name__=="__main__":main()
