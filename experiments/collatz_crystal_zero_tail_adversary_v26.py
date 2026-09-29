#!/usr/bin/env python3
"""Crystal V26: adversarial finite-support zero-tail campaign after V25.

Parent authority:
  collatz-crystal-parameter-quotient-v25@3d33a5a44cbcf3546f44e4ecdd4d153bafa03fcc
  run 36525097815, artifact 11014637515

V25 found 64 exact nonterminal cells at parameter depth 9 and showed that
each closes under an immediate all-zero continuation, with worst wait 93 bits.
That is bounded evidence, not a theorem for a natural parameter whose higher
bits may contain more 1s.

This campaign does not widen an ordinary-source census.  It keeps only a small
stateful beam of the V25 residual.  At each generation it:
  1. expands the next forced parameter bit b in {0,1};
  2. scores children by their exact direct/splice zero-tail escape time;
  3. full-verifies the hardest children with the V25 D/S/M classifier;
  4. retains only the hardest verified nonterminal states.

The first purpose is falsification of the tempting "93 zeros always suffice"
abstraction.  If that bound survives, the emitted normalized signatures are
the smallest next objects for a right-congruence proof.  If it fails, the
first separator is retained and the bound is rejected.

This remains theorem-discovery evidence.  Global Collatz stays UNKNOWN.
"""
from __future__ import annotations

from collections import Counter
import json

import collatz_crystal_parameter_quotient_v25 as v25

PARENT = "collatz-crystal-parameter-quotient-v25@3d33a5a44cbcf3546f44e4ecdd4d153bafa03fcc"
PARENT_RUN = 36525097815
PARENT_ARTIFACT = 11014637515

SEED_DEPTH = 9
SEED_R = [
  132,388,68,196,452,12,268,332,204,460,300,172,428,28,284,412,
  220,476,2,258,130,386,66,322,194,450,18,274,82,338,466,114,
  370,242,498,346,218,474,58,314,186,442,122,378,250,506,14,270,
  142,398,78,334,206,462,46,302,430,30,158,414,94,350,9,265,
]

ZERO_CAP = 256
ROUNDS = 20
BEAM = 12
OLD_BOUND = 93


def zero_tail(d: int, r: int):
    """Exact D/S-only all-zero continuation from a nonterminal cell."""
    for e in range(ZERO_CAP + 1):
        z = v25.classify_cell(d + e, r, with_merge=False)
        if z["terminal"]:
            return {
                "closed": True,
                "wait": e,
                "exit": z["exit"],
            }
    return {"closed": False, "wait": ZERO_CAP + 1, "exit": None}


def cmp_band(x: int, y: int):
    """Small exact relational fingerprint; no floating arithmetic."""
    return {
        "le1": x <= y,
        "le2": x <= 2*y,
        "le3": x <= 3*y,
        "le4": x <= 4*y,
        "le6": x <= 6*y,
        "le8": x <= 8*y,
    }


def signature(d: int, r: int, ztail=None):
    N = v25.N0 + v25.NC*r
    S = v25.NC * (1 << d)
    pref = v25.fixed_prefix(N, S)
    j, A, C, q = pref[-1]
    assert j == 59 + d
    m = v25.is_pow3(C)
    assert m is not None
    out = {
        "d": d,
        "r": r,
        "q": q,
        "pow3_exponent": m,
        "A_mod_8": A % 8,
        "A_mod_24": A % 24,
        "A_mod_81": A % 81,
        "endpoint_vs_source": cmp_band(A, N),
        "slope_vs_source": cmp_band(C, S),
        "endpoint_bit_length_gap": A.bit_length() - N.bit_length(),
        "slope_bit_length_gap": C.bit_length() - S.bit_length(),
    }
    if ztail is not None:
        out["zero_tail_wait"] = ztail["wait"]
        out["zero_tail_exit_kind"] = None if ztail["exit"] is None else ztail["exit"]["kind"]
    return out


