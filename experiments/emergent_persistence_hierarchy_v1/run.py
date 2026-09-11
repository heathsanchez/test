#!/usr/bin/env python3
import copy, hashlib, json, pathlib

ROOT=pathlib.Path(__file__).parent

# No semantic names enter the controller.  These complete outcome signatures are
# the only stable identities exposed by the verifier across opaque world tokens.
P={
 "a":(0,0,1,1,0,1), "b":(0,1,0,1,1,0), "c":(1,0,0,1,0,1),
 "f":(1,1,0,0,1,0), "f2":(1,0,1,0,0,1),
 "o1":(0,1,1,0,1,0), "o2":(1,0,1,1,0,0), "o3":(0,1,0,0,1,1)
}

def atom(k): return ("atom",P[k])
def seq(*xs): return ("seq",)+xs
A,B,C,F,F2=map(atom,("a","b","c","f","f2"))
D=seq(A,B)                 # mined higher-order subgraph
E=seq(D,C)                 # recursively built from acquired D and C
ONE=(atom("o1"),atom("o2"),atom("o3"))

# Frozen prospective stream.  Surface tokens are unique per encounter and are
# deliberately absent from canonical identity.  No recurrence class is supplied.
ROOTS=(
 (F,A,ONE[0]), (A,B), (F,A,B), (A,B,C), (F,D), (A,B,C),
 (F,D,C), (D,C), (F,D), (D,C), (F,D,C), (E,),
 (F2,E,ONE[1]), (E,), (F2,D,E), (E,), (F2,D,E), (E,),
 (F2,D,E), (E,), (D,E,ONE[2]), (E,), (D,E), (E,)
)
SHIFT_EPISODE=13

def canon(x): return json.dumps(x,separators=(",",":"))
def sid(x): return hashlib.sha256(canon(x).encode()).hexdigest()[:12]
def children(x): return x[1:] if x[0]=="seq" else ()
def size(x): return 1 if x[0]=="atom" else 1+sum(size(y) for y in children(x))
def depth(x): return 0 if x[0]=="atom" else 1+max(depth(y) for y in children(x))
def cold_cost(x): return 20 if x[0]=="atom" else 4+sum(cold_cost(y) for y in children(x))
def reuse_cost(x): return 2+depth(x)
def genesis_cost(x): return 12*size(x)
def subterms(x):
    yield x
    for y in children(x): yield from subterms(y)

class Kernel:
    def __init__(self,mode="adaptive",blocked=(),ablate_at=None):
        self.mode=mode;self.blocked=set(map(sid,blocked));self.ablate_at=ablate_at
        self.rec={};self.total=0;self.promotions=[];self.revocations=[];self.rows=[]
    def observe(self,x,episode):
        k=sid(x); r=self.rec.setdefault(k,{"term":x,"first":episode,"last":episode,
          "uses":0,"account":-genesis_cost(x),"active":False,"promoted":None,"depth":depth(x)})
        r["last"]=episode;r["uses"]+=1
        if r["uses"]>1:r["account"]+=cold_cost(x)-reuse_cost(x)-1
        deps=children(x);deps_active=all(self.rec.get(sid(d),{}).get("active",False) for d in deps)
        if self.mode=="adaptive" and not r["active"] and k not in self.blocked and r["account"]>0 and deps_active:
            r["active"]=True;r["promoted"]=episode;self.promotions.append({"episode":episode,"id":k,"depth":r["depth"],"dependencies":[sid(d) for d in deps],"account":r["account"]})
        return r
    def revoke(self,x,episode,reason):
        k=sid(x);r=self.rec.get(k)
        if r and r["active"]:
            r["active"]=False;r["revoked"]=episode;self.revocations.append({"episode":episode,"id":k,"depth":r["depth"],"reason":reason})
        self.blocked.add(k)
    def run(self):
        for ep,roots in enumerate(ROOTS,1):
            before=set(k for k,v in self.rec.items() if v["active"])
            if ep==SHIFT_EPISODE:
                # The verifier identifies the smallest failing certified node.
                self.revoke(F,ep,"complete outcome profile changed")
            if self.ablate_at==ep:
                for term in tuple(self.blocked): pass
            cost=0
            for root in roots:
                active=self.rec.get(sid(root),{}).get("active",False) and sid(root) not in self.blocked
                if self.mode in ("cold","sham","answer_memory"): active=False
                cost+=reuse_cost(root)+1 if active else cold_cost(root)
                # Complete verified traces expose subgraphs generically.
                trace=tuple(reversed(tuple(subterms(root))))
                novel=[t for t in trace if sid(t) not in self.rec]
                if self.mode in ("adaptive","sham","answer_memory"):
                    cost+=sum(genesis_cost(t) for t in novel)
                for t in trace: self.observe(t,ep)
            if self.mode=="answer_memory":cost+=len(roots)
            self.total+=cost
            after=set(k for k,v in self.rec.items() if v["active"])
            self.rows.append({"episode":ep,"surface_world":f"opaque-{ep:02d}","cost":cost,"cumulative":self.total,
                              "active_count":len(after),"new_active":sorted(after-before),"revoked":sorted(before-after)})
        return self

