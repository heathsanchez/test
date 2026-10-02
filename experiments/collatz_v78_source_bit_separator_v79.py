#!/usr/bin/env python3
"""V79: minimum source-parameter refinement after V78 full-key failure.

V78 proved that (affine law, full six-coordinate V53 source-free key) still
has 38 one-step future collisions on the frozen V53 authority. This gate adds
only the lowest b bits of the source parameter t and finds the first b that
restores deterministic projected next consequence.

If no bit depth through the exact binary t suffices, the gate tests whether
adding temporal return depth k0 is the next forced distinction.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import redirect_stdout
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

PARENT_V78_QUAL = "97261bd68f006b6d61deabf9356126fd6861dcf9043b3ce082f8b603d7a0a854"

def law(row):
    return (int(row["A"]), int(row["B"]), int(row["P"]), int(row["D"]))

trs = [tr for tr in v53.transitions if tr["src"]["residual"]]
assert trs
max_t_bits = max(int(tr["t"]).bit_length() for tr in trs)


def audit(bits=None, exact_t=False, include_k0=False):
    outs = defaultdict(set)
    rows = defaultdict(int)
    for tr in trs:
        src = tr["src"]
        if exact_t:
            source_part = int(tr["t"])
        else:
            mask = (1 << bits) - 1 if bits else 0
            source_part = int(tr["t"]) & mask

        state = (law(src), src["key"], source_part)
        if include_k0:
            state = state + (int(src["k0"]),)

        if tr["kind"] == "EXIT":
            out = ("EXIT",)
        else:
            d = tr["dst"]
            assert d is not None
            out = (tr["kind"], law(d), d["key"], source_part)
            if include_k0:
                out = out + (int(d["k0"]),)

        outs[state].add(out)
        rows[state] += 1

    coll = {s:o for s,o in outs.items() if len(o) > 1}
    return {
        "bits": bits,
        "exact_t": exact_t,
        "include_k0": include_k0,
        "states": len(outs),
        "collision_states": len(coll),
        "collision_rows": sum(rows[s] for s in coll),
        "max_outcomes_per_state": max(map(len, outs.values()), default=0),
        "sample_collisions": [
            {
                "state": repr(s),
                "outcomes": sorted(map(repr, os))[:12],
                "rows": rows[s],
            }
            for s,os in list(sorted(coll.items(), key=lambda z: repr(z[0])))[:12]
        ],
    }


bit_audits = []
first_zero = None
for b in range(max_t_bits + 1):
    a = audit(bits=b)
    bit_audits.append(a)
    if a["collision_states"] == 0:
        first_zero = b
        break

exact = audit(exact_t=True)
exact_k0 = audit(exact_t=True, include_k0=True)

result = {
    "schema": "COLLATZ_V78_SOURCE_BIT_SEPARATOR_V79",
    "parent_v78_qualification_sha256": PARENT_V78_QUAL,
    "transition_rows": len(trs),
    "max_t_bit_length": max_t_bits,
    "bit_audits": bit_audits,
    "minimum_low_source_bits": first_zero,
    "exact_t_audit": exact,
    "exact_t_plus_k0_audit": exact_k0,
    "status": (
        "LOW_SOURCE_BITS_SUFFICIENT" if first_zero is not None
        else "EXACT_T_SUFFICIENT" if exact["collision_states"] == 0
        else "EXACT_T_PLUS_K0_SUFFICIENT" if exact_k0["collision_states"] == 0
        else "SOURCE_AND_K0_STILL_INSUFFICIENT"
    ),
    "interpretation": (
        "This is the least source/provenance refinement test licensed by V78. "
        "A first zero-collision bit depth means the frozen protected one-step "
        "transition factors through full key + law + that many low t bits. "
        "Failure even for exact t implies temporal position is consequential."
    ),
    "global_collatz": "UNKNOWN",
    "qed": False,
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
