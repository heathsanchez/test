#!/usr/bin/env python3
"""Exact bounded census of source-order coalescence descent.

Process sources increasingly.  The owner table stores an exact previously
constructed forward occurrence T^b(p)=y with p smaller than every future
source.  For n, follow its actual shortcut orbit only until it first enters
that already-certified smaller-source future.  This produces a concrete
LowerMerge witness (p,a,b) without requiring direct descent.

Finite theorem-discovery evidence only; universal Collatz remains UNKNOWN.
"""
import json

LIMIT = (1 << 20) - 1
STEP_CAP = 10000

def T(n: int) -> int:
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2

def replay(n: int, k: int) -> int:
    x = n
    for _ in range(k):
        x = T(x)
    return x

# State -> (smallest processed source owning this state, source-forward depth).
# Source 1 owns 1 at depth 0 and 2 at depth 1.
owner = {1: (1, 0), 2: (1, 1)}

record_depth = -1
records = []
certified = 0
merge_at_start = 0
merge_above_source = 0
max_state = 2

for n in range(2, LIMIT + 1):
    x = n
    path = []  # states before first entry into an earlier source future
    if x in owner:
        a = 0
    else:
        for a in range(STEP_CAP + 1):
            if x in owner:
                break
            path.append(x)
            max_state = max(max_state, x)
            x = T(x)
        else:
            raise AssertionError(("STEP_CAP", n, x))

    p, b = owner[x]
    assert 0 < p < n, (n, p, a, b, x)
    # Exact lower-merge replay.
    assert replay(n, a) == x
    assert replay(p, b) == x
    certified += 1
    if a == 0:
        merge_at_start += 1
    if x >= n:
        merge_above_source += 1

    if a > record_depth:
        record_depth = a
        records.append({
            "source": n,
            "coalescence_depth": a,
            "meeting_state": x,
            "smaller_source": p,
            "smaller_source_depth": b,
        })

    # n is now an admissible smaller source for later sources.  Preserve the
    # first/smallest owner for states already known from an earlier source.
    for d, y in enumerate(path):
        owner.setdefault(y, (n, d))

expected = [
    (2, 0),
    (3, 4),
    (7, 7),
    (27, 59),
    (703, 81),
    (35655, 135),
    (270271, 161),
    (362343, 165),
    (401151, 167),
    (1027431, 183),
]
got = [(r["source"], r["coalescence_depth"]) for r in records]
assert got == expected, got

result = {
    "schema": "COLLATZ_COALESCENCE_RECORD_CENSUS_V1",
    "source_limit": LIMIT,
    "sources_certified": certified,
    "owner_states": len(owner),
    "merge_at_start": merge_at_start,
    "merge_after_forward_steps": certified - merge_at_start,
    "meeting_state_at_or_above_source": merge_above_source,
    "record_count": len(records),
    "record_rows": records,
    "max_coalescence_depth": record_depth,
    "max_state_indexed": str(max_state),
    "interpretation": (
        "Source-order coalescence removes many independent descent obligations, "
        "but the record residual remains sparse and unbounded-looking; the "
        "universal theorem is not established by this finite census."
    ),
    "next": (
        "Mine only the record-source actual prefixes for a source-changing "
        "parametric certificate; do not return to population P or a fixed time bound."
    ),
    "global_collatz": "UNKNOWN",
}
print(json.dumps(result, indent=2))