def main():
    # Reproduce the exact V25 seed boundary before extending it.
    seed_rows = []
    for r in SEED_R:
        full = v25.classify_cell(SEED_DEPTH, r, with_merge=True)
        assert not full["terminal"], (r, full)
        z = zero_tail(SEED_DEPTH, r)
        assert z["closed"], (r, z)
        seed_rows.append((r, z))
    seed_max = max(z["wait"] for _, z in seed_rows)
    assert seed_max == OLD_BOUND, seed_max

    ranked_seed = sorted(seed_rows, key=lambda x: (-x[1]["wait"], x[0]))
    beam = [(SEED_DEPTH, r, z) for r, z in ranked_seed[:BEAM]]

    rounds = [{
        "round": 0,
        "depth": SEED_DEPTH,
        "verified_nonterminal": len(SEED_R),
        "beam_size": len(beam),
        "max_zero_tail_wait": seed_max,
        "hardest": [
            {"r": r, "wait": z["wait"], "exit": z["exit"]["kind"]}
            for r, z in ranked_seed[:BEAM]
        ],
    }]

    first_over_93 = None
    max_seen = seed_max
    full_merge_pruned = 0
    ds_terminal_pruned = Counter()
    zero_censored = 0

    # Stateful residual search: only descendants of the retained hard states.
    for it in range(1, ROUNDS + 1):
        candidates = {}
        for d, r, _parent_zero in beam:
            assert d == SEED_DEPTH + it - 1
            for bit, rr in ((0, r), (1, r + (1 << d))):
                key = (d + 1, rr)
                if key in candidates:
                    continue
                ds = v25.classify_cell(d + 1, rr, with_merge=False)
                if ds["terminal"]:
                    ds_terminal_pruned[ds["exit"]["kind"]] += 1
                    continue
                z = zero_tail(d + 1, rr)
                if not z["closed"]:
                    zero_censored += 1
                candidates[key] = {"bit": bit, "zero": z}

        order = sorted(
            candidates.items(),
            key=lambda kv: (
                -kv[1]["zero"]["wait"],
                kv[0][1],
            ),
        )

        next_beam = []
        verified = []
        for (d, r), info in order:
            full = v25.classify_cell(d, r, with_merge=True)
            if full["terminal"]:
                full_merge_pruned += 1
                continue
            z = info["zero"]
            verified.append((d, r, z, info["bit"]))
            if z["wait"] > max_seen:
                max_seen = z["wait"]
            if first_over_93 is None and z["wait"] > OLD_BOUND:
                first_over_93 = {
                    "round": it,
                    "depth": d,
                    "r": r,
                    "incoming_bit": info["bit"],
                    "zero_tail": z,
                    "signature": signature(d, r, z),
                }
            if len(next_beam) < BEAM:
                next_beam.append((d, r, z))
            # Once the beam is full, continue only through a small audit margin
            # so an early M-prune cannot bias the selected hard set.
            if len(next_beam) >= BEAM and len(verified) >= BEAM + 8:
                break

        if not next_beam:
            rounds.append({
                "round": it,
                "depth": SEED_DEPTH + it,
                "candidate_nonterminal_before_M": len(candidates),
                "verified_nonterminal_checked": len(verified),
                "beam_size": 0,
                "max_zero_tail_wait": None,
            })
            beam = []
            break

        next_beam.sort(key=lambda x: (-x[2]["wait"], x[1]))
        beam = next_beam
        rounds.append({
            "round": it,
            "depth": beam[0][0],
            "candidate_nonterminal_before_M": len(candidates),
            "verified_nonterminal_checked": len(verified),
            "beam_size": len(beam),
            "max_zero_tail_wait": max(x[2]["wait"] for x in beam),
            "hardest": [
                {
                    "r": r,
                    "wait": z["wait"],
                    "exit": None if z["exit"] is None else z["exit"]["kind"],
                    "signature": signature(d, r, z),
                }
                for d, r, z in beam[:4]
            ],
        })

    result = {
        "schema": "COLLATZ_CRYSTAL_ZERO_TAIL_ADVERSARY_V26",
        "parent": {
            "authority": PARENT,
            "run": PARENT_RUN,
            "artifact": PARENT_ARTIFACT,
        },
        "boundary": {
            "seed_depth": SEED_DEPTH,
            "seed_survivors": len(SEED_R),
            "zero_cap": ZERO_CAP,
            "rounds": ROUNDS,
            "beam": BEAM,
        },
        "seed_reproduction": {
            "max_zero_tail_wait": seed_max,
            "expected": OLD_BOUND,
        },
        "rounds": rounds,
        "max_zero_tail_wait_seen": max_seen,
        "first_over_v25_bound": first_over_93,
        "pruning": {
            "direct_or_splice_terminal": dict(ds_terminal_pruned),
            "full_merge_terminal_after_DS_survival": full_merge_pruned,
            "zero_tail_censored_at_cap": zero_censored,
        },
        "scientific_verdict": (
            "V25_93_BIT_ZERO_TAIL_BOUND_REJECTED"
            if first_over_93 is not None else
            "NO_COUNTEREXAMPLE_TO_93_BIT_BOUND_ON_ADVERSARIAL_BOUNDARY"
        ),
        "next_residual": (
            "derive exact separator responsible for the first >93 wait and refine the protected state"
            if first_over_93 is not None else
            "test right-congruence of the repeated hard-state signature and compile a zero-transition rank"
        ),
        "universal_status": "UNKNOWN",
        "global_collatz": "UNKNOWN",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
