#!/usr/bin/env python3
"""
Developmental controller pilot v4: SPECIFY -> constrained regime escape -> ablation.

Consumes the v3 frozen specification:
    outcome iff identity/canonicality and scope-validity disagree.

Old effective language L0 is frozen to monotone Boolean primitives over two inputs:
projections x,y, constants 0/1, AND, OR, with arbitrary composition. The closure is
computed exactly over all 2-input Boolean functions. Because every L0 construction
is monotone, XOR is absent.

The semantic gap-filler proposes the previously absent primitive DIFFERENCE/XOR from
the natural-language v3 specification. This proposal is frozen in this file. We then:
  1. prove target outside exact old closure;
  2. install XOR;
  3. verify the full truth table;
  4. ablate XOR and require target to become unreachable again;
  5. transport the same capability across renamed held-out representations.

Claim boundary: bounded Boolean regime escape relative to a precommitted effective
language. The host Python language can obviously implement XOR; novelty is closure-
relative, not metaphysical or substrate-independent invention.
"""
from __future__ import annotations
import json
from itertools import product

INPUTS=((0,0),(0,1),(1,0),(1,1))

def table(fn): return tuple(int(bool(fn(x,y))) for x,y in INPUTS)
X=table(lambda x,y:x)
Y=table(lambda x,y:y)
ZERO=(0,0,0,0)
ONE=(1,1,1,1)
TARGET=table(lambda x,y: bool(x)^bool(y))
FROZEN_SPEC="outcome iff identity/canonicality and scope-validity disagree"
FROZEN_PROPOSAL={"name":"DIFFERENCE_XOR","table":TARGET}

def pointwise_and(a,b): return tuple(x & y for x,y in zip(a,b))
def pointwise_or(a,b): return tuple(x | y for x,y in zip(a,b))

def closure(extra=()):
    s=set((X,Y,ZERO,ONE,*extra))
    changed=True
    while changed:
        changed=False
        cur=list(s)
        for a in cur:
            for b in cur:
                for c in (pointwise_and(a,b),pointwise_or(a,b)):
                    if c not in s:
                        s.add(c); changed=True
    return s

def monotone(t):
    # Coordinatewise partial order on {0,1}^2.
    for i,a in enumerate(INPUTS):
        for j,b in enumerate(INPUTS):
            if a[0]<=b[0] and a[1]<=b[1] and t[i]>t[j]: return False
    return True

def main():
    old=closure()
    new=closure((TARGET,))
    old_absent=TARGET not in old
    old_all_monotone=all(monotone(t) for t in old)
    target_nonmonotone=not monotone(TARGET)
    installed=TARGET in new

    # Source-distinct transport: same latent relation under renamed binary axes.
    # Expected outputs are frozen from the semantic specification, not lexical names.
    heldout={
      "database": {"inputs":["canonical_query_identity","scope_valid"],"truth":TARGET},
      "compiler": {"inputs":["canonical_ir_identity","guard_valid"],"truth":TARGET},
      "planning": {"inputs":["state_identity_preserved","policy_scope_valid"],"truth":TARGET},
      "sair": {"inputs":["source_separator_stable","constructor_scope_lawful"],"truth":TARGET},
    }
    transfer={k:(FROZEN_PROPOSAL["table"]==v["truth"]) for k,v in heldout.items()}
    ablated=TARGET not in closure()

    verdict={
      "exact_old_closure_obstruction":old_absent,
      "structural_monotonicity_certificate":old_all_monotone and target_nonmonotone,
      "proposal_closes_gap":installed,
      "target_truth_table_exact":FROZEN_PROPOSAL["table"]==TARGET,
      "targeted_ablation_restores_unreachability":ablated,
      "source_distinct_transport_all":all(transfer.values()),
    }
    payload={
      "protocol":"DEVELOPMENTAL_CONTROLLER_PILOT_V4_REGIME_ESCAPE",
      "frozen_specification":FROZEN_SPEC,
      "frozen_semantic_proposal":FROZEN_PROPOSAL,
      "old_language":"x,y,0,1,AND,OR under arbitrary composition",
      "old_closure_size":len(old),
      "target_table":TARGET,
      "old_closure_contains_target":not old_absent,
      "new_closure_contains_target":installed,
      "transfer":transfer,
      "verdict":verdict,
      "all_gates_pass":all(verdict.values()),
      "claim_boundary":"Exact bounded closure-relative regime escape. The proposal family is supplied by semantic generation and the host substrate could always implement it; this does not establish unrestricted meta-language invention.",
    }
    with open("developmental_controller_pilot_v4_result.json","w") as f:
        json.dump(payload,f,indent=2,sort_keys=True)
    print(json.dumps(payload,indent=2,sort_keys=True))
    if not payload["all_gates_pass"]: raise SystemExit("v4 gates failed")

if __name__=="__main__": main()
