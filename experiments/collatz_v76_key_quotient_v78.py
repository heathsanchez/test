#!/usr/bin/env python3
"""V78: find the minimum source-free key projection restoring V76 admission.

V76 showed law identity alone is too coarse. V77 localized the exact separator:
none of the three law-only witness edges is admitted by frozen V53.

Rather than retain a 613-edge table, this experiment asks whether the already
available V53 source-free key can be quotient-compressed so that
    (current affine law, projected key)
has a deterministic next projected residual/progress/exit consequence.

All 2^6 coordinate subsets are tested exactly on the frozen V53 transition
authority. A zero-collision subset is a bounded sufficient interface for this
one-step protected transition relation. Minimal zero-collision subsets are the
smallest lawful refinements of V76's law-only state on this boundary.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import redirect_stdout
from itertools import combinations
import hashlib
import io
import json
import os
import sys

frozen = os.environ.get("V60_EXPERIMENTS_DIR")
if frozen:
    sys.path.insert(0, frozen)

with redirect_stdout(io.StringIO()):
    import collatz_crystal_nonpositive_budget_kernel_v53 as v53

PARENT_V77_QUAL = "05edc33ae3bc6f1d186b8e0c0f015d8585f72693b1853fe2d7c39f10cc6fef82"
FIELDS = ["anchor", "forced", "rho", "nearest", "radius", "extra"]
L0 = (2187,1785,2048,11)
L1 = (2187,1417,1024,10)


def law(row):
    return (int(row["A"]), int(row["B"]), int(row["P"]), int(row["D"]))


def proj(key, subset):
    return tuple(key[i] for i in subset)


trs = [tr for tr in v53.transitions if tr["src"]["residual"]]
assert trs


def transition_signature(tr, subset):
    src = (law(tr["src"]), proj(tr["src"]["key"], subset))
    if tr["kind"] == "EXIT":
        out = ("EXIT",)
    else:
        d = tr["dst"]
        assert d is not None
        out = (tr["kind"], law(d), proj(d["key"], subset))
    return src, out


def audit_subset(subset):
    outs = defaultdict(set)
    rows = defaultdict(int)
    for tr in trs:
        s, o = transition_signature(tr, subset)
        outs[s].add(o)
        rows[s] += 1
    collisions = {s: os for s, os in outs.items() if len(os) > 1}
    return {
        "subset": list(subset),
        "fields": [FIELDS[i] for i in subset],
        "states": len(outs),
        "collision_states": len(collisions),
        "max_outcomes_per_state": max(map(len, outs.values()), default=0),
        "transition_rows": len(trs),
        "collision_rows": sum(rows[s] for s in collisions),
        "sample_collisions": [
            {
                "state": repr(s),
                "outcomes": sorted(map(repr, os))[:12],
                "rows": rows[s],
            }
            for s, os in list(sorted(collisions.items(), key=lambda z: repr(z[0])))[:12]
        ],
    }


audits = []
for k in range(len(FIELDS)+1):
    for subset in combinations(range(len(FIELDS)), k):
        audits.append(audit_subset(subset))

zero = [a for a in audits if a["collision_states"] == 0]
min_k = min((len(a["subset"]) for a in zero), default=None)
minimal = [a for a in zero if len(a["subset"]) == min_k] if min_k is not None else []

# Directly verify that each minimal quotient excludes V76's first fake edge.
witness_checks = []
for a in minimal:
    subset = tuple(a["subset"])
    allowed = defaultdict(set)
    for tr in trs:
        s, o = transition_signature(tr, subset)
        if law(tr["src"]) == L0:
            allowed[s].add(o)
    bad = []
    for s, os in allowed.items():
        for o in os:
            if len(o) >= 2 and o[1] == L1:
                bad.append((s,o))
    witness_checks.append({
        "fields": a["fields"],
        "l0_projected_states": len(allowed),
        "l0_allowed_outcome_count": sum(len(x) for x in allowed.values()),
        "admits_v76_first_fake_edge": bool(bad),
        "allowed_outcomes": [
            {"state": repr(s), "outcomes": sorted(map(repr, os))}
            for s, os in sorted(allowed.items(), key=lambda z: repr(z[0]))
        ][:12],
    })

law_only = next(a for a in audits if not a["subset"])
full_key = next(a for a in audits if len(a["subset"]) == len(FIELDS))

result = {
    "schema": "COLLATZ_V76_KEY_QUOTIENT_V78",
    "parent_v77_qualification_sha256": PARENT_V77_QUAL,
    "key_fields": FIELDS,
    "transition_rows": len(trs),
    "law_only": law_only,
    "full_key": full_key,
    "zero_collision_subsets": len(zero),
    "minimum_key_coordinates": min_k,
    "minimal_zero_collision_subsets": minimal,
    "minimal_witness_checks": witness_checks,
    "all_subset_summary": [
        {
            "fields": a["fields"],
            "collision_states": a["collision_states"],
            "collision_rows": a["collision_rows"],
            "states": a["states"],
        }
        for a in audits
    ],
    "interpretation": (
        "A zero-collision projection makes the frozen one-step protected "
        "transition relation factor through (affine law, projected source-free key). "
        "The minimum such projection is the least refinement licensed by V76/V77 "
        "on this finite authority. This does not establish all-depth completeness."
    ),
    "global_collatz": "UNKNOWN",
    "qed": False,
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
