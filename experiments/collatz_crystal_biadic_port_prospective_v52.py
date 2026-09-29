#!/usr/bin/env python3
"""V52: prospective frozen bi-adic-port challenge.

V46 retrospectively found that the state
  (Q2 return cylinder, exact normalized source t,
   frozen nearest 3-adic centre/radius,
   next c owner bits after the forced D+1 return cylinder)
is future-functional on its accumulated corpus at c=5.

This gate freezes BOTH the V45 centre bank and c=5, then challenges them on
an unseen wider source family:
  64 V25 depth-9 live cells
  x all t mod 3^6 classes
  x six new 30-bit suffix motifs
= 279,936 exact source candidates before overlap removal.

No new centre is admitted to the key.  New centres and anchors are recorded
as separators instead.  The gate fails closed on censoring, zero-defect
returns, missing frozen anchors, or a repeated frozen key with two lawful
future labels.

Bounded prospective falsifier only; no global Collatz claim.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
from math import gcd
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_biadic_port_v46 as v46
    import collatz_crystal_nearest_centre_v45 as v45
    import collatz_crystal_owner8_prospective_v44 as v44
    import collatz_crystal_dynamic_owner_separator_v43 as v43
    import collatz_crystal_parameter_quotient_v25 as v25
    import collatz_crystal_phase_normalized_return_v40 as v40

FROZEN_C = 5
BASE_DEPTH = 9
SUFFIX_BITS = 30
MOD3 = 3**6
CAP = 1600

MOTIFS = {
    "N00011101": "00011101",
    "N11100010": "11100010",
    "N01011001": "01011001",
    "N10100110": "10100110",
    "N001011101": "001011101",
    "N110100010": "110100010",
}

assert v46.selected["CANONICAL_NEAREST"] == FROZEN_C

def pattern_bits(pattern: str) -> int:
    x = 0
    for i in range(SUFFIX_BITS):
        x |= int(pattern[i % len(pattern)]) << i
    return x

M2 = 1 << (BASE_DEPTH + SUFFIX_BITS)
INV2 = pow(M2, -1, MOD3)

def crt_parameter(r: int, a: int, pattern: str) -> int:
    t2 = r + (pattern_bits(pattern) << BASE_DEPTH)
    k = ((a - t2) * INV2) % MOD3
    t = t2 + M2 * k
    assert t % (1 << BASE_DEPTH) == r
    assert t % MOD3 == a
    return t

# All source parameters that contributed to the V45/V46 frozen bank.
old_t = set(v44.prior_t)
for r in v43.LIVE:
    for a in range(v44.MOD3):
        for pattern in v44.MOTIFS.values():
            old_t.add(v44.crt_parameter(r, a, pattern))

def normalize_center(A: int, B: int, D: int):
    C = (1 << D) - A
    assert C != 0
    num, den = B, C
    if den < 0:
        num, den = -num, -den
    g = gcd(abs(num), den)
    return (num // g, den // g)

def frozen_nearest(anchor: int, m: int):
    bank = v45.centres.get(anchor)
    if bank is None:
        return None
    exact = []
    scored = []
    for centre in bank:
        cid = v45.center_id[(anchor, centre)]
        val = v45.center_distance_v3(m, centre)
        if val is None:
            exact.append(cid)
        else:
            scored.append((val, cid))
    if exact:
        ids = tuple(sorted(exact))
        return {"canonical": ids[0], "ids": ids, "radius": "INF"}
    assert scored
    best = max(v for v, _ in scored)
    ids = tuple(sorted(cid for v, cid in scored if v == best))
    return {"canonical": ids[0], "ids": ids, "radius": best}

def q2_of_event(e):
    c = e["cert"]
    return (e["anchor"], c["D"] + 1, c["rho"])

def frozen_key(row, c=FROZEN_C):
    extra = 0 if c == 0 else (
        (row["m0"] >> row["forced_bits"]) & ((1 << c) - 1)
    )
    return (
        row["q2"],
        row["t"],
        row["nearest_canonical"],
        row["nearest_radius"],
        extra,
    )

def functional(rows, c=FROZEN_C):
    outs = defaultdict(set)
    first = {}
    for row in rows:
        k = frozen_key(row, c)
        outs[k].add(row["label"])
        first.setdefault((k, row["label"]), row)
    bad = [(k, labs) for k, labs in outs.items() if len(labs) > 1]
    bad.sort(key=lambda z: repr(z[0]))
    witness = None
    if bad:
        k, labs = bad[0]
        ls = sorted(labs, key=repr)
        ws = []
        for lab in ls[:4]:
            z = first[(k, lab)]
            ws.append({
                "source_name": z["source_name"],
                "source": str(z["source"]),
                "t": str(z["t"]),
                "m0": str(z["m0"]),
                "q2": repr(z["q2"]),
                "nearest_canonical": z["nearest_canonical"],
                "nearest_radius": z["nearest_radius"],
                "extra_bits": frozen_key(z, c)[-1],
                "depth": [z["k0"], z["k1"]],
                "label": repr(lab),
            })
        witness = {
            "key": repr(k),
            "labels": [repr(x) for x in ls[:8]],
            "rows": ws,
        }
    return {
        "keys": len(outs),
        "collision_keys": len(bad),
        "first_collision": witness,
    }

# Requalify the frozen retrospective candidate before prospective use.
prior = v46.functional(FROZEN_C, False)
assert prior["collision_keys"] == 0, prior

rows = []
stats = Counter()
sources = 0
overlap_skipped = 0
new_centres = defaultdict(set)
missing_anchor = []
zero_defects = []
censored = []

for r in v43.LIVE:
    for a in range(MOD3):
        for motif, pattern in MOTIFS.items():
            t = crt_parameter(r, a, pattern)
            if t in old_t:
                overlap_skipped += 1
                continue
            n = v25.N0 + v25.NC * t
            name = f"v52-r{r}-a{a}-{motif}"
            rr = v40.actual_episode_returns(name, n, CAP)
            sources += 1

            if rr["note"] == "ordinary exit before zero-tail":
                stats["EXIT_PRE_ZERO"] += 1
                continue

            stats["POST_ZERO_SOURCE"] += 1
            if rr["first_exit"] is None:
                stats["SOURCE_CENSORED"] += 1
                if len(censored) < 20:
                    censored.append({
                        "source_name": name, "source": str(n), "t": str(t)
                    })

            by = defaultdict(list)
            for e in rr["events"]:
                if e["zero_defect"]:
                    stats["ZERO_DEFECT_EVENT"] += 1
                    if len(zero_defects) < 20:
                        zero_defects.append({
                            "source_name": name, "source": str(n), "t": str(t),
                            "anchor": e["anchor"], "depth": [e["k0"], e["k1"]],
                        })

                c = e["cert"]
                centre = normalize_center(c["A"], c["B"], c["D"])
                if centre not in v45.centres.get(e["anchor"], ()):
                    new_centres[e["anchor"]].add(centre)
                by[e["anchor"]].append(e)

            for anchor, es in by.items():
                es.sort(key=lambda z: (z["k0"], z["k1"]))
                for i, e in enumerate(es):
                    if i + 1 < len(es):
                        label = v43.successor_label(es[i + 1])
                    elif rr["first_exit"] is not None:
                        label = ("EXIT", rr["first_exit"]["kind"])
                    else:
                        stats["CENSORED_LAST_EVENT"] += 1
                        continue

                    ns = frozen_nearest(anchor, e["m0"])
                    if ns is None:
                        stats["MISSING_FROZEN_ANCHOR_ROW"] += 1
                        if len(missing_anchor) < 20:
                            missing_anchor.append({
                                "source_name": name, "source": str(n),
                                "t": str(t), "anchor": anchor,
                                "depth": [e["k0"], e["k1"]],
                                "law": repr(v43.return_signature(e)[:5]),
                            })
                        continue

                    c = e["cert"]
                    rows.append({
                        "source_name": name,
                        "source": n,
                        "t": t,
                        "m0": e["m0"],
                        "m1": e["m1"],
                        "sig": v43.return_signature(e),
                        "A": c["A"],
                        "B": c["B"],
                        "D": c["D"],
                        "q2": q2_of_event(e),
                        "nearest_canonical": ns["canonical"],
                        "nearest_radius": ns["radius"],
                        "forced_bits": c["D"] + 1,
                        "k0": e["k0"],
                        "k1": e["k1"],
                        "label": label,
                    })
                    stats["ROWS"] += 1

prospective = functional(rows, FROZEN_C)

frontier = {}
minimum = None
for c in range(0, 13):
    z = functional(rows, c)
    frontier[str(c)] = {
        "collision_keys": z["collision_keys"],
        "keys": z["keys"],
    }
    if minimum is None and z["collision_keys"] == 0:
        minimum = c

new_centres_count = sum(len(v) for v in new_centres.values())
new_anchor_ids = sorted(a for a in new_centres if a not in v45.centres)

if stats["SOURCE_CENSORED"] or stats["CENSORED_LAST_EVENT"]:
    verdict = "PROSPECTIVE_CENSORED_NO_PROMOTION"
elif stats["ZERO_DEFECT_EVENT"]:
    verdict = "ZERO_DEFECT_OBSTRUCTION_EMITTED"
elif stats["MISSING_FROZEN_ANCHOR_ROW"]:
    verdict = "FROZEN_CENTRE_BANK_NEW_ANCHOR_SEPARATOR"
elif prospective["collision_keys"]:
    verdict = "FROZEN_BIADIC_PORT_REJECTED"
else:
    verdict = "FROZEN_BIADIC_PORT_SURVIVES_PROSPECTIVE_CHALLENGE"

result = {
    "schema": "COLLATZ_CRYSTAL_BIADIC_PORT_PROSPECTIVE_V52",
    "parents": {
        "V45": "collatz-crystal-nearest-centre-v45@0797cd9f47688249ceabfd521a3ae85ed33bc088",
        "V46": "collatz-crystal-biadic-port-v46@0338343dadbbf56a4e44869b06c110049396f664",
    },
    "frozen": {
        "extra_owner_bits": FROZEN_C,
        "centre_bank_size": sum(len(v) for v in v45.centres.values()),
        "anchors": sorted(v45.centres),
        "prior_collision_keys": prior["collision_keys"],
    },
    "challenge": {
        "live_binary_cells": len(v43.LIVE),
        "ternary_classes": MOD3,
        "suffix_bits": SUFFIX_BITS,
        "motifs": list(MOTIFS),
        "exact_sources_tested": sources,
        "overlap_skipped": overlap_skipped,
        "cap": CAP,
    },
    "stats": dict(sorted(stats.items())),
    "prospective_frozen_check": prospective,
    "diagnostic_port_frontier": frontier,
    "diagnostic_minimum_fresh_extra_bits": minimum,
    "frozen_bank_growth": {
        "distinct_new_centres": new_centres_count,
        "new_centres_by_anchor": {
            str(a): len(v) for a, v in sorted(new_centres.items())
        },
        "new_anchor_ids": new_anchor_ids,
    },
    "first_missing_anchor_rows": missing_anchor,
    "zero_defects": zero_defects,
    "censored_sources": censored,
    "verdict": verdict,
    "interpretation": (
        "V52 freezes the V46 c=5 bi-adic state and the entire V45 rational "
        "centre bank before an unseen wider source challenge. New laws may be "
        "observed, but their centres are diagnostic only and never admitted "
        "to the frozen key."
    ),
    "promotion_boundary": (
        "Even survival proves only bounded prospective functionality. Universal "
        "use still needs an all-depth theorem bounding centre-bank/reselection "
        "and proving eventual positive affine budget or OrdinaryExit."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
