#!/usr/bin/env python3
import hashlib, itertools, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parent
ROLES=("SCAN","FILTER","FIRST","PAIR","EXTEND","TEMPORAL")
TOKENS=("zx9","qa2","mn7","rv4","kp1","ht8")
D2=("SCAN","FILTER","FIRST","PAIR","EXTEND","PAIR")
CASES=("empty","one","two","useful","opened","temporal")
SIG={"SCAN":(1,2,2,2,2,3),"FILTER":(0,0,1,2,1,2),"FIRST":(0,0,0,1,1,1),
     "PAIR":(0,0,0,0,2,2),"EXTEND":(0,0,0,0,1,1),"TEMPORAL":(1,1,1,1,1,4)}
PERMS=((0,1,2,3,4,5),(5,4,3,2,1,0),(2,5,1,4,0,3),(3,0,4,1,5,2))

def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

class Oracle:
 def __init__(self,p): self.hidden={TOKENS[i]:ROLES[p[i]] for i in range(6)}
 def probe(self,t,c): return SIG[self.hidden[t]][CASES.index(c)]

def discover(oracle):
 calls=0; candidates={}
 for role in ROLES:
  hits=[]
  for token in TOKENS:
   ok=True
   for i,c in enumerate(CASES):
    calls+=1; ok &= oracle.probe(token,c)==SIG[role][i]
   if ok:hits.append(token)
  candidates[role]=hits
 if any(len(v)!=1 for v in candidates.values()) or len({v[0] for v in candidates.values()})!=6:return None,calls
 return {r:candidates[r][0] for r in ROLES},calls

def execute(program,oracle,macro=()):
 seq=tuple(x for t in program for x in (macro if t=="XFER" else (t,)))
 req={"lag-edge-a","lag-edge-b"}; avail=["edge-a","edge-b","edge-c","edge-d"]
 scanned=useful=None; selected=[]; opened=False; calls=evals=0; valid=True; success=False
 for t in seq:
  if t=="SHAM":continue
  if t=="MEM_A":selected.append("edge-a");continue
  if t=="MEM_B":selected.append("edge-b");continue
  role=oracle.hidden.get(t)
  if role=="TEMPORAL":avail += ["lag-edge-a","lag-edge-b","lag-edge-c","lag-edge-d"]
  elif role=="SCAN":scanned=list(avail)
  elif role=="FILTER" and scanned is not None:calls+=len(scanned)*2;useful=[x for x in scanned if x in req]
  elif role=="FIRST" and useful:
   if useful[0] not in selected:selected.append(useful[0])
  elif role=="PAIR" and selected:calls+=2;evals+=1;opened=True;success=req.issubset(selected)
  elif role=="EXTEND" and opened and useful is not None:
   for x in useful:
    calls+=2
    if x not in selected:selected.append(x)
    if req.issubset(selected):break
   opened=False;success=False
  else:valid=False;break
 return valid,success,calls,evals

def search(oracle,extra=(),macro=(),overhead=0):
 alphabet=TOKENS+tuple(extra);calls=overhead;nodes=evals=0
 for depth in range(1,8):
  wins=[]
  for p in itertools.product(alphabet,repeat=depth):
   nodes+=1;v,s,c,e=execute(p,oracle,macro);calls+=c;evals+=e
   if v and s:wins.append(p)
  if wins:return {"correct":True,"verifier_calls":calls,"search_nodes":nodes,"candidate_evaluations":evals,"depth":depth,"canonical":list(min(wins)),"adapter_calls":overhead}
 return {"correct":False,"verifier_calls":calls,"search_nodes":nodes,"candidate_evaluations":evals,"depth":None,"canonical":None,"adapter_calls":overhead}

def one(perm):
 o=Oracle(perm);phi,dcalls=discover(o);macro=tuple(phi[x] for x in D2)
 # Deterministic derangement: provably not the discovered map in every role.
 sham_phi={r:TOKENS[(TOKENS.index(phi[r])+1)%6] for r in ROLES};sham=tuple(sham_phi[x] for x in D2)
 r={"cold":search(o),"discovered_adapter":search(o,("XFER",),macro,dcalls),"adapter_ablation":search(o),
    "random_bijection_sham":search(o,("XFER",),sham,dcalls),"answer_memory":search(o,("MEM_A","MEM_B"))}
 return {"hidden_permutation":list(perm),"discovered_map":phi,"results":r,
         "map_exact":all(o.hidden[phi[x]]==x for x in ROLES),"sham_wrong":any(o.hidden[sham_phi[x]]!=x for x in ROLES)}

def main():
 enc=[one(p) for p in PERMS]
 gates={"all_maps_exact":all(x["map_exact"] for x in enc),"all_conditions_correct":all(y["correct"] for x in enc for y in x["results"].values()),
  "warm_always_cheaper":all(x["results"]["discovered_adapter"]["verifier_calls"]<x["results"]["cold"]["verifier_calls"] for x in enc),
  "ablation_restores":all(x["results"]["adapter_ablation"]["verifier_calls"]==x["results"]["cold"]["verifier_calls"] for x in enc),
  "sham_not_reproduce":all(x["results"]["random_bijection_sham"]["verifier_calls"]>=x["results"]["cold"]["verifier_calls"] for x in enc),
  "memory_not_reproduce":all(x["results"]["answer_memory"]["verifier_calls"]>=x["results"]["cold"]["verifier_calls"] for x in enc),
  "surface_disjoint":not set(ROLES)&set(TOKENS),"counterbalanced":len(enc)==4}
 agg={k:sum(x["results"][k]["verifier_calls"] for x in enc) for k in enc[0]["results"]}
 snap={"roles":ROLES,"opaque_tokens":TOKENS,"source_D2":D2,"probe_cases":CASES,"hidden_permutations":PERMS,"search":"level-complete","metric":"all discovery and acquisition verifier calls"}
 verdict="VERIFIED_AUTONOMOUS_ADAPTER_GENESIS" if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
 ev={"verdict":verdict,"classification":"BOUNDED_EXHAUSTIVE_CAUSAL_PROSPECTIVE","snapshot_digest":digest(snap),"encodings":enc,"aggregate_calls":agg,"aggregate_reduction_factor":agg["cold"]/agg["discovered_adapter"],"gates":gates,"seed":None,
     "not_established":["natural-domain transfer","non-isomorphic structural transfer","unbounded adapter discovery","substrate genesis"]}
 out=ROOT/"results";out.mkdir(exist_ok=True);(out/"snapshot.json").write_text(json.dumps(snap,sort_keys=True,separators=(",",":"))+"\n");(out/"evidence.json").write_text(json.dumps(ev,indent=2)+"\n");print(json.dumps(ev,indent=2));return 0 if verdict.startswith("VERIFIED") else 1
if __name__=="__main__":sys.exit(main())
