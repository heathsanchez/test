#!/usr/bin/env python3
"""V55: exact anatomy of the three V54 rank-4 residual states.

V54 rejected a simple formula for the full 0..4 empirical DAG rank.  Its
three maximal-rank states nevertheless share anchor=2, forced=4, rho=15.
This gate asks whether they are all the same exact expanding 110 return
m'=(9m+1)/8, and traces every realized successor spine until progress/exit.

If the top states are one universal affine law, its own-centre defect obeys
  m'+1 = 9(m+1)/8
so v2(m'+1) drops by exactly 3 on every actual repetition.  That gives a
reusable theorem target for this maximal residual stratum, but does not by
itself rank lower strata or prove Collatz.
"""
from __future__ import annotations
from collections import defaultdict, Counter
from contextlib import redirect_stdout
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_nonpositive_budget_kernel_v53 as v53
    import collatz_crystal_residual_rank_law_v54 as v54
    import collatz_crystal_nearest_centre_v45 as v45

nodes=set(); succ=defaultdict(set)
for tr in v53.transitions:
    if not tr["src"]["residual"]: continue
    u=tr["src"]["key"]; nodes.add(u); succ.setdefault(u,set())
    if tr["kind"]=="RESIDUAL":
        v=tr["dst"]["key"]; nodes.add(v); succ[u].add(v); succ.setdefault(v,set())
rank,left,layers=v53.elimination_rank(nodes,succ)
assert not left and max(rank.values())==4
tops=sorted([k for k,r in rank.items() if r==4],key=repr)
assert len(tops)==3

def v2(x:int):
    x=abs(x)
    if x==0: return None
    return (x & -x).bit_length()-1

by_src=defaultdict(list)
for tr in v53.transitions:
    if tr["src"]["residual"]:
        by_src[tr["src"]["key"]].append(tr)

def center_of(k):
    anchor,forced,rho,cid,rad,extra=k
    a,c=v45.id_center[cid]
    assert a==anchor
    return c

top_rows=[]
all_top_110=True
all_top_center_minus1=True
all_v2_drop3=True
for k in tops:
    trs=by_src[k]
    laws=sorted(set((tr["src"]["A"],tr["src"]["B"],tr["src"]["P"],tr["src"]["D"],tr["src"]["W"]) for tr in trs))
    center=center_of(k)
    is110=all((A,B,P,D)==(9,1,8,3) for A,B,P,D,W in laws)
    all_top_110 &= is110
    all_top_center_minus1 &= (center==(-1,1))
    witnesses=[]
    dests=Counter()
    for tr in trs[:20]:
        s=tr["src"]
        vv0=v2(s["m0"]+1); vv1=v2(s["m1"]+1)
        if is110:
            assert 8*(s["m1"]+1)==9*(s["m0"]+1)
            assert vv0 is not None and vv1 is not None and vv0-vv1==3
        if vv0 is not None and vv1 is not None:
            all_v2_drop3 &= (vv0-vv1==3)
        if tr["kind"]=="RESIDUAL":
            dr=rank[tr["dst"]["key"]]
            dests[f"RESIDUAL_RANK_{dr}"]+=1
            dkey=repr(tr["dst"]["key"])
        else:
            dests[tr["kind"]]+=1
            dkey=None
        witnesses.append({
          "source":str(tr["source"]),"t":str(tr["t"]),
          "depth":[s["k0"],s["k1"]],
          "m0":str(s["m0"]),"m1":str(s["m1"]),
          "v2_m0_plus1":vv0,"v2_m1_plus1":vv1,
          "kind":tr["kind"],"dst_rank":(rank[tr["dst"]["key"]] if tr["kind"]=="RESIDUAL" else None),
          "dst_key":dkey,
        })
    top_rows.append({
      "key":repr(k),"center":[center[0],center[1]],
      "rank":rank[k],"realized_transition_rows":len(trs),
      "laws":[[str(A),str(B),str(P),D,str(W)] for A,B,P,D,W in laws],
      "is_exact_110_owner_law":is110,
      "destination_histogram":dict(sorted(dests.items())),
      "witnesses":witnesses,
    })

# Enumerate all realized maximal paths from rank4 nodes through residual edges.
# DAG rank <=4 makes this tiny.
paths=[]
def walk(path):
    u=path[-1]
    vs=sorted(succ.get(u,()),key=repr)
    if not vs:
        paths.append(path[:]); return
    for v in vs: walk(path+[v])
for t in tops: walk([t])

path_rows=[]
for p in paths:
    path_rows.append({
      "ranks":[rank[x] for x in p],
      "keys":[repr(x) for x in p],
      "nearest_classifier_centres":[list(center_of(x)) for x in p],
      "forced":[x[1] for x in p],
      "radius":[x[4] for x in p],
      "extra":[x[5] for x in p],
    })

result={
 "schema":"COLLATZ_CRYSTAL_RANK4_SPINE_V55",
 "parents":{
   "V53":"collatz-crystal-nonpositive-budget-kernel-v53@2b49ce24eb1593e045a7e1b7bcb8782f3f426d02",
   "V54":"collatz-crystal-residual-rank-law-v54@d74a3b6850ba1dd8a4a4333e045a42f84116a830",
 },
 "top_count":len(tops),
 "top_states":top_rows,
 "all_top_states_exact_110_owner_law":all_top_110,
 "all_top_centres_minus_one":all_top_center_minus1,
 "all_top_realizations_drop_v2_mplus1_by_3":all_v2_drop3,
 "maximal_residual_paths":path_rows,
 "path_count":len(path_rows),
 "verdict":(
   "MAXIMAL_STRATUM_IS_EXACT_110_MINUS_ONE_COUNTDOWN"
   if all_top_110 and all(
     row["actual_law_centres"]==[[-1,1]] for row in top_rows
   ) and all_v2_drop3
   else "RANK4_STRATUM_NOT_ONE_UNIVERSAL_110_LAW"
 ),
 "interpretation":(
   "Tests whether the only rank-4 residual mechanism is the classical 110 / "
   "fixed-centre -1 expanding return.  If yes, exact v2(m+1) countdown proves "
   "finite residence in that maximal stratum for every individual realization."
 ),
 "promotion_boundary":(
   "This can discharge only the maximal empirical stratum.  Global QED still "
   "requires a source-independent classification showing every lawful maximal "
   "residual state has this form and a well-founded treatment of the lower "
   "strata, or a direct theorem bypassing the empirical strata."
 ),
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
