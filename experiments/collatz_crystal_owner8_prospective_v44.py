#!/usr/bin/env python3
"""Crystal V44: prospective test of the V43-earned +8 dyadic owner separator.

V43 rejected its frozen (c=2,d=6) training quotient on held-out motifs, but
the postmortem combined corpus had a smaller structural description:
    exact return signature + exact normalized V23 source parameter t
    + the next 8 owner bits after the return law's forced (D+1) bits
was functional, with no extra owner Q3 coordinate.

V44 freezes exactly c=8,d=0 BEFORE this new challenge. It then:
  1. replays the V43 combined corpus and requires zero collisions at +8 bits;
  2. expands to a disjoint, wider exact source family:
       64 V25 depth-9 live cells
       x all t mod 3^5 classes
       x six new 24-bit adversarial suffix motifs;
  3. fails closed on censoring, zero-defect returns, or any repeated protected
     key with distinct next consequences;
  4. diagnostically reports the minimum dyadic lookahead c on the combined
     prior+prospective corpus, without retuning the frozen candidate.

This is bounded separator evidence only. QED still needs an all-depth symbolic
right-congruence/progress theorem feeding V37 hprogress.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
import hashlib
import io
import json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_dynamic_owner_separator_v43 as v43
    import collatz_crystal_parameter_quotient_v25 as v25
    import collatz_crystal_phase_normalized_return_v40 as v40

FROZEN_C = 8
SUFFIX_BITS = 24
MOD3 = 3**5
CAP = 1200

MOTIFS = {
    "P001101": "001101",
    "P111001": "111001",
    "P010011": "010011",
    "P101100": "101100",
    "P00010111": "00010111",
    "P01111000": "01111000",
}

M2 = 1 << (v43.BASE_DEPTH + SUFFIX_BITS)
INV2 = pow(M2, -1, MOD3)


def pattern_bits(pattern: str) -> int:
    x = 0
    for i in range(SUFFIX_BITS):
        x |= int(pattern[i % len(pattern)]) << i
    return x


def crt_parameter(r: int, a: int, pattern: str) -> int:
    t2 = r + (pattern_bits(pattern) << v43.BASE_DEPTH)
    k = ((a - t2) * INV2) % MOD3
    t = t2 + M2 * k
    assert t % (1 << v43.BASE_DEPTH) == r
    assert t % MOD3 == a
    return t


def frozen_key(row, c: int = FROZEN_C):
    extra = (row["m0"] >> row["forced_bits"]) & ((1 << c) - 1) if c else 0
    return (row["sig"], row["t"], extra)


def functional(rows, c: int):
    outs = defaultdict(set)
    first = {}
    for row in rows:
        k = frozen_key(row, c)
        outs[k].add(row["label"])
        first.setdefault((k, row["label"]), row)
    bad = [(k, v) for k, v in outs.items() if len(v) > 1]
    bad.sort(key=lambda kv: repr(kv[0]))
    witness = None
    if bad:
        k, labels = bad[0]
        ls = sorted(labels, key=repr)
        ws = []
        for lab in ls[:4]:
            row = first[(k, lab)]
            ws.append({
                "source_name": row["source_name"],
                "t": str(row["t"]),
                "source": str(row["source"]),
                "m0": str(row["m0"]),
                "forced_bits": row["forced_bits"],
                "phase": row["phase"],
                "occurrence": row["occurrence"],
                "depth": [row["k0"], row["k1"]],
                "prev_sig": repr(row["prev_sig"]),
                "label": repr(lab),
            })
        witness = {
            "key": repr(k),
            "labels": [repr(x) for x in ls[:8]],
            "witnesses": ws,
        }
    return {
        "keys": len(outs),
        "collision_keys": len(bad),
        "first_collision": witness,
    }


def collect_run_rows(name: str, t: int, n: int):
    rr = v40.actual_episode_returns(name, n, CAP)
    rows = []
    stats = Counter()
    if rr["note"] == "ordinary exit before zero-tail":
        stats["EXIT_PRE_ZERO"] += 1
        return rows, stats

    stats["POST_ZERO_SOURCE"] += 1
    if rr["first_exit"] is None:
        stats["SOURCE_CENSORED"] += 1
    else:
        stats["EXIT_" + rr["first_exit"]["kind"]] += 1

    by = defaultdict(list)
    for e in rr["events"]:
        if e["zero_defect"]:
            stats["ZERO_DEFECT_EVENT"] += 1
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
            rows.append({
                "source_name": name,
                "t": t,
                "source": n,
                "sig": v43.return_signature(e),
                "label": label,
                "m0": e["m0"],
                "forced_bits": e["cert"]["D"] + 1,
                "k0": e["k0"],
                "k1": e["k1"],
                "zero_depth": rr["zero_depth"],
                "phase": e["k0"] - rr["zero_depth"],
                "occurrence": i,
                "prev_sig": ("START",) if i == 0 else v43.return_signature(es[i - 1]),
            })
            stats["ROWS"] += 1
    return rows, stats


# Reconstruct all exact t values from both prior motif banks, including sources
# that exited pre-zero and therefore contributed no row.
prior_t = set()
for r in v43.LIVE:
    for a in range(v43.MOD3):
        for pattern in list(v43.TRAIN_MOTIFS.values()) + list(v43.HOLDOUT_MOTIFS.values()):
            prior_t.add(v43.crt_parameter(r, a, pattern))

prior_rows = list(v43.train_rows) + list(v43.hold_rows)
prior_check = functional(prior_rows, FROZEN_C)
assert prior_check["collision_keys"] == 0, prior_check

rows = []
stats = Counter()
sources = 0
overlap_skipped = 0
first_censored = None
first_zero = None

for r in v43.LIVE:
    for a in range(MOD3):
        for mname, pattern in MOTIFS.items():
            t = crt_parameter(r, a, pattern)
            if t in prior_t:
                overlap_skipped += 1
                continue
            n = v25.N0 + v25.NC * t
            name = f"prospective-r{r}-a{a}-{mname}"
            rr_rows, rr_stats = collect_run_rows(name, t, n)
            rows.extend(rr_rows)
            stats.update(rr_stats)
            sources += 1
            if rr_stats["SOURCE_CENSORED"] and first_censored is None:
                first_censored = {
                    "r": r, "a": a, "motif": mname,
                    "t": str(t), "source": str(n),
                }

# Frozen candidate is evaluated on the prospective family itself and on the
# full accumulated corpus. Exact t in the key prevents cross-source aliasing;
# the test is whether one source can revisit the same protected state with a
# different lawful future.
prospective_check = functional(rows, FROZEN_C)
combined_rows = prior_rows + rows
combined_check = functional(combined_rows, FROZEN_C)

# Diagnostic growth law: how many next owner bits are required as the source
# family expands? This does not retune the frozen c=8 candidate.
dyadic_frontier = {}
minimum_combined = None
for c in range(0, 17):
    z = functional(combined_rows, c)
    dyadic_frontier[str(c)] = {
        "collision_keys": z["collision_keys"],
        "keys": z["keys"],
    }
    if minimum_combined is None and z["collision_keys"] == 0:
        minimum_combined = c

if stats["SOURCE_CENSORED"]:
    verdict = "PROSPECTIVE_CENSORED_NO_PROMOTION"
elif stats["ZERO_DEFECT_EVENT"]:
    verdict = "ZERO_DEFECT_OBSTRUCTION_EMITTED"
elif combined_check["collision_keys"]:
    verdict = "FROZEN_OWNER8_QUOTIENT_REJECTED"
else:
    verdict = "BOUNDED_OWNER8_QUOTIENT_SURVIVES_WIDER_PROSPECTIVE_CHALLENGE"

result = {
    "schema": "COLLATZ_CRYSTAL_OWNER8_PROSPECTIVE_V44",
    "parent": "collatz-crystal-dynamic-owner-separator-v43@f36deeed50755d0ad416a997fdf7b4314dbaebc4",
    "frozen_candidate": {
        "extra_owner_q2_bits": FROZEN_C,
        "extra_owner_q3_trits": 0,
        "key": "(return_signature, exact normalized t, next 8 owner bits after D+1)",
        "prior_combined_replay": prior_check,
    },
    "prospective_challenge": {
        "v25_depth": v43.BASE_DEPTH,
        "live_binary_cells": len(v43.LIVE),
        "ternary_classes": MOD3,
        "suffix_bits": SUFFIX_BITS,
        "motifs": list(MOTIFS),
        "exact_sources": sources,
        "overlap_skipped": overlap_skipped,
        "rows": len(rows),
        "stats": dict(sorted(stats.items())),
        "first_censored": first_censored,
        "first_zero_defect": first_zero,
        "frozen_check": prospective_check,
    },
    "combined_frozen_check": combined_check,
    "diagnostic_dyadic_frontier": dyadic_frontier,
    "diagnostic_minimum_combined_extra_bits": minimum_combined,
    "verdict": verdict,
    "interpretation": (
        "V44 freezes the V43 postmortem +8-bit dynamic owner separator before "
        "a disjoint challenge that widens both the suffix horizon and ternary "
        "source fibres. Any collision is an earned separator; survival is only "
        "bounded evidence for a finite-lookahead dyadic right-congruence."
    ),
    "promotion_boundary": (
        "QED requires a symbolic theorem deriving the successor from the "
        "phase-normalized return law plus the warranted dynamic coordinate, "
        "and a well-founded progress measure instantiating V37 hprogress."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
