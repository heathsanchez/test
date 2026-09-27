#!/usr/bin/env python3
"""Crystal pruning-event automaton for target-directed source-valid reverse exits.

States are survivor residue classes at consequential Q levels. Edges are exact
ternary lifts r -> r + k*3^Q that survive at the next consequential level.
This measures recursive structure of the reverse-certificate language itself.
It does NOT yet prove coupling to forward source/origin states.
"""
import json,math
from collections import Counter,defaultdict
from collatz_reverse_target_audit import enumerate_target,coverage

EVENTS=[3,5,6,8,10,11,13]
tables={}
survivors={}
for Q in EVENTS:
    tab,st=coverage(enumerate_target(Q),Q)
    tables[Q]=tab
    survivors[Q]=[r for r in range(1,3**Q,3) if not tab[r]]

trans=[]
for q0,q1 in zip(EVENTS,EVENTS[1:]):
    scale=3**(q1-q0); M0=3**q0
    child_counts=Counter(); total_edges=0
    examples={}
    for r in survivors[q0]:
        cnt=0
        for k in range(scale):
            y=r+k*M0
            if y<3**q1 and y%3==1 and not tables[q1][y]:
                cnt+=1; total_edges+=1
        child_counts[cnt]+=1
        if cnt not in examples: examples[cnt]=r
    trans.append({"from":q0,"to":q1,"scale":scale,
      "parents":len(survivors[q0]),"children":len(survivors[q1]),
      "edge_count":total_edges,"child_count_hist":dict(sorted(child_counts.items())),
      "max_children":max(child_counts) if child_counts else 0,
      "mean_children":total_edges/len(survivors[q0]),
      "full_branching":scale,
      "normalized_survival_per_refinement":total_edges/(len(survivors[q0])*scale),
      "separator_examples":examples})

# Test exact self-similarity: survivor membership at q1 as function of parent
# survivor status plus new trits. Parent collisions with different child masks
# demand suffix refinement.
masks=[]
for q0,q1 in zip(EVENTS,EVENTS[1:]):
    scale=3**(q1-q0); M0=3**q0
    hist=Counter()
    for r in survivors[q0]:
        mask=0
        for k in range(scale):
            y=r+k*M0
            if y%3==1 and not tables[q1][y]: mask|=1<<k
        hist[mask]+=1
    masks.append({"from":q0,"to":q1,"distinct_child_masks":len(hist),
                  "mask_hist_top":hist.most_common(12)})

print(json.dumps({"schema":"COLLATZ_PRUNING_EVENT_AUTOMATON_V0",
 "events":EVENTS,
 "survivor_counts":{q:len(survivors[q]) for q in EVENTS},
 "transitions":trans,"child_masks":masks,
 "interpretation":"exact nested source-valid reverse-survivor language under ternary refinement; forward source/origin coupling still separate",
 "global_collatz":"UNKNOWN"},indent=2))
