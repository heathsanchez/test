#!/usr/bin/env python3
"""V54: extract the smallest exact rank law behind V53's source-free DAG.

V53 found, on the frozen prospective corpus, that every nonprogress/nonpositive-
budget protected return lies in a source-free DAG of height 4.  V54 does not
expand the corpus.  It asks what that rank actually depends on.

For every source-free V53 node
  (anchor, forced_bits, rho, nearest_center_id, nearest_radius, extra5)
we compute the exact elimination rank and search:
  * single-coordinate monotones;
  * smallest coordinate subset making rank functional;
  * lexicographic 2-coordinate monotones;
  * tiny integer linear potentials over local numeric features.

The purpose is theorem discovery: if the rank collapses to a tiny local
coordinate, that is the next universal Lean target.  If it needs full law
identity / unbounded data, emit that separator explicitly.

Bounded discovery only; no global Collatz claim.
"""
from __future__ import annotations
from collections import defaultdict, Counter
from contextlib import redirect_stdout
from itertools import combinations, product
import hashlib, io, json, math

with redirect_stdout(io.StringIO()):
    import collatz_crystal_nonpositive_budget_kernel_v53 as v53
    import collatz_crystal_nearest_centre_v45 as v45

# Rebuild exactly the source-free residual graph used by V53.
nodes=set()
succ=defaultdict(set)
for tr in v53.transitions:
    if not tr["src"]["residual"]:
        continue
    u=tr["src"]["key"]
    nodes.add(u); succ.setdefault(u,set())
    if tr["kind"]=="RESIDUAL":
        v=tr["dst"]["key"]
        nodes.add(v); succ[u].add(v); succ.setdefault(v,set())

rank,left,layers=v53.elimination_rank(nodes,succ)
assert not left
assert max(rank.values(),default=-1)==4

edges=[(u,v) for u in nodes for v in succ.get(u,())]
assert len(edges)==833

def radnum(r):
    return 10**9 if r=="INF" else int(r)

def v2(x):
    x=abs(int(x))
    if x==0: return 64
    return (x & -x).bit_length()-1

def center_data(cid):
    a,c=v45.id_center[cid]
    num,den=c
    return a,num,den

def feats(k):
    anchor,forced,rho,cid,rad,extra=k
    ca,num,den=center_data(cid)
    assert ca==anchor
    return {
      "anchor":anchor,
      "forced":forced,
      "rho":rho,
      "rho5":rho & 31,
      "rho6":rho & 63,
      "rho8":rho & 255,
      "center":cid,
      "radius":radnum(rad),
      "extra":extra,
      "extra_pop":int(extra).bit_count(),
      "extra_v2":v2(extra),
      "extra1_v2":v2(extra+1),
      "forced_minus_anchor":forced-anchor,
      "rho_v2":v2(rho),
      "rho1_v2":v2(rho+1),
      "center_num_v2":v2(num),
      "center_den_v2":v2(den),
      "center_num_mod32":num & 31,
      "center_den_mod32":den & 31,
    }

F={k:feats(k) for k in nodes}
field_names=["anchor","forced","rho","center","radius","extra"]

# Scalar monotonicity on every residual edge.
scalar={}
for name in F[next(iter(nodes))]:
    ds=[F[u][name]-F[v][name] for u,v in edges]
    scalar[name]={
      "strict_decrease":all(d>0 for d in ds),
      "nonincrease":all(d>=0 for d in ds),
      "strict_increase":all(d<0 for d in ds),
      "nondecrease":all(d<=0 for d in ds),
      "min_delta":min(ds),"max_delta":max(ds),
    }

# Smallest raw-key coordinate subset for which elimination rank is functional.
functional_subsets=[]
for sz in range(1,len(field_names)+1):
    for sub in combinations(field_names,sz):
        g={}
        bad=0
        for k in nodes:
            q=tuple(F[k][x] for x in sub)
            rr=rank[k]
            if q in g and g[q]!=rr:
                bad+=1; break
            g[q]=rr
        if not bad:
            functional_subsets.append({
              "fields":sub,"classes":len(g),
              "rank_hist":dict(sorted(Counter(g.values()).items()))
            })
    if functional_subsets:
        break

