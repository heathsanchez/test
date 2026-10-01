#!/usr/bin/env python3
"""V65: consequential contraction of the V64 bank to its actually proved dyadic domains.

The frozen backward-cover certificates were stored in the source parameterization
N0 + NC*(r + 2^h*u), where NC = 2^59 * 3^8.  The generic Lean theorem
SourceCylinderExit.shortcut_iter_source_lift proves the same exit consequence on
n + 2^k*u.  For every frozen certificate k = 59+h, so the stored 3^8 factor is
not a semantic premise of the exit law.

This audit:
  * independently replays every frozen certificate;
  * contracts each law to the dyadic cylinder already justified by the theorem;
  * rechecks the exact V61 original-source residual;
  * asks whether the u=0 representative of any maximal fixed prefix lies in one
    of the contracted law domains with a valid lower-source witness.

If u=0 is uncovered, no union of conditional parameter rays can close that
whole residual cell.  This is a scoped capability-domain result, not Collatz QED.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

N0 = 38_911_100_780_481_085_467
NC = 3_782_158_995_862_761_504_768
THREE8 = 3 ** 8
BANK_SHA256 = "f6ae7adab39824a50f227546be6d4990ac7045f2ec320a134db2354048e530b9"
STATE_SHA256 = "a4dcc7bd5d51e6eb5f375140fd29ed722c9337bb11fde9c14ce6e6e9d51353b6"

def shortcut(n: int) -> int:
    return (3 * n + 1) // 2 if n & 1 else n // 2

def orbit(n: int, k: int) -> tuple[int, int]:
    q = 0
    for _ in range(k):
        q += n & 1
        n = shortcut(n)
    return n, q

def fixed_prefix(N: int, S: int):
    """Exact affine prefixes N+S*u until the parameter slope first becomes odd."""
    j = 0
    X, R = N, S
    while True:
        yield j, X, R
        if R & 1:
            return
        if X & 1:
            X = (3 * X + 1) // 2
            R = 3 * R // 2
        else:
            X //= 2
            R //= 2
        j += 1

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", required=True)
    ap.add_argument("--state", required=True)
    args = ap.parse_args()

    bank_path = Path(args.bank)
    assert hashlib.sha256(bank_path.read_bytes()).hexdigest() == BANK_SHA256
    certs = json.loads(bank_path.read_text())
    assert len(certs) == 3294

    state = json.loads(Path(args.state).read_text())
    claimed = state.pop("certificate_sha256")
    assert claimed == STATE_SHA256
    assert hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest() == claimed
    live = state["joined_reclosure"]["residual_residues"]
    assert len(live) == 14934

    # NC's ternary factor is historical source-family parameterization, not a
    # premise of the generic source-cylinder lift theorem.
    assert NC == (2 ** 59) * THREE8

    laws = {}
    k_hist = collections.Counter()
    kind_hist = collections.Counter()
    contracted_factor_hist = collections.Counter()

    for c in certs:
        r = int(c["r"])
        h = int(c["h"])
        n = int(c["n"])
        k = int(c["k"])
        y = int(c["y"])
        q = int(c["q"])
        stored_slope = int(c["source_slope"])

        assert n == N0 + NC * r
        assert k == 59 + h
        dyadic_modulus = 2 ** k
        assert stored_slope == NC * (2 ** h)
        assert stored_slope == dyadic_modulus * THREE8

        yy, qq = orbit(n, k)
        assert (yy, qq) == (y, q)

        if c["kind"] == "D":
            lower = y
            lower_slope = 3 ** q
            assert 0 < y < n
            assert lower_slope <= dyadic_modulus
        else:
            lower = int(c["p"])
            assert q > 0
            lower_slope = 2 * (3 ** (q - 1))
            assert 0 < lower < n
            assert lower & 1
            assert shortcut(lower) == y
            assert lower_slope <= dyadic_modulus

        # The contracted law is indexed only by the source congruence actually
        # required to preserve the k-step parity word.
        key = (k, n % dyadic_modulus)
        assert key not in laws
        laws[key] = (n, dyadic_modulus, lower, lower_slope, c)
        k_hist[k] += 1
        kind_hist[c["kind"]] += 1
        contracted_factor_hist[stored_slope // dyadic_modulus] += 1

    assert len(laws) == 3294
    assert set(contracted_factor_hist) == {THREE8}
    ks = sorted(k_hist)

    counts = collections.Counter()
    first_near = []
    S = NC * (2 ** 18)

    for r in live:
        N = N0 + NC * r
        hit = False
        for j, X, R in fixed_prefix(N, S):
            counts["prefixes"] += 1

            # Test the u=0 representative against every law precision.  A match
            # is exact membership in a contracted dyadic source cylinder.
            for k in ks:
                modulus = 2 ** k
                law = laws.get((k, X % modulus))
                if law is None:
                    continue
                counts["dyadic_residue_matches"] += 1
                base, _, lower, lower_slope, c = law
                if X < base:
                    counts["residue_matches_below_base"] += 1
                    continue
                v = (X - base) // modulus
                witness = lower + lower_slope * v
                counts["dyadic_cylinder_memberships"] += 1
                if witness >= N:
                    counts["memberships_without_original_source_exit"] += 1
                    if len(first_near) < 8:
                        first_near.append({
                            "r": r, "prefix": j, "law_r": c["r"], "law_h": c["h"],
                            "kind": c["kind"], "law_k": k,
                            "current": str(X), "witness": str(witness),
                            "original_source": str(N),
                        })
                    continue
                counts["protected_u0_hits"] += 1
                hit = True
                if len(first_near) < 8:
                    first_near.append({
                        "r": r, "prefix": j, "law_r": c["r"], "law_h": c["h"],
                        "kind": c["kind"], "law_k": k,
                        "current": str(X), "witness": str(witness),
                        "original_source": str(N),
                    })

        if hit:
            counts["cells_with_u0_hit"] += 1
        else:
            counts["cells_with_uncovered_zero"] += 1

    # This is the decisive reclosure fact.  Since every whole parameter cell
    # contains u=0, a union of guarded rays from this contracted bank cannot
    # close a cell whose u=0 point is uncovered.
    assert counts["prefixes"] == 1_164_852
    assert counts["dyadic_residue_matches"] == 0
    assert counts["dyadic_cylinder_memberships"] == 0
    assert counts["protected_u0_hits"] == 0
    assert counts["cells_with_u0_hit"] == 0
    assert counts["cells_with_uncovered_zero"] == 14_934

    result = {
        "schema": "COLLATZ_MAX_DYADIC_REQUALIFICATION_V65",
        "parent": "collatz-full-bank-preimage-v64@59ad1397a0339a314e9c0c8158548378fdfab89b",
        "parent_run": 36837597897,
        "protected_query": "eventual OrdinaryExit relative to the original source",
        "bank_laws": len(laws),
        "input_cells": len(live),
        "counts": dict(counts),
        "law_k_histogram": dict(sorted(k_hist.items())),
        "law_kind_histogram": dict(sorted(kind_hist.items())),
        "erased_historical_factor": THREE8,
        "requalification": {
            "stored_domain": "n + (2^k * 3^8) * u",
            "contracted_domain": "n + 2^k * u",
            "basis": "existing kernel-checked SourceCylinderExit lift theorem plus independent exact replay",
        },
        "whole_cell_closures": 0,
        "first_near": first_near,
        "status": "WARRANTED_GUARD_CONTRACTION__REJECTED_AS_RESIDUAL_CLOSURE",
        "residual_type": "CAPABILITY_DOMAIN_MISMATCH_NOT_STATE_REPRESENTATION_SEPARATOR",
        "adaptation": (
            "Do not add a protected-state coordinate. Compile transition/preimage closure "
            "of verified ExitCertificate consequences on (original_source,current), then "
            "reclose this same residual. Expand base consequence grammar only if that "
            "transition closure emits an exact uncovered separator."
        ),
        "qed": False,
        "global_collatz": "UNKNOWN",
        "scope": (
            "Exact V61 14,934-cell residual and the frozen 3,294-law backward-cover bank. "
            "This proves lawful removal of the bank's historical 3^8 parameter factor and "
            "zero whole-cell gain from that contraction; it is not complete ROS saturation."
        ),
    }
    result["certificate_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
