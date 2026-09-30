#!/usr/bin/env python3
"""V60: pull actual affine centres back to one fixed residual-streak origin.

V58 proved on every genuine residual centre switch in the prospective corpus:
the post-return owner is strictly closer 2-adically to the next affine centre
than to the old one. Pulling each future centre through the already executed
affine maps converts that local statement into approximations of one fixed
starting owner m0.

For a streak with
  m_i = (Abar_i*m0+Bbar_i)/Pbar_i
and local centre c_i, define
  C_i = (Pbar_i*c_i-Bbar_i)/Abar_i.
Then v2(m0-C_i) is the source-coordinate precision of the i-th centre.

V60 checks:
  * precision is constant across same-centre repeats and strictly increases at
    every genuine centre switch;
  * whether the pulled-centre approximation is unusually strong relative to
    rational height (the prerequisite for a p-adic Diophantine obstruction);
  * whether the pulled centres stay in any simple real-sign/height regime.

This is bounded theorem discovery, not Collatz QED.
"""
from __future__ import annotations

from collections import defaultdict, Counter
from fractions import Fraction
import hashlib, json

import collatz_crystal_nonpositive_budget_kernel_v53 as v53

def v2z(x: int):
    x = abs(x)
    if x == 0:
        return None
    return (x & -x).bit_length() - 1

def rat_v2(x: Fraction):
    if x == 0:
        return None
    return v2z(x.numerator) - v2z(x.denominator)

def center(row):
    return Fraction(row["B"], row["P"] - row["A"])

def height_bits(x: Fraction):
    return max(abs(x.numerator).bit_length(), x.denominator.bit_length())

# Group residual-to-residual transition rows by actual source + anchor.
groups = defaultdict(list)
for tr in v53.transitions:
    if tr["src"]["residual"] and tr["kind"] == "RESIDUAL":
        groups[(tr["source"], tr["anchor"])].append(tr)
for g in groups.values():
    g.sort(key=lambda tr: (tr["src"]["k0"], tr["src"]["k1"]))

streaks = []
same_precision_ok = True
switch_precision_ok = True
max_ratio_num = 0.0
max_ratio_row = None
min_height_surplus = None
precision_jump_hist = Counter()
switches = 0
same = 0
all_rows = []

for (source, anchor), trs in groups.items():
    # Split if the transition chain is not contiguous.
    chunks = []
    cur = []
    for tr in trs:
        if cur and cur[-1]["dst"]["k0"] != tr["src"]["k0"]:
            chunks.append(cur); cur = []
        cur.append(tr)
    if cur: chunks.append(cur)

    for chunk in chunks:
        # Build states: src of first + each dst.
        states = [chunk[0]["src"]] + [tr["dst"] for tr in chunk]
        m_start = states[0]["m0"]
        Abar, Bbar, Pbar = 1, 0, 1
        rows = []
        prev_pull = None
        prev_prec = None
        prev_local_center = None
        for i, s in enumerate(states):
            c = center(s)
            pulled = (Pbar * c - Bbar) / Abar
            prec = rat_v2(Fraction(m_start) - pulled)
            assert prec is not None
            hb = height_bits(pulled)
            ratio = prec / hb if hb else 0.0
            surplus = hb - prec
            if min_height_surplus is None or surplus < min_height_surplus:
                min_height_surplus = surplus
            if ratio > max_ratio_num:
                max_ratio_num = ratio
                max_ratio_row = {
                    "source": str(source), "anchor": anchor,
                    "state_index": i, "precision": prec,
                    "height_bits": hb, "ratio": ratio,
                    "pulled_center": [pulled.numerator, pulled.denominator],
                    "local_center": [c.numerator, c.denominator],
                    "depth": [s["k0"], s["k1"]],
                }

            relation = "START"
            if prev_pull is not None:
                same_local = c == prev_local_center
                # Pullback source centre itself is unchanged by another use of
                # the same fixed-point law.
                same_pulled = pulled == prev_pull
                if same_local:
                    same += 1
                    same_precision_ok &= same_pulled and prec == prev_prec
                    relation = "SAME_CENTER"
                else:
                    switches += 1
                    jump = prec - prev_prec
                    precision_jump_hist[jump] += 1
                    switch_precision_ok &= jump > 0
                    relation = "SWITCH"
            rows.append({
                "index": i,
                "depth": [s["k0"], s["k1"]],
                "law": [str(s["A"]), str(s["B"]), str(s["P"]), s["D"]],
                "local_center": [c.numerator, c.denominator],
                "pulled_center": [pulled.numerator, pulled.denominator],
                "source_precision_v2": prec,
                "height_bits": hb,
                "precision_over_height_bits": ratio,
                "real_sign": -1 if pulled < 0 else (1 if pulled > 0 else 0),
                "relation_from_previous": relation,
            })
            # Advance to next state.
            Abar, Bbar, Pbar = (
                s["A"] * Abar,
                s["A"] * Bbar + s["B"] * Pbar,
                s["P"] * Pbar,
            )
            prev_pull, prev_prec, prev_local_center = pulled, prec, c

        streaks.append({
            "source": str(source), "anchor": anchor,
            "states": len(states),
            "switches": sum(r["relation_from_previous"] == "SWITCH" for r in rows),
            "same_center_repeats": sum(r["relation_from_previous"] == "SAME_CENTER" for r in rows),
            "rows": rows,
        })
        all_rows.extend(rows)

