#!/usr/bin/env python3
"""Crystal V46: minimum dyadic port on the A8/V45 nearest-centre state.

V45 compressed 657 exact-source successor collisions to 9 with
  (intrinsic Q2 return cylinder, exact source t, nearest 3-adic centre, radius)
but did not close them. V44 showed that raw owner-prefix state alone required
10 extra dyadic bits on the same accumulated corpus.

V46 asks whether the two structures compose: how many *additional* owner Q2
bits beyond the return law's forced D+1 cylinder are needed once the
ultrametric nearest-centre state is present?

This is the exact A8 bi-adic question. We search c=0..16 for both canonical
nearest-centre identity and the full tied-nearest set. No held-out retuning is
performed here; the smallest closing c, if any, is only a candidate for a
subsequent prospective freeze.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import redirect_stdout
import hashlib
import io
import json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_nearest_centre_v45 as v45

rows = v45.rows


def extra_bits(row, c: int):
    if c == 0:
        return 0
    return (row["m0"] >> row["forced_bits"]) & ((1 << c) - 1)


def key(row, c: int, tied: bool):
    ns = v45.nearest_cache[(row["sig"][0], row["m0"])]
    centre = ns["ids"] if tied else ns["canonical"]
    return (
        v45.q2(row),
        row["t"],
        centre,
        ns["radius"],
        extra_bits(row, c),
    )


def functional(c: int, tied: bool):
    outs = defaultdict(set)
    first = {}
    for row in rows:
        k = key(row, c, tied)
        outs[k].add(row["label"])
        first.setdefault((k, row["label"]), row)
    bad = [(k, vs) for k, vs in outs.items() if len(vs) > 1]
    bad.sort(key=lambda kv: repr(kv[0]))
    witness = None
    if bad:
        k, vs = bad[0]
        labels = sorted(vs, key=repr)
        ws = []
        for lab in labels[:4]:
            row = first[(k, lab)]
            ns = v45.nearest_cache[(row["sig"][0], row["m0"])]
            ws.append({
                "source_name": row["source_name"],
                "t": str(row["t"]),
                "source": str(row["source"]),
                "m0": str(row["m0"]),
                "q2": repr(v45.q2(row)),
                "extra_bits": extra_bits(row, c),
                "nearest_ids": list(ns["ids"]),
                "nearest_radius": ns["radius"],
                "phase": row["phase"],
                "occurrence": row["occurrence"],
                "depth": [row["k0"], row["k1"]],
                "label": repr(lab),
            })
        witness = {
            "key": repr(k),
            "labels": [repr(x) for x in labels[:8]],
            "witnesses": ws,
        }
    return {
        "keys": len(outs),
        "collision_keys": len(bad),
        "first_collision": witness,
    }


frontiers = {}
selected = {}
for tied in (False, True):
    name = "NEAREST_SET" if tied else "CANONICAL_NEAREST"
    frontier = {}
    first_zero = None
    for c in range(17):
        z = functional(c, tied)
        frontier[str(c)] = {
            "keys": z["keys"],
            "collision_keys": z["collision_keys"],
            "first_collision": z["first_collision"] if c in (0,1,2,3,4,8,10,16) else None,
        }
        if first_zero is None and z["collision_keys"] == 0:
            first_zero = c
    frontiers[name] = frontier
    selected[name] = first_zero

if selected["CANONICAL_NEAREST"] is not None:
    verdict = "CANONICAL_NEAREST_PLUS_DYADIC_PORT_FUNCTIONAL"
elif selected["NEAREST_SET"] is not None:
    verdict = "NEAREST_SET_PLUS_DYADIC_PORT_FUNCTIONAL"
else:
    verdict = "BIADIC_PORT_UP_TO_16_BITS_DOES_NOT_CLOSE"

result = {
    "schema": "COLLATZ_CRYSTAL_BIADIC_PORT_V46",
    "parent": "collatz-crystal-nearest-centre-v45@0797cd9f47688249ceabfd521a3ae85ed33bc088",
    "corpus_rows": len(rows),
    "centre_bank_size": sum(len(v) for v in v45.centres.values()),
    "state": (
        "Q2 return cylinder + exact normalized source t + nearest 3-adic "
        "centre/radius + c residual owner Q2 bits"
    ),
    "minimum_closing_extra_bits": selected,
    "frontiers": frontiers,
    "raw_owner_reference": {
        "V44_minimum_extra_bits_same_corpus": 10,
        "V45_q2_nearest_collisions_at_c0": v45.modes["Q2_NEAREST"]["collision_keys"],
    },
    "verdict": verdict,
    "interpretation": (
        "V46 tests whether the growing raw owner prefix in V44 was compensating "
        "for missing 3-adic centre information. A materially smaller closing c "
        "is evidence for the intrinsic bi-adic state; a growing/large c rejects "
        "that compression on this corpus."
    ),
    "promotion_boundary": (
        "Any closing c is retrospective bounded evidence. Freeze it before new "
        "sources/return laws and test centre-bank growth before claiming a "
        "right-congruence. Global QED still requires V37 hprogress."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
