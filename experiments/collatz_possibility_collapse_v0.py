#!/usr/bin/env python3
"""Possibility-collapse audit for the canonical Collatz residual.

This is an epistemic gate, not a proof. It encodes the exact current boundary:
local/finite projections are not allowed to masquerade as universal closure.
"""
import json
routes=[
 {"route":"bounded finite-state / bounded-window contraction","status":"REJECTED",
  "reason":"formal no-go: arbitrarily long Mersenne/critical adversaries defeat every bounded-window finite-state multiplier"},
 {"route":"endpoint-only / static source language / Farey rung","status":"REJECTED",
  "reason":"qualified internal negative controls; protected future quotient and source admission do not close"},
 {"route":"historical P37 -> two-block core as universal entry","status":"REJECTED_AS_UNPROVED",
  "reason":"P37 is strong finite structure; P39/P40 core authority is a frozen residual corpus, not all canonical M>=0 cylinders"},
 {"route":"historical two-block recurrent core itself","status":"CLOSED",
  "reason":"exact A/B replay: B has no exact A/B successor; A^infinity requires a negative rational source"},
 {"route":"Ansari automatic 4*3^44+2 interval extension","status":"REJECTED_EXTERNAL_SHORTCUT",
  "reason":"independent audit found a defect in the printed ternary induction; extension is not accepted as proof authority"},
 {"route":"generic p-adic two-log bound on 3^q R+B","status":"NOT_APPLICABLE_AS_STATED",
  "reason":"B is a word-dependent growing S-unit sum, not a fixed algebraic base; generic Yu/Chim two-log bounds do not directly bound this moving cocycle"},
 {"route":"globally mechanical/Sturmian itinerary exclusion","status":"VALID_BUT_COVERAGE_MISSING",
  "reason":"mechanical tails are excluded, but no theorem forces every canonical M>=0 itinerary to become mechanical"},
 {"route":"P28 eventual polynomial canonical-residue lower bound","status":"OPEN_SUFFICIENT",
  "reason":"would close, but is itself a universal stopping/realizability theorem; fixed-rate exponential lower bound already has near-rational counterexamples"},
 {"route":"P30/P31 cross-scale joint transducer","status":"LIVE",
  "reason":"must use one integer's coherent 2-adic source and 3-adic shadow across unbounded scales; finite prefixes alone are provably insufficient"}
]
assert sum(r["status"]=="LIVE" for r in routes)==1
result={
 "schema":"COLLATZ_POSSIBILITY_COLLAPSE_V0",
 "canonical_residual":"nontrivial legal first-crossing canonical cylinder with M>=0",
 "already_forced":["actual source = canonical R","common tail u=0","terminal carry e=0"],
 "routes":routes,
 "sole_live_research_route":"P30/P31 cross-scale joint transducer / coherence",
 "required_new_theorem":"exclude an infinite coherent positive-integer path through the joint low-R/high-B 2-adic/3-adic survivor system",
 "warning":"that theorem is not currently proved; asserting it would be asserting Collatz in a renamed form",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
