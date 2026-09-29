#!/usr/bin/env python3
"""Crystal V26: bounded protected-future quotient for the sole V23 affine cell.

Parent: collatz-crystal-parameter-quotient-v25@3d33a5a44cbcf3546f44e4ecdd4d153bafa03fcc

V25 earned the next parameter bit as necessary state and showed all 64 depth-9
survivors have finite all-zero exits.  V26 asks for the minimum consequential
state directly: two live parameter cells are identified only when their exact
future EXIT/non-EXIT trees agree to horizon h.

For each h we then test the induced class under one more parameter bit:
* right-congruence ambiguity: does one class have multiple observed 0- or
  1-successor classes at the same h?
* zero-edge SCCs: can the bounded quotient support an indefinitely zero tail?

Everything here is exact on the generated symbolic tree.  Stabilization on a
finite tree is a theorem candidate, not a universal proof.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from functools import lru_cache
import hashlib,json

import collatz_crystal_parameter_quotient_v25 as v25

MAX_DEPTH=11
MAX_HORIZON=6

def children(d,r):
    return ((d+1,r),(d+1,r+(1<<d)))

def build_tree():
    nodes={}
    frontier=[(0,0)]
    bydepth=defaultdict(list)
    while frontier:
        d,r=frontier.pop()
        if (d,r) in nodes or d>MAX_DEPTH:
            continue
        z=v25.classify_cell(d,r,with_merge=True)
        term=bool(z["terminal"])
        nodes[(d,r)]={"terminal":term,"exit":z.get("exit")}
        bydepth[d].append(r)
        if not term and d<MAX_DEPTH:
            frontier.extend(children(d,r))
    for d in bydepth:
        bydepth[d].sort()
    return nodes,bydepth

def main():
    nodes,bydepth=build_tree()

    @lru_cache(maxsize=None)
    def sig(d,r,h):
        z=nodes[(d,r)]
        if z["terminal"]:
            return ("E",)
        if h==0:
            return ("L",)
        assert d+h<=MAX_DEPTH
        c0,c1=children(d,r)
        return ("N",sig(*c0,h-1),sig(*c1,h-1))

    horizons=[]
    first_right_congruent=None
    for h in range(MAX_HORIZON+1):
        eligible=[(d,r) for (d,r),z in nodes.items()
                  if not z["terminal"] and d+h<=MAX_DEPTH]
        classes=defaultdict(list)
        for d,r in eligible:
            classes[sig(d,r,h)].append((d,r))

        # Same-h successor test requires another h steps below each child.
        trans0=defaultdict(set);trans1=defaultdict(set)
        supported=0
        for d,r in eligible:
            if d+h+1>MAX_DEPTH:
                continue
            k=sig(d,r,h)
            c0,c1=children(d,r)
            # A child can be terminal; sig handles that.
            trans0[k].add(sig(*c0,h))
            trans1[k].add(sig(*c1,h))
            supported+=1

        amb0=sum(len(v)>1 for v in trans0.values())
        amb1=sum(len(v)>1 for v in trans1.values())
        ambiguous_classes=len({k for k,v in trans0.items() if len(v)>1} |
                              {k for k,v in trans1.items() if len(v)>1})

        # Empirical same-h class graph where transitions are single-valued.
        keys=set(classes)
        idx={k:i for i,k in enumerate(sorted(keys,key=repr))}
        g0=defaultdict(set);gall=defaultdict(set)
        for k,vs in trans0.items():
            if len(vs)==1:
                v=next(iter(vs))
                if v in idx:
                    g0[idx[k]].add(idx[v])
                    gall[idx[k]].add(idx[v])
        for k,vs in trans1.items():
            if len(vs)==1:
                v=next(iter(vs))
                if v in idx:
                    gall[idx[k]].add(idx[v])

        def scc(graph):
            # Tarjan on observed live class edges.
            n=len(idx);index=0;stack=[];on=set();I={};L={};comps=[]
            def dfs(v):
                nonlocal index
                I[v]=L[v]=index;index+=1;stack.append(v);on.add(v)
                for w in graph.get(v,()):
                    if w not in I:
                        dfs(w);L[v]=min(L[v],L[w])
                    elif w in on:
                        L[v]=min(L[v],I[w])
                if L[v]==I[v]:
                    c=[]
                    while True:
                        w=stack.pop();on.remove(w);c.append(w)
                        if w==v:break
                    comps.append(c)
            for v in range(n):
                if v not in I:dfs(v)
            cyc=[]
            for c in comps:
                if len(c)>1:cyc.append(c)
                elif c and c[0] in graph.get(c[0],set()):cyc.append(c)
            return comps,cyc

        _,zero_cycles=scc(g0)
        _,all_cycles=scc(gall)
        row={
          "horizon":h,
          "eligible_live_nodes":len(eligible),
          "future_classes":len(classes),
          "supported_transitions":supported,
          "ambiguous_zero_classes":amb0,
          "ambiguous_one_classes":amb1,
          "ambiguous_classes_union":ambiguous_classes,
          "zero_edge_cycle_sccs":len(zero_cycles),
          "all_edge_cycle_sccs":len(all_cycles),
          "largest_class_support":max((len(v) for v in classes.values()),default=0),
        }
        horizons.append(row)
        if first_right_congruent is None and supported and ambiguous_classes==0:
            first_right_congruent=h

    # Class-count refinement profile by source depth for the best tested horizon.
    h=MAX_HORIZON
    depth_profile=[]
    for d in range(MAX_DEPTH-h+1):
        live=[r for r in bydepth.get(d,()) if not nodes[(d,r)]["terminal"]]
        cs=Counter(repr(sig(d,r,h)) for r in live)
        depth_profile.append({
          "depth":d,"live":len(live),"classes":len(cs),
          "largest_support":max(cs.values(),default=0)
        })

    # Exact terminal census.
    exits=Counter()
    live_by_depth={}
    for (d,r),z in nodes.items():
        if z["terminal"]:
            exits[z["exit"]["kind"]]+=1
        else:
            live_by_depth[d]=live_by_depth.get(d,0)+1

    body={
      "schema":"COLLATZ_CRYSTAL_FUTURE_QUOTIENT_V26",
      "parent":"collatz-crystal-parameter-quotient-v25@3d33a5a44cbcf3546f44e4ecdd4d153bafa03fcc",
      "max_depth":MAX_DEPTH,
      "max_horizon":MAX_HORIZON,
      "nodes":len(nodes),
      "live_by_depth":dict(sorted(live_by_depth.items())),
      "exit_census":dict(sorted(exits.items())),
      "horizons":horizons,
      "first_bounded_right_congruent_horizon":first_right_congruent,
      "depth_profile_h6":depth_profile,
      "claim_boundary":(
        "Future signatures are exact only through their declared finite horizon. "
        "Zero observed ambiguity or zero SCCs is a candidate for an all-depth "
        "right congruence/rank and is not promoted without a symbolic proof."
      ),
      "universal_status":"UNKNOWN",
      "global_collatz":"UNKNOWN"
    }
    body["certificate_sha256"]=hashlib.sha256(
        json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(json.dumps(body,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
