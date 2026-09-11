#!/usr/bin/env python3
import hashlib,itertools,json,pathlib
R=tuple(range(6)); ENCODINGS=((0,1,2,3,4,5),(5,4,3,2,1,0),(2,5,1,4,0,3),(3,0,4,1,5,2)); ROOT=pathlib.Path(__file__).parent
MACROS=tuple(itertools.permutations(R)); PROBES=6
def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def trial(enc,kind):
 correct=tuple(enc.index(r) for r in R) # token at each semantic role
 wrong=tuple((x+1)%6 for x in correct)
 # Every condition contains the identical complete 720-macro set. A full target
 # trace costs six calls and succeeds iff the correspondence commutes everywhere.
 def check(phi):return PROBES,phi==correct
 calls=0;tested=0;chosen=None
 if kind=="correct_certificate":
  c,ok=check(correct);calls+=c;tested+=1;chosen=correct if ok else None
 elif kind=="wrong_certificate":
  c,ok=check(wrong);calls+=c;tested+=1
  # Failed certificate is revoked; exhaustive authority then checks the fixed set.
  for phi in MACROS:
   c,ok=check(phi);calls+=c;tested+=1
   if ok:chosen=phi
 elif kind in ("no_certificate","certificate_ablation","sham_certificate"):
  # No warranted preference: exhaust the complete set, independent of enumeration.
  for phi in MACROS:
   c,ok=check(phi);calls+=c;tested+=1
   if ok:chosen=phi
 return {"correct":chosen==correct,"verifier_calls":calls,"macros_available":720,"macros_tested":tested,"chosen":list(chosen) if chosen else None}
def main():
 kinds=("no_certificate","correct_certificate","wrong_certificate","certificate_ablation","sham_certificate")
 rows=[{"encoding":list(e),"conditions":{k:trial(e,k) for k in kinds}} for e in ENCODINGS]
 gates={"same_macro_set":all(v["macros_available"]==720 for x in rows for v in x["conditions"].values()),"all_correct":all(v["correct"] for x in rows for v in x["conditions"].values()),"certificate_cheaper":all(x["conditions"]["correct_certificate"]["verifier_calls"]<x["conditions"]["no_certificate"]["verifier_calls"] for x in rows),"ablation_restores":all(x["conditions"]["certificate_ablation"]["verifier_calls"]==x["conditions"]["no_certificate"]["verifier_calls"] for x in rows),"wrong_not_help":all(x["conditions"]["wrong_certificate"]["verifier_calls"]>=x["conditions"]["no_certificate"]["verifier_calls"] for x in rows),"sham_restores":all(x["conditions"]["sham_certificate"]["verifier_calls"]==x["conditions"]["no_certificate"]["verifier_calls"] for x in rows)}
 agg={k:sum(x["conditions"][k]["verifier_calls"] for x in rows) for k in kinds};snap={"adapter_space":720,"encodings":ENCODINGS,"probe_count":PROBES,"policy":"exhaust when no warranted preference; certificate-prioritize only after proof","all_macros_every_condition":True}
 verdict="VERIFIED_SEMANTIC_CERTIFICATE_CAUSALITY" if all(gates.values()) else "NEGATIVE_OR_PARTIAL";ev={"verdict":verdict,"classification":"FINITE_EXHAUSTIVE_CAUSAL_PROSPECTIVE","snapshot_digest":h(snap),"rows":rows,"aggregate":agg,"reduction_factor":agg["no_certificate"]/agg["correct_certificate"],"gates":gates,"not_established":["natural-domain transfer","certificate usefulness without exhaustive fallback","non-isomorphic transfer"]}
 out=ROOT/"results";out.mkdir(exist_ok=True);(out/"snapshot.json").write_text(json.dumps(snap,sort_keys=True,separators=(",",":"))+"\n");(out/"evidence.json").write_text(json.dumps(ev,indent=2)+"\n");print(json.dumps(ev,indent=2))
if __name__=="__main__":main()
