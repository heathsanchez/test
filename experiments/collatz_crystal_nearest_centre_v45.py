#!/usr/bin/env python3
"""Crystal V45: reuse A8 nearest-3-adic-centre state on the V44 residual.

V44 falsified a frozen +8 dyadic owner window and the minimum observed
lookahead grew to +10 bits as the source family widened. Rather than chase a
larger fixed prefix, V45 asks whether the older A8 structural coordinate
compresses those dynamic distinctions.

From every exact same-anchor law observed across the accumulated V40--V44
corpus, form its 3-adic fixed-point centre
    q = B / (2^D - A).
Centres are reduced as exact rationals and grouped by episode anchor.

For each current return state m:
  * retain its intrinsic Q2 return cylinder (anchor, D+1, rho);
  * find the centre(s) maximizing v3(m-q);
  * retain the canonical nearest-centre identity + radius, or the full tied
    nearest-centre set as a stronger control;
  * keep exact normalized source parameter t fixed so this test isolates the
    dynamic coordinate, not source aliasing.

The gate compares:
  baseline current-return signature,
  Q2 + nearest centre/radius,
  full current law + nearest centre/radius,
  Q2 + tied nearest-centre set/radius,
  and the V44 +10 dyadic-prefix control.

This is a bounded representation diagnostic, not a Collatz proof.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import redirect_stdout
from math import gcd
import hashlib
import io
import json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_owner8_prospective_v44 as v44

rows = list(v44.combined_rows)


def v3_nonzero(x: int) -> int:
    x = abs(x)
    assert x != 0
    v = 0
    while x % 3 == 0:
        x //= 3
        v += 1
    return v


def normalize_center(A: int, B: int, D: int):
    C = (1 << D) - A
    assert C != 0
    num, den = B, C
    if den < 0:
        num, den = -num, -den
    g = gcd(abs(num), den)
    return (num // g, den // g)


# Exact centre bank induced by all accumulated laws, but quotient law identity
# down to centre identity. This is the representation object A8 actually used.
centres = defaultdict(set)
law_count = 0
for row in rows:
    anchor, A, B, D, rho, _vr, _res = row["sig"]
    centres[anchor].add(normalize_center(A, B, D))
    law_count += 1
centres = {a: tuple(sorted(cs)) for a, cs in centres.items()}

center_id = {}
id_center = {}
next_id = 0
for anchor in sorted(centres):
    for c in centres[anchor]:
        center_id[(anchor, c)] = next_id
        id_center[next_id] = (anchor, c)
        next_id += 1


def center_distance_v3(m: int, center):
    num, den = center
    z = den * m - num
    if z == 0:
        return None  # +infinity / exact centre
    return v3_nonzero(z) - v3_nonzero(den)


def nearest_state(row):
    anchor = row["sig"][0]
    scored = []
    exact = []
    for c in centres[anchor]:
        v = center_distance_v3(row["m0"], c)
        cid = center_id[(anchor, c)]
        if v is None:
            exact.append(cid)
        else:
            scored.append((v, cid))
    if exact:
        ids = tuple(sorted(exact))
        return {
            "radius": "INF",
            "ids": ids,
            "canonical": ids[0],
            "exact": True,
        }
    assert scored
    best = max(v for v, _ in scored)
    ids = tuple(sorted(cid for v, cid in scored if v == best))
    return {
        "radius": best,
        "ids": ids,
        "canonical": ids[0],
        "exact": False,
    }


nearest_cache = {}
for row in rows:
    # m + anchor is enough to cache; same m may appear under different current
    # laws but nearest-centre semantics is anchor-relative.
    ck = (row["sig"][0], row["m0"])
    if ck not in nearest_cache:
        nearest_cache[ck] = nearest_state(row)


def q2(row):
    anchor, A, B, D, rho, _vr, _res = row["sig"]
    return (anchor, D + 1, rho)


def current_law(row):
    return row["sig"][:5]


def extra_owner(row, c: int):
    if c == 0:
        return 0
    return (row["m0"] >> row["forced_bits"]) & ((1 << c) - 1)


def key_for(row, mode):
    ns = nearest_cache[(row["sig"][0], row["m0"])]
    if mode == "BASELINE":
        return (row["sig"], row["t"])
    if mode == "Q2_NEAREST":
        return (q2(row), row["t"], ns["canonical"], ns["radius"])
    if mode == "LAW_NEAREST":
        return (current_law(row), row["t"], ns["canonical"], ns["radius"])
    if mode == "Q2_NEAREST_SET":
        return (q2(row), row["t"], ns["ids"], ns["radius"])
    if mode == "OWNER10_CONTROL":
        return (row["sig"], row["t"], extra_owner(row, 10))
    if mode == "EXACT_OWNER_CONTROL":
        return (row["sig"], row["t"], row["m0"])
    raise KeyError(mode)


def functionality(mode):
    outs = defaultdict(set)
    first = {}
    for row in rows:
        k = key_for(row, mode)
        outs[k].add(row["label"])
        first.setdefault((k, row["label"]), row)
    bad = [(k, vs) for k, vs in outs.items() if len(vs) > 1]
    bad.sort(key=lambda kv: repr(kv[0]))
    witness = None
    if bad:
        k, vs = bad[0]
        labs = sorted(vs, key=repr)
        ws = []
        for lab in labs[:4]:
            row = first[(k, lab)]
            ns = nearest_cache[(row["sig"][0], row["m0"])]
            ws.append({
                "source_name": row["source_name"],
                "t": str(row["t"]),
                "source": str(row["source"]),
                "m0": str(row["m0"]),
                "q2": repr(q2(row)),
                "current_law": repr(current_law(row)),
                "nearest_ids": list(ns["ids"]),
                "nearest_radius": ns["radius"],
                "depth": [row["k0"], row["k1"]],
                "phase": row["phase"],
                "occurrence": row["occurrence"],
                "label": repr(lab),
            })
        witness = {
            "key": repr(k),
            "labels": [repr(x) for x in labs[:8]],
            "witnesses": ws,
        }
    return {
        "keys": len(outs),
        "collision_keys": len(bad),
        "first_collision": witness,
    }


modes = {}
for mode in (
    "BASELINE",
    "Q2_NEAREST",
    "LAW_NEAREST",
    "Q2_NEAREST_SET",
    "OWNER10_CONTROL",
    "EXACT_OWNER_CONTROL",
):
    modes[mode] = functionality(mode)

exact_hits = []
for (anchor, m), ns in nearest_cache.items():
    if ns["exact"]:
        exact_hits.append({
            "anchor": anchor,
            "m": str(m),
            "center_ids": list(ns["ids"]),
        })

if modes["Q2_NEAREST"]["collision_keys"] == 0:
    verdict = "Q2_NEAREST_CENTRE_RADIUS_FUNCTIONAL_ON_ACCUMULATED_CORPUS"
elif modes["LAW_NEAREST"]["collision_keys"] == 0:
    verdict = "LAW_NEAREST_CENTRE_RADIUS_FUNCTIONAL_ON_ACCUMULATED_CORPUS"
elif modes["Q2_NEAREST_SET"]["collision_keys"] == 0:
    verdict = "Q2_NEAREST_CENTRE_SET_RADIUS_FUNCTIONAL_ON_ACCUMULATED_CORPUS"
else:
    verdict = "NEAREST_CENTRE_REVIVAL_DOES_NOT_CLOSE_DYNAMIC_SUCCESSOR"

result = {
    "schema": "COLLATZ_CRYSTAL_NEAREST_CENTRE_V45",
    "parent": "collatz-crystal-owner8-prospective-v44@e2989adf620a2d365952a552e22d0e4a543b6f87",
    "corpus": {
        "rows": len(rows),
        "sources_are_exact_t_keyed": True,
        "anchors": len(centres),
        "distinct_centres": sum(len(v) for v in centres.values()),
        "centres_by_anchor": {str(a): len(v) for a, v in sorted(centres.items())},
    },
    "modes": modes,
    "exact_center_hits": exact_hits[:50],
    "exact_center_hit_count": len(exact_hits),
    "verdict": verdict,
    "interpretation": (
        "V45 tests whether the older A8 ultrametric state captures the dynamic "
        "distinction that caused required dyadic owner lookahead to grow from "
        "8 to 10 bits. Centre identity is exact rational B/(2^D-A), not law name."
    ),
    "promotion_boundary": (
        "Functionality here is retrospective/bounded because the centre bank is "
        "induced from the accumulated corpus. A positive result must be frozen "
        "and challenged on unseen source families/return laws before promotion; "
        "universal QED additionally needs bank-growth transition/reselection and "
        "V37 hprogress."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
