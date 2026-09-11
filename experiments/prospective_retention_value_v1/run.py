#!/usr/bin/env python3
import hashlib,itertools,json,pathlib
ROOT=pathlib.Path(__file__).parent; N=48; CAP=3
S={
"broad_transient":{"d":0,"b":18,"g":12,"eps":list(range(1,17)),"dom":lambda t:t%4,"invalid":17},
"narrow_persistent":{"d":0,"b":13,"g":10,"eps":list(range(1,49,5)),"dom":lambda t:0},
"deep_broad":{"d":2,"b":31,"g":45,"eps":list(range(7,49,2)),"dom":lambda t:t%4},
"deep_transient":{"d":2,"b":25,"g":38,"eps":list(range(1,16,2)),"dom":lambda t:1,"invalid":16},
"late_huge":{"d":1,"b":44,"g":55,"eps":[3,12]+list(range(20,49)),"dom":lambda t:(t+1)%4},
"cheap_oneoff":{"d":0,"b":7,"g":2,"eps":[2,30],"dom":lambda t:2},
"early_invalid":{"d":1,"b":38,"g":25,"eps":list(range(1,13)),"dom":lambda t:t%3,"invalid":13},
"weak_to_strong":{"d":1,"b":27,"g":24,"eps":[4,11,18]+list(range(25,49,2)),"dom":lambda t:(t+2)%4}}

def future_value(name,t):
 s=S[name];return sum(s["b"]-1 for x in s["eps"] if x>t and x<s.get("invalid",10**9))
def score(policy,n,h,t):
 s=S[n]; uses=h[n]["uses"]; recent=sum(x>t-8 for x in h[n]["times"]); scope=len(h[n]["domains"])
 if policy=="oracle":return future_value(n,t)
 if policy=="amortization":return h[n]["saved"]-s["g"]-.5*h[n]["age"]
 if policy=="depth":return s["d"]
 if policy=="persistence":return h[n]["age"]
 if policy=="scope":return scope
 if policy=="geometry":return recent*s["b"]*(1+.35*scope)+.25*h[n]["saved"]-s["g"]-3*s["d"]
 if policy=="sham":return int(hashlib.sha256(f"{n}/{t}".encode()).hexdigest()[:8],16)
 raise ValueError(policy)
def simulate(policy,block=None,unlimited=False):
 h={n:{"uses":0,"times":[],"domains":set(),"saved":0,"age":0,"valid":True} for n in S}; kept=set();cost=0;rows=[]
 for t in range(1,N+1):
  for n,s in S.items():
   if t==s.get("invalid"):
    h[n]["valid"]=False
    if n in kept:kept.remove(n);cost+=2
   if h[n]["uses"]:h[n]["age"]+=1
  cost+=.5*len(kept)
  for n,s in S.items():
   if t in s["eps"] and h[n]["valid"]:
    cost+=2 # authority/verifier
    if n in kept and not(block and block[0]<=t<=block[1] and n==block[2]):cost+=1;h[n]["saved"]+=s["b"]-1
    else:cost+=s["b"]
    h[n]["uses"]+=1;h[n]["times"].append(t);h[n]["domains"].add(s["dom"](t))
  eligible=[n for n in S if h[n]["valid"] and h[n]["uses"]>=2]
  ranked=sorted(eligible,key=lambda n:(score(policy,n,h,t),n),reverse=True)
  new=set(ranked if unlimited else ranked[:CAP])
  for n in new-kept:cost+=S[n]["g"] if h[n]["uses"]==2 else 1
  kept=new;rows.append({"t":t,"cost":cost,"kept":sorted(kept)})
 return cost,rows,h
def oracle_dp():
 # Exact hindsight lower reference over every legal retained subset (≤ CAP).
 states={frozenset():0.0};uses={n:0 for n in S}
 for t in range(1,N+1):
  for n,s in S.items():
   if t in s["eps"] and t<s.get("invalid",10**9):uses[n]+=1
  eligible=[n for n,s in S.items() if uses[n]>=2 and t<s.get("invalid",10**9)]
  choices=[frozenset(x) for k in range(CAP+1) for x in itertools.combinations(eligible,k)]
  nxt={}
  for old,prior in states.items():
   valid_old={n for n in old if t<S[n].get("invalid",10**9)}
   base=prior+.5*len(valid_old)+2*sum(t==S[n].get("invalid") for n in old)
   for n,s in S.items():
    if t in s["eps"] and t<s.get("invalid",10**9):base+=2+(1 if n in valid_old else s["b"])
   for new in choices:
    transition=sum(S[n]["g"] if uses[n]==2 else 1 for n in new-valid_old)
    nxt[new]=min(nxt.get(new,float("inf")),base+transition)
  states=nxt
 return min(states.values())
def main():
 policies=("geometry","amortization","depth","persistence","scope","sham")
 runs={p:simulate(p) for p in policies};unlimited=simulate("geometry",unlimited=True)
 totals={p:runs[p][0] for p in policies};totals["oracle"]=oracle_dp();totals["unlimited"]=unlimited[0]
 # Frozen midpoint state; each criterion nominates one node. Force-remove it for
 # the remaining suffix while leaving all later policy decisions unchanged.
 base,rows,h=runs["geometry"];mid_kept=set(rows[23]["kept"])
 nominees={p:max(mid_kept,key=lambda n:(score(p,n,h,24),n)) for p in ("geometry","amortization","depth","persistence","scope")}
 penalties={p:simulate("geometry",block=(25,48,n))[0]-base for p,n in nominees.items()}
 scalars=[totals[p] for p in ("amortization","depth","persistence","scope")]
 gates={"beats_all_scalar_heuristics":totals["geometry"]<min(scalars),"better_than_sham":totals["geometry"]<totals["sham"],
  "non_oracle":totals["geometry"]>totals["oracle"],
 "highest_value_ablation_maximal":penalties["geometry"]>=max(penalties[p] for p in penalties if p!="geometry"),
 "scarcity_binding":all(len(x["kept"])<=CAP for x in rows),"revocation_executed":"early_invalid" not in rows[12]["kept"]}
 snap={"episodes":N,"capacity":CAP,"structures":S,"policies":policies,"decision_information":"past verified uses/domains/savings/age only"}
 enc=lambda x:json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
 ev={"verdict":"VERIFIED_PROSPECTIVE_RETENTION_VALUE" if all(gates.values()) else "NEGATIVE_OR_PARTIAL","classification":"FINITE_SCARCE_STATE_CAUSAL_PROSPECTIVE","totals":totals,"nominees":nominees,"ablation_penalties":penalties,"gates":gates,"snapshot_digest":hashlib.sha256(enc(snap).encode()).hexdigest(),"not_established":["natural-world forecasting","estimator learning","global optimality","open-ended retention"]}
 out=ROOT/"results";out.mkdir(exist_ok=True);(out/"snapshot.json").write_text(json.dumps(snap,indent=2,default=str)+"\n");(out/"evidence.json").write_text(json.dumps(ev,indent=2)+"\n");print(json.dumps(ev,indent=2))
if __name__=="__main__":main()