# Lexicographic candidates using compact/local features; orientation +1 means
# descending ordinary value, -1 means ascending ordinary value.
lex_names=["anchor","forced","radius","extra","extra_pop","extra_v2",
           "extra1_v2","rho5","rho6","rho_v2","rho1_v2",
           "forced_minus_anchor","center_num_mod32","center_den_mod32"]
lex=[]
for a,b in combinations(lex_names,2):
    for sa,sb in product((1,-1),repeat=2):
        ok=True
        for u,v in edges:
            U=(sa*F[u][a],sb*F[u][b])
            V=(sa*F[v][a],sb*F[v][b])
            if not (U>V):
                ok=False; break
        if ok:
            lex.append({"features":[a,b],"signs":[sa,sb]})

# Tiny linear potentials. Search sparse triples first, with coefficients in
# [-4,4]. A valid potential must drop by >=1 on all edges.
lin_names=["anchor","forced","radius","extra","extra_pop","extra_v2",
           "extra1_v2","rho5","rho_v2","rho1_v2","forced_minus_anchor",
           "center_num_mod32","center_den_mod32"]
linear=[]
for names in combinations(lin_names,3):
    diffs=[tuple(F[u][x]-F[v][x] for x in names) for u,v in edges]
    for coeff in product(range(-4,5),repeat=3):
        if coeff==(0,0,0): continue
        vals=[sum(c*d for c,d in zip(coeff,ds)) for ds in diffs]
        if min(vals)>=1:
            linear.append({
              "features":names,"coeff":coeff,
              "min_drop":min(vals),"max_drop":max(vals)
            })
            break
    if linear: break

# Rank layer summaries by coordinate ranges.
layer_summary={}
for r in range(max(rank.values())+1):
    ks=[k for k in nodes if rank[k]==r]
    layer_summary[str(r)]={
      "nodes":len(ks),
      "anchors":sorted(set(F[k]["anchor"] for k in ks)),
      "forced_range":[min(F[k]["forced"] for k in ks),max(F[k]["forced"] for k in ks)],
      "radius_values":sorted(set(F[k]["radius"] for k in ks))[:50],
      "extra_values":sorted(set(F[k]["extra"] for k in ks)),
      "extra_pop_values":sorted(set(F[k]["extra_pop"] for k in ks)),
      "extra_v2_values":sorted(set(F[k]["extra_v2"] for k in ks)),
      "rho5_values":sorted(set(F[k]["rho5"] for k in ks)),
      "centres":len(set(F[k]["center"] for k in ks)),
    }

# Exact edge rank-drop histogram.
drop_hist=Counter(rank[u]-rank[v] for u,v in edges)
assert min(drop_hist)>0

result={
 "schema":"COLLATZ_CRYSTAL_RESIDUAL_RANK_LAW_V54",
 "parent":"collatz-crystal-nonpositive-budget-kernel-v53@2b49ce24eb1593e045a7e1b7bcb8782f3f426d02",
 "graph":{
   "nodes":len(nodes),"edges":len(edges),"max_rank":max(rank.values()),
   "rank_histogram":dict(sorted(Counter(rank.values()).items())),
   "rank_drop_histogram":dict(sorted(drop_hist.items())),
   "elimination_layers":layers,
 },
 "single_coordinate_monotonicity":scalar,
 "minimum_rank_functional_subsets":functional_subsets[:30],
 "lexicographic_local_potentials":lex[:30],
 "linear_local_potential":linear[:10],
 "layer_summary":layer_summary,
 "verdict":(
   "TINY_LOCAL_RANK_LAW_FOUND"
   if lex or linear or (functional_subsets and len(functional_subsets[0]["fields"])<=2)
   else "RANK_REQUIRES_RICH_RETURN_IDENTITY_ON_THIS_CORPUS"
 ),
 "interpretation":(
   "V54 extracts the exact 0..4 elimination rank behind V53 and tests whether "
   "it is already a simple local arithmetic invariant rather than a memorized "
   "finite DAG rank."
 ),
 "promotion_boundary":(
   "Even a tiny exact law here is only a theorem candidate until challenged "
   "prospectively and proved for every lawful zero-tail residual return."
 ),
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