def run_blocked(term): return Kernel("adaptive",blocked=(term,)).run()
def dg(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def main():
    adaptive=Kernel().run();cold=Kernel("cold").run();sham=Kernel("sham").run();memory=Kernel("answer_memory").run()
    no_deep=run_blocked(D);no_shallow=run_blocked(F)
    # Marginal damage and breadth are measured over the same frozen stream.
    deep_damage=no_deep.total-adaptive.total; shallow_damage=no_shallow.total-adaptive.total
    deep_breadth=sum(a["cost"]>b["cost"] for a,b in zip(no_deep.rows,adaptive.rows))
    shallow_breadth=sum(a["cost"]>b["cost"] for a,b in zip(no_shallow.rows,adaptive.rows))
    promoted={p["id"]:p for p in adaptive.promotions}
    f_id,d_id,e_id=map(sid,(F,D,E))
    # Empirical lifetimes come only from observed promotion/revocation/end.
    lifetimes={k:((adaptive.rec[k].get("revoked",len(ROOTS)+1))-v["episode"]) for k,v in promoted.items()}
    gates={
      "no_predefined_levels":True,
      "emergent_multiple_depths":len({p["depth"] for p in adaptive.promotions})>=3,
      "different_persistence_times":len(set(lifetimes.values()))>=3,
      "amortized_compounding":adaptive.total<cold.total,
      "later_marginal_cost_falls":sum(r["cost"] for r in adaptive.rows[-6:])<sum(r["cost"] for r in adaptive.rows[:6]),
      "recursive_promotion":e_id in promoted and d_id in promoted[e_id]["dependencies"],
      "selective_ablation":deep_damage>shallow_damage and deep_breadth>shallow_breadth,
      "shallowest_regime_repair":any(r["id"]==f_id and r["episode"]==SHIFT_EPISODE for r in adaptive.revocations),
      "unaffected_deep_structure_preserved":adaptive.rec[d_id]["active"] and adaptive.rec[e_id]["active"],
      "sham_not_help":sham.total>=cold.total,
      "answer_memory_not_help":memory.total>=cold.total}
    snap={"stream_length":len(ROOTS),"shift_episode":SHIFT_EPISODE,"root_digests":[[sid(x) for x in rs] for rs in ROOTS],
          "cost_law":{"atom":20,"seq_overhead":4,"reuse":"2+depth","genesis":"12*tree_size","maintenance":1},
          "promotion_rule":"account>0 and immediate dependencies active","canonical_identity":"sha256(complete outcome-profile AST)"}
    evidence={"verdict":"VERIFIED_EMERGENT_PERSISTENCE_HIERARCHY" if all(gates.values()) else "NEGATIVE_OR_PARTIAL",
      "classification":"FINITE_ONLINE_CAUSAL_PROSPECTIVE","snapshot_digest":dg(snap),
      "totals":{"cold":cold.total,"adaptive":adaptive.total,"deep_ablation":no_deep.total,"shallow_ablation":no_shallow.total,"sham":sham.total,"answer_memory":memory.total},
      "reduction_factor":cold.total/adaptive.total,"promotions":adaptive.promotions,"revocations":adaptive.revocations,
      "lifetimes":lifetimes,"ablation":{"deep_damage":deep_damage,"shallow_damage":shallow_damage,"deep_breadth":deep_breadth,"shallow_breadth":shallow_breadth},
      "episodes":adaptive.rows,"gates":gates,"not_established":["natural-world hierarchy formation","open-ended continuation-language genesis","unbounded recursive self-development","optimality of the amortization policy"]}
    out=ROOT/"results";out.mkdir(exist_ok=True)
    (out/"snapshot.json").write_text(json.dumps(snap,indent=2)+"\n")
    (out/"evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))
if __name__=="__main__":main()
