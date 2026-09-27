#!/usr/bin/env python3
"""Meta-Crystal over the canonical Collatz programme.

Object being quotiented: promoted/superseded research capabilities, not Collatz
trajectory states.  Protected consequence: whether a capability changes the
existence/construction of a strictly-smaller-source coalescence certificate.

This is an epistemic/compiler experiment.  It does NOT prove Collatz.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import collatz_reverse_predecessor_tree as pred
from collatz_live_origin_bridge_v1 import language_counts, first_crossing

Q = 14
M = 3 ** Q

# Canonical, supersession-aware programme rows.  These are deliberately semantic
# representatives, not a census of every historical experiment file.
ROWS = [
    # Proof / normalization shell.
    dict(id="ordinary_exit_reduction", status="WARRANTED", effect="PROOF_SHELL"),
    dict(id="source_order_strong_induction", status="CANDIDATE_LOGICAL_COMPRESSION", effect="PROOF_SHELL"),
    dict(id="source_product_normalization", status="WARRANTED", effect="NORMALIZATION"),
    dict(id="fixed_origin_zero_tail", status="WARRANTED", effect="NORMALIZATION"),

    # Constructors of the single protected terminal consequence.
    dict(id="direct_forward_descent", status="WARRANTED", effect="LOWER_SOURCE_CERTIFICATE"),
    dict(id="inverse_odd", status="WARRANTED", effect="LOWER_SOURCE_CERTIFICATE"),
    dict(id="q7_reverse_predecessor", status="WARRANTED", effect="LOWER_SOURCE_CERTIFICATE"),
    dict(id="q14_reverse_predecessor", status="WARRANTED", effect="LOWER_SOURCE_CERTIFICATE"),
    dict(id="target_directed_reverse_search", status="REUSABLE_BOUNDED", effect="LOWER_SOURCE_CERTIFICATE"),
    dict(id="first_crossing_direct_descent", status="WARRANTED_BOUNDED_AND_CONDITIONAL", effect="LOWER_SOURCE_CERTIFICATE"),

    # Constraints on a hypothetical certificate-free survivor.
    dict(id="first_crossing_rigidity_gap", status="WARRANTED", effect="SURVIVOR_CONSTRAINT"),
    dict(id="q14_reverse_height_barrier", status="WARRANTED", effect="SURVIVOR_CONSTRAINT"),
    dict(id="q_source_squeeze", status="WARRANTED_CONDITIONAL", effect="SURVIVOR_CONSTRAINT"),
    dict(id="zero_exit_carry_normal_form", status="WARRANTED", effect="SURVIVOR_CONSTRAINT"),
    dict(id="coefficient_corridor_escape", status="WARRANTED_NECESSARY", effect="SURVIVOR_CONSTRAINT"),
    dict(id="stationary_source_threshold_scan", status="WARRANTED_BOUNDED", effect="SURVIVOR_CONSTRAINT"),

    # Proof devices that do not add a protected consequence.
    dict(id="uniform_block_B", status="REJECTED", effect="NO_PROTECTED_GAIN"),
    dict(id="population_P_as_final_rank", status="SUPERSEDED", effect="NO_PROTECTED_GAIN"),
    dict(id="static_affine_deficit_separator", status="REJECTED", effect="NO_PROTECTED_GAIN"),
    dict(id="q14_height_only_kernel_closure", status="REJECTED", effect="NO_PROTECTED_GAIN"),
    dict(id="fixed_bounded_residue_quotient", status="REJECTED", effect="NO_PROTECTED_GAIN"),
    dict(id="three_adic_only_closure", status="REJECTED", effect="NO_PROTECTED_GAIN"),
    dict(id="phase_blind_translation_uniform_fourier", status="REJECTED", effect="NO_PROTECTED_GAIN"),
    dict(id="p37_parent_rejection_rank", status="REJECTED", effect="NO_PROTECTED_GAIN"),
    dict(id="running_coefficient_ceiling_rank", status="REJECTED", effect="NO_PROTECTED_GAIN"),
]

# --- Meta-separator 1: prove the newest strong-reverse Q14 cover is not a new
# protected distinction.  It is exactly the prior q/source squeeze mask in the
# conditional q<=n regime:
#
# strong reverse: a/d <= 3/4  <=>  L=d/a >= 4/3
# q/source squeeze: 3(L-1) >= 1 <=> L >= 4/3.
certs = pred.enumerate_first_contractions(Q)
bar = [Fraction(1, 1) for _ in range(M)]
strong = bytearray(M)
for c in certs:
    L = Fraction(c.d, c.a)
    for r in range(c.residue, M, c.d):
        if L > bar[r]:
            bar[r] = L
        if r % 3 == 1 and 4 * c.a <= 3 * c.d:
            strong[r] = 1

squeeze = bytearray(M)
for r in range(1, M, 3):
    if 3 * (bar[r] - 1) >= 1:
        squeeze[r] = 1

assert strong == squeeze
hard_total = M // 3
killed = sum(strong)
assert killed == 33723
assert hard_total - killed == 1560600

# --- Meta-separator 2: replay the hardest currently exposed stationary-source
# records through BOTH constructor families.  This is only bounded evidence.
HARD = [
    13421671, 14378779, 8088063, 12132095, 9280639,
    13774695, 1126015, 2252031, 1689023, 6206655,
]
qmin, _, _ = language_counts(2000)

by = {}
for c in certs:
    by.setdefault(c.d, {}).setdefault(c.residue, []).append(c)

def T(x: int) -> int:
    return (3 * x + 1) // 2 if x & 1 else x // 2

def best_lower_reverse(y: int, n: int):
    hit = None
    for d, rows in by.items():
        for c in rows.get(y % d, ()):
            num = c.a * y - c.c
            if num % d:
                continue
            p = num // d
            if not (0 < p < n):
                continue
            assert pred.reverse_apply(y, c.word) == p
            cand = (p, c.steps, c.word)
            if hit is None or cand < hit:
                hit = cand
    return hit

hard_rows = []
reverse_before = 0
direct_at_cross = 0
combined_by_cross = 0
for n in HARD:
    y = n
    first_reverse = None
    crossing = None
    crossing_y = None
    for j in range(1, 2001):
        y = T(y)
        if first_reverse is None:
            h = best_lower_reverse(y, n)
            if h is not None:
                first_reverse = dict(j=j, y=y, p=h[0], steps=h[1], word=h[2])
        # Use the same exact coefficient-threshold crossing authority as the
        # qualified live-origin bridge.
        z = first_crossing(n, qmin)
        if z is not None:
            crossing, crossing_y, _ = z
        if crossing is not None and j >= crossing:
            break
    before = first_reverse is not None and first_reverse["j"] < crossing
    descent = crossing_y is not None and crossing_y < n
    reverse_before += int(before)
    direct_at_cross += int(descent)
    combined_by_cross += int(before or descent)
    hard_rows.append(dict(
        n=n,
        crossing=crossing,
        crossing_endpoint=crossing_y,
        direct_descent_at_cross=descent,
        first_q14_lower_reverse=first_reverse,
        reverse_before_cross=before,
    ))

assert reverse_before == 4
assert direct_at_cross == len(HARD)
assert combined_by_cross == len(HARD)

# Quotient canonical results by protected effect.
classes = {}
for row in ROWS:
    classes.setdefault(row["effect"], []).append(dict(id=row["id"], status=row["status"]))

result = {
    "schema": "COLLATZ_PROGRAMME_META_CRYSTAL_V1",
    "scope": "supersession-aware canonical Collatz programme representatives plus exact replay of current hard records",
    "protected_terminal_consequence": "LOWER_SOURCE_CERTIFICATE(n): exists p<n and a,b with T^a(n)=T^b(p)",
    "logical_shell": "If LOWER_SOURCE_CERTIFICATE(n) holds for every n>1, strong induction on source order proves every trajectory reaches 1.",
    "proof_obligation_compression": {
        "old_devices_not_required_as_obligations": [
            "source-independent finite waiting bound",
            "strict decrease of aggregate P on a uniform block",
            "independent time-indexed carry rank",
            "Q14 height-kernel emptiness",
            "a universal scalar rank on trajectory snapshots",
        ],
        "single_remaining_obligation": "prove total coverage of every fixed positive source by at least one sound lower-source certificate constructor",
    },
    "protected_effect_quotient": classes,
    "exact_meta_deduplication": {
        "new_strong_reverse_q14_vs_prior_q_source_squeeze_q_le_n": {
            "equivalent_masks": True,
            "reason": "4*a<=3*d iff L=d/a>=4/3 iff 3*(L-1)>=1",
            "hard_classes": hard_total,
            "killed": killed,
            "survivors": hard_total-killed,
            "consequence": "NO_NEW_PROTECTED_SEPARATOR",
        }
    },
    "bounded_constructor_coverage_replay": {
        "records": len(HARD),
        "q14_reverse_merge_strictly_before_cross": reverse_before,
        "direct_descent_at_first_coefficient_cross": direct_at_cross,
        "covered_by_cross_by_union": combined_by_cross,
        "rows": hard_rows,
        "boundary": "ten current hard 24-bit stationary-source record survivors only; not a universal proof",
    },
    "meta_crystal_promotion": {
        "name": "LOWER_SOURCE_CONSTRUCTOR_COVERAGE",
        "status": "CANDIDATE",
        "statement": "For every n>1, some finite actual-orbit prefix enters the verified domain of a constructor that emits p<n with a common future.",
        "why_this_is_smaller": "all successful forward, reverse, crossing and carry results matter only through whether they construct or force this certificate; timing/rank representations are auxiliary",
    },
    "highest_leverage_unknown": "totality of the lower-source constructor bank on an arbitrary actual fixed-source no-OrdinaryExit path",
    "next_experiment": {
        "name": "constructor-coverage compiler",
        "instruction": "Run every verified constructor on actual long-lived source prefixes, label the earliest valid lower-source certificate, quotient prefixes by the minimum observations needed to select a constructor, and hold out harder source scales. Emit exact uncovered residuals instead of a new scalar rank.",
        "protected_output": "(n,k,constructor,p,a,b) with p<n and independently replayed T^a(n)=T^b(p)",
    },
    "global_collatz": "UNKNOWN",
}
print(json.dumps(result, indent=2))
