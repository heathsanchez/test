#!/usr/bin/env python3
"""V55: symbolic switch-grammar audit of the V53 nonpositive-budget kernel.

This is a bounded theorem-discovery gate, not QED.

V53 found a source-free acyclic residual graph (5430 nodes, 833 edges, rank 4).
V54 independently formalized the exact centre-switch defect transport identity.
Here we join them without changing the source corpus or the V53 key.

For every V53 residual->residual edge we compute:
  * return-centre determinant/injection J = C1*B2-C2*B1,
  * dyadic separation h=v2(|J|) when defined,
  * the exact drop/flat/recharge classification used by the older q=0 engine,
  * V53 elimination-rank change.

We also exhaustively project the six coordinates of the V53 source-free key and
ask which coordinate subsets determine the bounded rank.  This identifies the
smallest empirical state that a universal symbolic theorem would need to
explain.

No new source search.  No new return-law bank.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
from itertools import combinations
import hashlib
import io
import json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_nonpositive_budget_kernel_v53 as v53

KEY_FIELDS=("anchor","forced","rho","centre","radius","extra5")

def v2(x:int)->int:
    assert x>0
    return (x & -x).bit_length()-1

def graph_and_rank():
    nodes=set()
    succ=defaultdict(set)
    for tr in v53.transitions:
        if not tr["src"]["residual"]:
            continue
        u=tr["src"]["key"]
        nodes.add(u); succ.setdefault(u,set())
        if tr["kind"]=="RESIDUAL":
            w=tr["dst"]["key"]
            nodes.add(w); succ[u].add(w); succ.setdefault(w,set())
    rank,left,layers=v53.elimination_rank(nodes,succ)
    assert not left
    assert len(nodes)==v53.base_graph["nodes"]
    assert sum(len(z) for z in succ.values())==v53.base_graph["edges"]
    return nodes,succ,rank,layers

nodes,succ,rank,layers=graph_and_rank()

# Any representative row for a source-free key.  Different exact sources may
# realize the same key; V53 has already checked that source identity is not
# needed for bounded acyclicity.
rows_by_key=defaultdict(list)
for r in v53.rows:
    if r["residual"]:
        rows_by_key[r["key"]].append(r)

stats=Counter()
class_hist=Counter()
rank_pair_hist=Counter()
h_hist=Counter()
excess_hist=Counter()
separators=[]
examples=defaultdict(list)
edge_rows=[]

for tr in v53.transitions:
    if tr["kind"]!="RESIDUAL":
        continue
    s=tr["src"]; d=tr["dst"]
    u=s["key"]; w=d["key"]
    assert u in rank and w in rank
    assert rank[u] > rank[w]
    rank_pair_hist[(rank[u],rank[w])]+=1
    stats["EDGE_ROWS"]+=1
    if s["k1"]!=d["k0"]:
        stats["NONCONTIGUOUS"]+=1
        continue
    assert s["m1"]==d["m0"]
    m=d["m0"]

    A1,B1,P1,D1=s["A"],s["B"],s["P"],s["D"]
    A2,B2,P2,D2=d["A"],d["B"],d["P"],d["D"]
    C1=P1-A1; C2=P2-A2
    J=C1*B2-C2*B1
    rho1=u[2]; rho2=w[2]
    bits=min(D1+1,D2+1)
    mask=(1<<bits)-1

    row={
      "src_rank":rank[u],"dst_rank":rank[w],
      "anchor":s["anchor"],
      "D1":D1,"D2":D2,
      "C1_sign":(C1>0)-(C1<0),"C2_sign":(C2>0)-(C2<0),
      "J":str(J),"bits":bits,
      "src_key":repr(u),"dst_key":repr(w),
      "m":str(m),
    }

    if J==0:
        cls="SAME_CENTRE"
        stats["SAME_CENTRE"]+=1
    else:
        h=v2(abs(J)); row["h"]=h; h_hist[h]+=1
        disjoint=((rho1-rho2)&mask)!=0
        row["disjoint_cylinders"]=disjoint
        if not disjoint:
            cls="DISTINCT_CENTRE_OVERLAP"
            stats["DISTINCT_CENTRE_OVERLAP"]+=1
        else:
            stats["DISTINCT_CENTRE_DISJOINT"]+=1
            if not h<bits:
                stats["H_NOT_BELOW_BITS"]+=1
            before=C1*m-B1
            if before==0:
                cls="ZERO_OLD_DEFECT"
                stats["ZERO_OLD_DEFECT"]+=1
            else:
                vb=v2(abs(before)); row["old_defect_v2"]=vb
                if vb!=h:
                    stats["OLD_DEFECT_NOT_AT_SEPARATION"]+=1
                if C2==0:
                    cls="NEXT_UNIT_SLOPE_NO_CENTRE"
                    stats["NEXT_UNIT_SLOPE_NO_CENTRE"]+=1
                else:
                    q=Fraction(B2,C2)
                    p,den=q.numerator,q.denominator
                    nd=den*m-p
                    if nd==0:
                        cls="ZERO_NEW_DEFECT"
                        stats["ZERO_NEW_DEFECT"]+=1
                    else:
                        vv=v2(abs(nd))
                        base=D2+1
                        row["new_normalized_defect_v2"]=vv
                        row["base"]=base
                        if vv<base:
                            cls="CYLINDER_VALUATION_UNDERFLOW"
                            stats["CYLINDER_VALUATION_UNDERFLOW"]+=1
                        else:
                            excess=vv-base
                            threshold=h-1
                            row["excess"]=excess
                            row["threshold"]=threshold
                            excess_hist[excess]+=1
                            if excess<threshold:
                                cls="DROP"
                            elif excess>threshold:
                                cls="FLAT"
                            else:
                                cls="RECHARGE"
                            stats[cls]+=1
    row["class"]=cls
    class_hist[(cls,rank[u],rank[w])]+=1
    if len(examples[cls])<12:
        examples[cls].append(row)
    edge_rows.append(row)

# Test the historical switch-transport consequence on consecutive residual
# switches along each exact source/anchor chronology.  This is separate from
# source-free graph composition: it only compares actually consecutive edges.
chron=defaultdict(list)
for tr in v53.transitions:
    if tr["kind"]=="RESIDUAL" and tr["src"]["k1"]==tr["dst"]["k0"]:
        chron[(tr["source"],tr["anchor"])].append(tr)
for seq in chron.values():
    seq.sort(key=lambda z:(z["src"]["k0"],z["src"]["k1"]))
    for a,b in zip(seq,seq[1:]):
        if a["dst"]["k1"]!=b["dst"]["k0"]:
            continue
        # Recompute only if both transitions have a proper disjoint-centre
        # classification with h/excess.
        def sw(tr):
            s,d=tr["src"],tr["dst"]
            C1=s["P"]-s["A"]; C2=d["P"]-d["A"]
            J=C1*d["B"]-C2*s["B"]
            if J==0 or C2==0: return None
            bits=min(s["D"]+1,d["D"]+1)
            if ((s["key"][2]-d["key"][2])&((1<<bits)-1))==0:
                return None
            h=v2(abs(J))
            m=d["m0"]
            before=C1*m-s["B"]
            if before==0 or v2(abs(before))!=h: return None
            q=Fraction(d["B"],C2)
            nd=q.denominator*m-q.numerator
            if nd==0: return None
            vv=v2(abs(nd)); base=d["D"]+1
            if vv<base: return None
            excess=vv-base
            threshold=h-1
            out="DROP" if excess<threshold else "FLAT" if excess>threshold else "RECHARGE"
            return h,excess,out
        z1=sw(a); z2=sw(b)
        if z1 and z2:
            stats["CONSECUTIVE_SWITCH_PAIRS"]+=1
            if z2[0]==z1[1]+1:
                stats["H_TRANSPORT_MATCH"]+=1
            else:
                stats["H_TRANSPORT_FAIL"]+=1
                if len(separators)<20:
                    separators.append({
                      "kind":"H_TRANSPORT_FAIL",
                      "first":z1,"second":z2,
                      "source":str(a["source"]),"anchor":a["anchor"],
                      "depth":[a["src"]["k0"],b["dst"]["k1"]],
                    })
            if z1[2]=="RECHARGE":
                stats["RECHARGE_WITH_OBSERVED_NEXT_SWITCH"]+=1

# Exhaustively test which coordinate subsets of the six-field V53 key determine
# bounded elimination rank.  A projection is rank-functional iff no projected
# key contains nodes of two different ranks.
projection_results=[]
for k in range(0,len(KEY_FIELDS)+1):
    for inds in combinations(range(len(KEY_FIELDS)),k):
        buckets=defaultdict(set)
        for node in nodes:
            sig=tuple(node[i] for i in inds)
            buckets[sig].add(rank[node])
        collisions=sum(1 for rs in buckets.values() if len(rs)>1)
        max_mult=max((len(rs) for rs in buckets.values()),default=0)
        projection_results.append({
          "fields":[KEY_FIELDS[i] for i in inds],
          "field_count":k,
          "signatures":len(buckets),
          "rank_collision_signatures":collisions,
          "max_rank_multiplicity":max_mult,
          "rank_functional":collisions==0,
        })

functional=[z for z in projection_results if z["rank_functional"]]
min_k=min(z["field_count"] for z in functional)
minimal_functional=[z for z in functional if z["field_count"]==min_k]
minimal_functional.sort(key=lambda z:(z["signatures"],z["fields"]))

# Edge-level symbolic signature ambiguity: does a compact switch tuple determine
# the observed rank pair?  This is a discovery diagnostic, not a state claim.
sig_pairs=defaultdict(set)
for e in edge_rows:
    sig=(e["class"],e.get("h"),e.get("excess"),e["D1"],e["D2"],
         e["C1_sign"],e["C2_sign"])
    sig_pairs[sig].add((e["src_rank"],e["dst_rank"]))
amb=[(repr(k),sorted(v)) for k,v in sig_pairs.items() if len(v)>1]
amb.sort()
stats["SYMBOLIC_EDGE_SIGNATURES"]=len(sig_pairs)
stats["SYMBOLIC_EDGE_RANKPAIR_AMBIGUITIES"]=len(amb)

verdict=(
  "SWITCH_GRAMMAR_SEPARATOR"
  if stats["NONCONTIGUOUS"] or stats["OLD_DEFECT_NOT_AT_SEPARATION"]
     or stats["CYLINDER_VALUATION_UNDERFLOW"] or stats["H_TRANSPORT_FAIL"]
  else "SWITCH_GRAMMAR_CONSISTENT_ON_V53_RESIDUAL"
)

result={
 "schema":"COLLATZ_CRYSTAL_SWITCH_GRAMMAR_V55",
 "parents":{
   "V53":"collatz-crystal-nonpositive-budget-kernel-v53@2b49ce24eb1593e045a7e1b7bcb8782f3f426d02",
   "V54":"collatz-crystal-return-defect-transport-v54@966d86417b124ba876bb35ab97294786ce10a855",
   "historical_q0":"collatz-rigid-component-termination-v1@5cf8cc623da64b513a2c6c564f852b20652bec36",
 },
 "v53_graph":{"nodes":len(nodes),"edges":sum(len(z) for z in succ.values()),
              "layers":layers,"max_rank":max(rank.values())},
 "stats":dict(sorted(stats.items())),
 "class_rank_histogram":{
   repr(k):v for k,v in sorted(class_hist.items(),key=lambda kv:repr(kv[0]))
 },
 "h_histogram":dict(sorted(h_hist.items())),
 "excess_histogram":dict(sorted(excess_hist.items())),
 "minimal_rank_functional_key_projections":minimal_functional,
 "all_rank_functional_projection_count":len(functional),
 "symbolic_edge_rankpair_ambiguities":amb[:50],
 "examples":{k:v for k,v in examples.items()},
 "separators":separators,
 "verdict":verdict,
 "interpretation":(
   "V54 supplies the exact centre-switch transport identity. V55 asks whether "
   "the V53 source-free DAG is already explained by the historical dyadic "
   "drop/flat/recharge geometry, and which V53 key coordinates are actually "
   "needed to determine the bounded elimination rank."
 ),
 "promotion_boundary":(
   "Even a perfect bounded match is not all-depth grammar completeness. "
   "Universal promotion requires formal dyadic valuation transport plus a "
   "proof that every lawful zero-tail residual return projects into the "
   "rank-decreasing switch grammar, or an exact symbolic separator."
 ),
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
