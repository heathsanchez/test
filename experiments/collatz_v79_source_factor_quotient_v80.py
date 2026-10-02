#!/usr/bin/env python3
"""V80: source-factor quotient tournament after V79's 44-bit separator.

V79 showed that full V53 key + affine law + low 44 bits of t makes the frozen
one-step protected transition deterministic, while 43 bits leave one collision.

V53's challenge source is constructed from three natural factors:
  r      : low 9-bit binary residue,
  motif  : frozen 30-bit binary suffix family,
  a      : ternary class modulo 3^6,
with t = t2 + 2^39*k.

This gate asks whether the needed source distinction factors through a much
smaller meaningful coordinate (especially ternary precision) and simultaneously
re-tournaments all 64 subsets of the six source-free key coordinates.
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

PARENT_V79_QUAL = "d382875d5083c6d3e2254744e2dde40688f6c0296f35a29a2257e3f205394f7f"
KEY_FIELDS = ["anchor", "forced", "rho", "nearest", "radius", "extra"]

def law(row):
    return (int(row["A"]), int(row["B"]), int(row["P"]), int(row["D"]))

trs = [tr for tr in v53.transitions if tr["src"]["residual"]]
assert trs

def source_parts(tr):
    t = int(tr["t"])
    src = tr["src"]
    r = t % (1 << v53.BASE_DEPTH)
    motif = src["motif"]
    a = t % v53.MOD3
    pattern = v53.MOTIFS[motif]
    t2 = r + (v53.pattern_bits(pattern) << v53.BASE_DEPTH)
    assert (t - t2) % v53.M2 == 0
    k = (t - t2) // v53.M2
    assert 0 <= k < v53.MOD3
    return r, motif, a, k

SOURCE_DESCRIPTORS = [("none", lambda tr: ())]
for q in range(1, 7):
    m = 3**q
    SOURCE_DESCRIPTORS.append((f"a_mod_3^{q}", lambda tr, m=m: (source_parts(tr)[2] % m,)))
for q in range(1, 11):
    mask = (1 << q) - 1
    SOURCE_DESCRIPTORS.append((f"k_low_{q}", lambda tr, mask=mask: (source_parts(tr)[3] & mask,)))
SOURCE_DESCRIPTORS += [
    ("r", lambda tr: (source_parts(tr)[0],)),
    ("motif", lambda tr: (source_parts(tr)[1],)),
    ("a_exact", lambda tr: (source_parts(tr)[2],)),
    ("k_exact", lambda tr: (source_parts(tr)[3],)),
    ("r_motif", lambda tr: source_parts(tr)[:2]),
    ("r_a", lambda tr: (source_parts(tr)[0], source_parts(tr)[2])),
    ("motif_a", lambda tr: (source_parts(tr)[1], source_parts(tr)[2])),
    ("r_motif_a", lambda tr: source_parts(tr)[:3]),
]

def keyproj(key, subset):
    return tuple(key[i] for i in subset)

def audit(desc_fn, subset):
    outs = defaultdict(set)
    rows = defaultdict(int)
    for tr in trs:
        sp = desc_fn(tr)
        s = (law(tr["src"]), keyproj(tr["src"]["key"], subset), sp)
        if tr["kind"] == "EXIT":
            o = ("EXIT",)
        else:
            d = tr["dst"]
            assert d is not None
            o = (tr["kind"], law(d), keyproj(d["key"], subset), sp)
        outs[s].add(o)
        rows[s] += 1
    coll = {s:o for s,o in outs.items() if len(o)>1}
    return {
        "collision_states": len(coll),
        "collision_rows": sum(rows[s] for s in coll),
        "states": len(outs),
        "max_outcomes": max(map(len, outs.values()), default=0),
    }

summary = []
for name, fn in SOURCE_DESCRIPTORS:
    zeros = []
    best_collision = None
    best_examples = []
    for n in range(len(KEY_FIELDS)+1):
        for subset in combinations(range(len(KEY_FIELDS)), n):
            z = audit(fn, subset)
            rec = {
                "key_fields": [KEY_FIELDS[i] for i in subset],
                **z,
            }
            if best_collision is None or z["collision_states"] < best_collision:
                best_collision = z["collision_states"]
                best_examples = [rec]
            elif z["collision_states"] == best_collision and len(best_examples)<12:
                best_examples.append(rec)
            if z["collision_states"] == 0:
                zeros.append(rec)
        if zeros:
            break
    summary.append({
        "source_descriptor": name,
        "minimum_key_coordinates_if_zero": (
            len(zeros[0]["key_fields"]) if zeros else None
        ),
        "minimal_zero_collision_key_sets": zeros[:20],
        "best_collision_states": best_collision,
        "best_examples": best_examples[:12],
    })

def get(name):
    return next(x for x in summary if x["source_descriptor"]==name)

first_a_q = next(
    (q for q in range(1,7)
     if get(f"a_mod_3^{q}")["minimum_key_coordinates_if_zero"] is not None),
    None,
)
first_k_q = next(
    (q for q in range(1,11)
     if get(f"k_low_{q}")["minimum_key_coordinates_if_zero"] is not None),
    None,
)

result = {
    "schema": "COLLATZ_V79_SOURCE_FACTOR_QUOTIENT_V80",
    "parent_v79_qualification_sha256": PARENT_V79_QUAL,
    "transition_rows": len(trs),
    "key_fields": KEY_FIELDS,
    "descriptor_summary": summary,
    "first_sufficient_ternary_precision_q": first_a_q,
    "first_sufficient_k_low_bits": first_k_q,
    "exact_factor_status": {
        name: {
            "minimum_key_coordinates_if_zero": get(name)["minimum_key_coordinates_if_zero"],
            "minimal_zero_collision_key_sets": get(name)["minimal_zero_collision_key_sets"],
        }
        for name in ["r","motif","a_exact","k_exact","r_motif","r_a","motif_a","r_motif_a"]
    },
    "interpretation": (
        "The smallest surviving source distinction should be expressed in the "
        "native source factorization, not as an arbitrary 44-bit prefix. This "
        "tournament identifies which source factor and which residual key fields "
        "are actually required for the frozen protected transition to factor."
    ),
    "global_collatz": "UNKNOWN",
    "qed": False,
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
