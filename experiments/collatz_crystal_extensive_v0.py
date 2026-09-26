#!/usr/bin/env python3
"""Crystal-style extensive experiment selection over the live Collatz residual.

Uses only exact/warranted consequences already available on this branch plus
fresh arithmetic checks. It deliberately distinguishes protected-consequence
experiments from presentation-coordinate separators.

No Collatz theorem is claimed.
"""
from __future__ import annotations
import json, math
import collatz_reverse_trit_bicell_v2 as v2
import collatz_reverse_trit_separator_v0 as v0
import collatz_symbolic_merge as sm

G=v0.G
PARENTS=v2.parent_residuals()
assert len(PARENTS)==27
H=[f"bicell:{i}" for i in range(27)]

def minimax(hypotheses, table):
    scored=[]
    partitions={}
    for action, outcomes in table.items():
        groups={}
        for h in hypotheses:
            groups.setdefault(outcomes[h],[]).append(h)
        worst=max(map(len,groups.values()))
        scored.append((worst,action))
        partitions[action]={k:sorted(v) for k,v in groups.items()}
    worst,action=min(scored)
    return action,worst,partitions[action]

# 1. Entire low-bit source-gap family: exact universal negative.
# For M=2^a, if G>=M-1, then for any endpoint residue e and any source
# residue r choose delta=(e-r) mod M in [0,M-1] subset [0,G].
lowbit_rows=[]
for a in range(1,40):
    M=1<<a
    saturated=G>=M-1
    lowbit_rows.append(dict(depth=a,modulus=M,saturated=saturated))
first_possible=next(x["depth"] for x in lowbit_rows if not x["saturated"])
assert first_possible==32
assert all(x["saturated"] for x in lowbit_rows[:31])

# 2. Existing exact certificate families on all 27 parent bicells.
# By construction each is residual after direct reverse and one-forward reverse.
table={}
table["direct_reverse_certificate"]={h:"RESIDUAL" for h in H}
table["one_forward_then_reverse"]={h:"RESIDUAL" for h in H}
for a in range(1,32):
    table[f"gap_plus_q2_depth_{a}"]={h:"ALL_SOURCE_RESIDUES_POSSIBLE" for h in H}

# 3. Re-run protected endpoint Q2 refinement through depth 12.
# The protected observation is the entire survivor-language fingerprint/count,
# not parent identity. All 27 parents must remain consequence-equivalent.
live={i:{1} for i in range(27)}
endpoint_rows=[]
for a in range(1,13):
    if a>1:
        bit=1<<(a-1)
        live={i:{x for s in vals for x in (s,s|bit)} for i,vals in live.items()}
    nxt={}
    for i,vals in live.items():
        keep=set()
        for s in vals:
            if v2.composed_certificate(PARENTS[i],s,a) is None:
                keep.add(s)
        nxt[i]=keep
    live=nxt
    langs=[tuple(sorted(live[i])) for i in range(27)]
    distinct=len(set(langs))
    assert distinct==1
    fp=hash(langs[0]) # run-local diagnostic only; equality above is authority
    endpoint_rows.append(dict(depth=a,count=len(langs[0]),distinct_parent_languages=distinct))
    table[f"protected_endpoint_q2_depth_{a}"]={h:f"LANGUAGE_COUNT:{len(langs[0])}" for h in H}

# 4. Source coefficient-persistence + gap at depth <=20 cannot repair the
# low-bit saturation: source residual may shrink, but every surviving source
# residue is compatible with every endpoint residue because delta spans all
# residues modulo 2^a. Re-run exact source residual count at depth 18.
_bank,source_residual,_exc=sm.compile_portfolio(18)
assert len(source_residual)==6342
table["source_persistence_depth18_plus_gap"]={h:"NO_PARENT_SEPARATOR" for h in H}

# 5. Protected minimax selection over all COMPLETE exact experiments.
chosen,worst,partition=minimax(H,table)
assert worst==27

# 6. Presentation coordinates can separate labels but are not protected
# consequences, so they are deliberately outside the admissible action set.
presentation={
 "first_difference_depth":{h:str(PARENTS[i]["depth"]) for i,h in enumerate(H)},
 "alternate_digit":{h:str(PARENTS[i]["alternate_digit"]) for i,h in enumerate(H)},
 "q3_residue":{h:str(PARENTS[i]["residue"]) for i,h in enumerate(H)},
}
presentation_scores={}
for action,outcomes in presentation.items():
    _,w,p=minimax(H,{action:outcomes})
    presentation_scores[action]=dict(worst_case=w,groups=len(p))

# 7. The missing source-admission intervention has no complete prediction table.
# Crystal must fail closed rather than pretend it is a separator.
source_admission_missing=len(H)

result={
 "schema":"COLLATZ_CRYSTAL_EXTENSIVE_V0",
 "hypotheses":len(H),
 "complete_protected_experiments":len(table),
 "prediction_rows":len(H)*len(table),
 "fresh_endpoint_replay_depth":12,
 "fresh_endpoint_rows":endpoint_rows,
 "lowbit_gap_family":{
   "tested_depths":39,
   "provably_nonseparating_depths":[1,31],
   "first_potentially_informative_depth":first_possible,
   "reason":"G >= 2^a-1 implies every source residue mod 2^a is compatible with every endpoint residue"
 },
 "source_portfolio_depth18_residual_cylinders":len(source_residual),
 "protected_separator":{
   "status":"EXCLUDED",
   "chosen_action":chosen,
   "worst_case_survivors":worst,
   "reason":"no_separator_in_complete_warranted_action_set"
 },
 "presentation_only_diagnostics":presentation_scores,
 "presentation_coordinates_admitted_as_experiments":False,
 "source_admission_query":{
   "status":"UNKNOWN",
   "reason":"incomplete_prediction_table",
   "missing_predictions":source_admission_missing,
   "needed":"exact source-admission outcome for each of 27 bicells"
 },
 "crystal_residual":{
   "id":"SOURCE_ADMISSION_OVER_27_BICELLS",
   "smallest_new_information":"a source-admission predicate stronger than any Q2 residue test of depth <=31",
   "first_lowbit_depth_not_ruled_out":32,
   "preferred_symbolic_route":"exact high-depth/valuation source-cylinder admission rather than enumerating deeper endpoint prefixes"
 },
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2,sort_keys=True))