# Longest / most informative streaks.
streaks.sort(key=lambda z: (-z["states"], -z["switches"], int(z["source"])))

sign_hist = Counter(r["real_sign"] for r in all_rows)
precision_hist = Counter(r["source_precision_v2"] for r in all_rows)
max_precision = max((r["source_precision_v2"] for r in all_rows), default=None)
max_height = max((r["height_bits"] for r in all_rows), default=None)

result = {
    "schema": "COLLATZ_CRYSTAL_PULLED_CENTRE_HEIGHT_V60",
    "parents": {
        "V53": "collatz-crystal-nonpositive-budget-kernel-v53@2b49ce24eb1593e045a7e1b7bcb8782f3f426d02",
        "V58": "collatz-crystal-actual-centre-switch-v58@0cb10d7c7ccc62e10564cf6147a0dae3a6f0085d",
    },
    "streaks": len(streaks),
    "same_center_steps": same,
    "centre_switches": switches,
    "same_center_preserves_pulled_center_and_precision": same_precision_ok,
    "every_switch_strictly_increases_source_precision": switch_precision_ok,
    "precision_jump_histogram": dict(sorted(precision_jump_hist.items())),
    "pulled_center_sign_histogram": dict(sorted(sign_hist.items())),
    "max_source_precision_v2": max_precision,
    "max_pulled_center_height_bits": max_height,
    "minimum_height_bits_minus_precision": min_height_surplus,
    "max_precision_over_height_bits": max_ratio_num,
    "max_ratio_witness": max_ratio_row,
    "longest_streaks": streaks[:20],
    "verdict": (
        "SOURCE_PULLBACK_PRECISION_MONOTONE_BUT_NOT_HEIGHT_BREAKING"
        if same_precision_ok and switch_precision_ok and max_ratio_num <= 1.25
        else "PULLED_CENTRE_DIOPHANTINE_SEPARATOR"
    ),
    "interpretation": (
        "Actual-centre switching becomes a strictly improving sequence of "
        "2-adic rational approximants to one fixed starting owner after source "
        "pullback. The height comparison tests whether this improvement is "
        "strong enough to invoke a p-adic rational-approximation obstruction. "
        "A ratio near or below 1 means precision is paid for by comparable "
        "arithmetic height and no Roth/Ridout-style finish is earned."
    ),
    "promotion_boundary": (
        "Prospective-corpus exact arithmetic only. Even monotone pulled-centre "
        "precision does not exclude an infinite natural orbit unless one proves "
        "a universal height/denominator restriction or another source-coherence "
        "obstruction."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
