#!/usr/bin/env python3
"""Crystal V17: four-thirds odd-budget frontier, with adversarial local countermodels.

This cycle does two different jobs and never confuses them:

1. Actual protected prefixes (bounded discovery only): replay the exact shortcut
   map, stopping at direct descent or the already-Lean-verified quarter-splice
   event.  Measure the source budget W = 4*n - 3*q only at odd protected states.

2. Adversarial abstraction: search tuples satisfying the currently formal local
   V16 waist (source class, q=floor(4n/3), qmin corridor, owner floor, and the
   universal source-relative growth inequality) without enforcing the exact
   parity-word/source-admission recurrence.  Any odd tuple here is a separator:
   it proves those local inequalities alone cannot derive the boundary parity.

No larger source census is used.  The finite replay boundary is the same 2^20
scale already used by the weighted-coalescence V15 gate.  Universal claims are
never promoted from either finite search.
"""
from __future__ import annotations
import json

LIMIT = 1 << 20
CAP = 4096
SOURCE_CLASSES = {3, 7, 15, 19}

def T(x: int) -> int:
    return (3*x + 1)//2 if x & 1 else x//2

def owner_normal(x: int):
    r = 0
    while x % 8 == 5:
        x = (x - 1)//4
        r += 1
    return r, x

def qmin(k: int) -> int:
    q = 0
    p3 = 1
    p2 = 1 << k
    while p3 < p2:
        p3 *= 3
        q += 1
    return q

# ---------------------------------------------------------------------------
# Cycle A: actual protected odd-budget frontier.
# ---------------------------------------------------------------------------
tested = direct = splice = censored = 0
odd_states = 0
min_budget = None
min_witness = None
class_min = {}
boundary_entrants = 0
boundary_odd = 0
first_boundary = []

for n in range(3, LIMIT, 2):
    tested += 1
    x = n
    q = 0
    for k in range(CAP + 1):
        if x < n:
            direct += 1
            break
        if x % 8 == 5 and x <= 4*n:
            splice += 1
            break

        W = 4*n - 3*q
        if x & 1:
            odd_states += 1
            r, p = owner_normal(x)
            row = {
                "n": n, "k": k, "q": q, "x": x, "budget": W,
                "source_mod24": n % 24, "owner_depth": r, "owner": p,
            }
            if min_budget is None or W < min_budget:
                min_budget = W
                min_witness = row
            c = n % 24
            if c in SOURCE_CLASSES and (c not in class_min or W < class_min[c]["budget"]):
                class_min[c] = row

        Q = (4*n)//3
        if q == Q:
            boundary_entrants += 1
            if x & 1:
                boundary_odd += 1
            if len(first_boundary) < 20:
                r, p = owner_normal(x) if x & 1 else (None, None)
                first_boundary.append({
                    "n": n, "k": k, "q": q, "x": x,
                    "parity": x & 1, "owner_depth": r, "owner": p,
                })
            # If the state is even, continue: the next forced state still has q=Q.
            # Any odd state at this same q would be the exact V17 obstruction.

        if x & 1:
            q += 1
        x = T(x)
    else:
        censored += 1

# This is discovery evidence, not a theorem.  Pin the exact finite result so a
# regression cannot silently change the scientific statement.
assert tested == (LIMIT - 3 + 1)//2
assert censored == 0
assert min_budget == 3, (min_budget, min_witness)
assert min_witness["n"] == 27 and min_witness["q"] == 35
assert min_witness["x"] == 325
assert min_witness["owner_depth"] == 1 and min_witness["owner"] == 81
assert boundary_odd == 0

# ---------------------------------------------------------------------------
# Cycle B: adversarial V16-local abstraction.
# Search for an odd boundary tuple satisfying every *local numerical* theorem
# we currently possess, but not the exact parity-word admission equation.
# This is deliberately a countermodel search, not evidence against Collatz.
# ---------------------------------------------------------------------------
synthetic = None
for n in range(27, 400, 2):
    if n % 24 not in SOURCE_CLASSES:
        continue
    q = (4*n)//3
    for k in range(q, 2*q + 1):
        qm = qmin(k)
        if qm > q + 1:
            continue
        # Source-relative nondescending envelope:
        # 2^k n^q x <= (3n+1)^q n.
        den = (1 << k) * (n ** q)
        xmax = ((3*n + 1) ** q * n) // den
        if xmax < n:
            continue
        # Find the first odd normalized-owner tuple above the source.
        start = n if n & 1 else n + 1
        for x in range(start, min(xmax, 20*n) + 1, 2):
            r, p = owner_normal(x)
            if p < n or p % 8 == 5:
                continue
            B = (1 << k)*x - (3 ** q)*n
            if B < 0:
                continue
            synthetic = {
                "n": n, "q": q, "k": k, "qmin": qm, "x": x,
                "xmax_from_source_relative_envelope": xmax,
                "owner_depth": r, "owner": p,
                "bias_required": B,
                "budget": 4*n - 3*q,
                "satisfies_local_v16_waist": True,
                "missing_constraint": "exact parity-word/source-admission recurrence for bias B",
            }
            break
        if synthetic is not None:
            break
    if synthetic is not None:
        break

assert synthetic is not None
assert synthetic["x"] & 1
assert synthetic["budget"] in (0, 1)

result = {
    "schema": "COLLATZ_CRYSTAL_FOUR_THIRDS_BUDGET_V17",
    "actual_boundary": {
        "limit": LIMIT,
        "step_cap": CAP,
        "tested_odd_sources": tested,
        "direct_exit_sources": direct,
        "quarter_splice_sources": splice,
        "censored": censored,
        "protected_odd_states": odd_states,
        "minimum_odd_budget": min_budget,
        "minimum_odd_budget_witness": min_witness,
        "source_class_minima": {str(k): v for k, v in sorted(class_min.items())},
        "boundary_states_seen": boundary_entrants,
        "boundary_odd_states": boundary_odd,
        "first_boundary_states": first_boundary,
    },
    "adversarial_abstraction": {
        "first_synthetic_odd_boundary_countermodel": synthetic,
        "conclusion": (
            "V16 local inequalities + owner floor + source-relative growth do not imply "
            "boundary evenness; an exact source/parity-word admission law is necessary."
        ),
    },
    "candidate": {
        "name": "ProtectedOddBudgetGap",
        "statement": (
            "on every direct/quarter-protected prefix with odd endpoint, "
            "3*oddCount(n,k)+3 <= 4*n"
        ),
        "why_decisive": (
            "at q=floor(4n/3), a minimal-bad source has budget 0 or 1, "
            "so the odd-budget gap forces the boundary state even; V16 then closes Collatz"
        ),
        "status": "CANDIDATE_ONLY",
    },
    "residual": {
        "name": "FOUR_THIRDS_PARITY_WORD_SOURCE_ADMISSION",
        "statement": (
            "derive the +3 odd-budget gap from the exact frozen-source affine recurrence "
            "2^k*T^k(n)=3^q*n+bias(n,k), including the parity-word admission constraints "
            "on bias; do not replace this by local envelope inequalities or a larger census"
        ),
        "universal": "UNKNOWN",
    },
    "global_collatz": "UNKNOWN",
}
print(json.dumps(result, indent=2))
