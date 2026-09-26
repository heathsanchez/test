#!/usr/bin/env python3
"""Future-relative quotient of the V2 Collatz bi-adic residual.

Tests the ROS-predicted simplification:
  the 27 surviving Q3 first-difference parents may induce the same exact
  Q2 survivor language under the already-qualified forward/reverse certificate
  compiler. If so, parent Q3 identity is not consequential state for this
  residual and may be quotiented away.

Also compares the resulting binary survivor language against the existing
direct-descent and inverse-odd symbolic lower-merge frontiers, and computes
finite-horizon future signatures of the Q2 survivor tree.

No new certificate family is introduced. No Collatz theorem is claimed.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from collections import defaultdict

import collatz_reverse_trit_bicell_v2 as v2
import collatz_symbolic_merge as sm
import collatz_symbolic_frontier as sf


def evolve(max_depth):
    parents=v2.parent_residuals()
    # parent -> set of residues mod 2^a
    live={i:{1} for i in range(len(parents))}
    rows=[]
    languages={}
    for a in range(1,max_depth+1):
        if a>1:
            bit=1<<(a-1)
            live={i:{x for s in vals for x in (s,s|bit)}
                  for i,vals in live.items()}
        nxt={}
        kinds=defaultdict(int)
        for i,vals in live.items():
            keep=set()
            for s in sorted(vals):
                cert=v2.composed_certificate(parents[i],s,a)
                if cert is None:
                    keep.add(s)
                else:
                    kinds[cert["kind"]]+=1
            nxt[i]=keep
        live=nxt
        sets=[tuple(sorted(live[i])) for i in range(len(parents))]
        distinct=sorted(set(sets))
        languages[a]=sets
        rows.append(dict(
            q2_depth=a,
            total_residual=sum(len(x) for x in sets),
            per_parent_counts=sorted(set(len(x) for x in sets)),
            distinct_parent_languages=len(distinct),
            canonical_language=list(distinct[0]) if len(distinct)==1 else None,
            closure_kinds=dict(sorted(kinds.items())),
        ))
        print("LANGUAGE",json.dumps(rows[-1],sort_keys=True))
    return parents,languages,rows


def symbolic_residual_sets(max_depth):
    out={}
    direct={}
    for a in range(1,max_depth+1):
        _,res,_=sm.compile_portfolio(a)
        out[a]=set(x["b"] for x in res)
        _,r2,_=sf.compile_frontier(a)
        direct[a]=set(x["b"] for x in r2)
    return out,direct


def tree_signatures(language_by_depth,max_depth):
    """Bottom-up protected-future signatures for one binary survivor language."""
    # live sets are nested cylinder languages. Closed child = -1.
    sig_ids={}
    classes_by_depth={}
    next_id=0
    terminal_id=0
    next_id=1
    # At max depth every live node has same remaining-horizon signature.
    classes_by_depth[max_depth]={s:terminal_id for s in language_by_depth[max_depth]}
    level_stats=[dict(depth=max_depth,classes=1 if language_by_depth[max_depth] else 0,
                      live_nodes=len(language_by_depth[max_depth]))]
    for a in range(max_depth-1,0,-1):
        child_classes=classes_by_depth[a+1]
        sig_to_id={}
        node_map={}
        bit=1<<a
        for s in language_by_depth[a]:
            c0=s
            c1=s|bit
            left=child_classes.get(c0,-1)
            right=child_classes.get(c1,-1)
            sig=(left,right)
            if sig not in sig_to_id:
                sig_to_id[sig]=len(sig_to_id)
            node_map[s]=sig_to_id[sig]
        classes_by_depth[a]=node_map
        level_stats.append(dict(depth=a,classes=len(set(node_map.values())),
                                live_nodes=len(node_map),
                                signatures=[list(x) for x in sorted(sig_to_id)]))
    return list(reversed(level_stats)),classes_by_depth


def run(max_depth,output):
    parents,langs,rows=evolve(max_depth)
    sym,direct=symbolic_residual_sets(max_depth)

    comparisons=[]
    all_parent_equal=True
    canonical={}
    for a in range(1,max_depth+1):
        sets=[set(langs[a][i]) for i in range(len(parents))]
        eq=all(x==sets[0] for x in sets)
        all_parent_equal &= eq
        if eq:
            S=sets[0]; canonical[a]=S
            comparisons.append(dict(
                depth=a,
                v2_count=len(S),
                symbolic_merge_count=len(sym[a]),
                direct_count=len(direct[a]),
                v2_subset_symbolic=S<=sym[a],
                v2_subset_direct=S<=direct[a],
                symbolic_extra=sorted(sym[a]-S)[:100],
                direct_extra=sorted(direct[a]-S)[:100],
            ))
        else:
            comparisons.append(dict(depth=a,parent_languages_equal=False))

    if canonical:
        stats,classes=tree_signatures(canonical,max_depth)
    else:
        stats=[];classes={}

    result=dict(
        schema="COLLATZ_REVERSE_TRIT_BICELL_V3_QUOTIENT",
        parent="collatz-reverse-trit-bicell-v2@741454370eb8d0d29565a7ed1b0a6bb44344c111",
        q3_parent_count=len(parents),
        max_q2_depth=max_depth,
        parent_languages_equal_all_depths=all_parent_equal,
        rows=rows,
        frontier_comparisons=comparisons,
        future_signature_levels=stats,
        verdict=("PASS_Q3_PARENT_IDENTITY_QUOTIENTS_TO_ONE_Q2_LANGUAGE"
                 if all_parent_equal else
                 "Q3_PARENT_SEPARATOR_REMAINS"),
        scope=("finite exact V1 residual through existing V2 certificate compiler; "
               "future-relative language quotient; no universal Collatz claim")
    )
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("PARENT_LANGUAGES_EQUAL",all_parent_equal)
    for x in comparisons:
        print("COMPARE",json.dumps(x,sort_keys=True))
    for x in stats:
        print("FUTURE_SIG",json.dumps(x,sort_keys=True))
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-q2-depth",type=int,default=14)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    assert 2<=a.max_q2_depth<=24
    run(a.max_q2_depth,a.output)
