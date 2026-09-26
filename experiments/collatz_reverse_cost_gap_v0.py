#!/usr/bin/env python3
"""Compile minimal reverse cost and alternative-predecessor thresholds per 3-adic context.

For each 12-odd residue modulo 3^12 admitted by an S=19 block, find whether the
same endpoint context admits a lower-cost S<=18 block. For every S=19 word,
compare its predecessor with the best lower-cost alternative and compute the
integer y threshold above which the alternative predecessor is strictly smaller.

This separates identity/replay histories from genuinely cheaper inverse histories.
"""
from itertools import combinations
import json
O=12;MOD=3**O
def comps(total,parts):
    for cuts in combinations(range(1,total),parts-1):
        p=0;w=[]
        for c in cuts+(total,):w.append(c-p);p=c
        yield tuple(w)
def cocycle(w):
    C=0
    for i,a in enumerate(w):C=(1<<a)*C+3**i
    return C
best={} # residue -> (S,C,w), prioritize smaller S then larger C (smaller predecessor)
all19=[]
for S in range(12,20):
    inv=pow(1<<S,-1,MOD)
    for w in comps(S,O):
        C=cocycle(w);r=C*inv%MOD
        cand=(S,-C,w,C)
        if r not in best or cand[:2]<best[r][:2]:best[r]=cand
        if S==19:all19.append((r,C,w))
lower_res={r for r,v in best.items() if v[0]<19}
only19={r for r,v in best.items() if v[0]==19}
thresholds=[];words_with_cheaper=0
for r,C19,w19 in all19:
    if r not in lower_res:continue
    Sneg=best[r];Sa=Sneg[0];Ca=Sneg[3]
    den=(1<<19)-(1<<Sa)
    # p_alt < p19 iff 2^Sa*y-Ca < 2^19*y-C19
    # iff den*y > C19-Ca.
    num=C19-Ca
    y0=0 if num<0 else num//den+1
    thresholds.append(y0);words_with_cheaper+=1
result={
 "schema":"COLLATZ_REVERSE_COST_GAP_V0",
 "s19_words":len(all19),
 "admissible_residues":len(best),
 "residues_with_lower_cost_alternative":len(lower_res),
 "residues_only_cost19":len(only19),
 "fraction_contexts_with_cheaper_alternative":len(lower_res)/len(best),
 "s19_words_with_cheaper_context":words_with_cheaper,
 "alternative_smaller_threshold":{
   "max":max(thresholds) if thresholds else None,
   "median":sorted(thresholds)[len(thresholds)//2] if thresholds else None,
   "all_below_130":all(x<130 for x in thresholds)
 },
 "only19_sample":sorted(only19)[:30],
 "interpretation":"for a cost-19 actual 12-odd block, any same-context lower-cost block yields a strictly smaller predecessor once y exceeds its threshold",
 "next":"the only genuine identity-context residual is residues whose minimal reverse cost is exactly 19; quotient those and test forward context transition",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
