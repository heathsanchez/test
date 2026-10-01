"""V65: exact earlier-source collision pilot on the protected Collatz quotient.

The protected state is (original_source,current_endpoint).  This experiment does
not invent a new state coordinate.  It reuses the existing exact reverse
constructor to ask whether a V61 residual affine source cell has a uniform
smaller-source coalescence certificate.

A hit is consequential: for every natural parameter u, the original source
reaches the affine endpoint after the maximal fixed prefix and a strictly
smaller affine source reaches the same endpoint after an exact reverse word.
That is exactly the coalescent constructor of ExitCertificate.

The pilot is intentionally the first 128 V61 residual cells.  A positive result
earns full-bank reclosure; a negative result is only bounded no-hit evidence.
"""
import argparse
import hashlib
import json

import collatz_crystal_parameter_quotient_v25 as bank
from collatz_consequential_splice_reuse_v57 import orbit

PILOT = 128
DEPTH = 18


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    args = ap.parse_args()

    state = json.load(open(args.state))
    claimed = state.pop("certificate_sha256")
    actual = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
    assert claimed == actual == "a4dcc7bd5d51e6eb5f375140fd29ed722c9337bb11fde9c14ce6e6e9d51353b6"

    live = state["joined_reclosure"]["residual_residues"]
    assert len(live) == 14934
    sample = live[:PILOT]

    S = bank.NC * (1 << DEPTH)
    rows = []
    reverse_states = 0
    max_word = 0

    for r in sample:
        N = bank.N0 + bank.NC * r
        prefix = bank.fixed_prefix(N, S)
        j, A, C, q = prefix[-1]
        assert j == 59 + DEPTH

        # The V61 full bank already closed direct descent, M1 and paid splice
        # leaves at this depth.  Recheck the D/S part through the independent
        # V25 constructor before trying a more general coalescence.
        assert bank.direct_or_splice(prefix, N, S) is None

        witness, states = bank.reverse_lower_witness(A, C, N, S)
        reverse_states += states
        if witness is None:
            continue

        p0 = int(witness["p0"])
        ps = int(witness["pSlope"])
        word = witness["word"]
        max_word = max(max_word, len(word))

        assert p0 > 0
        assert (p0 < N and ps <= S) or (p0 <= N and ps < S)

        replays = []
        for u in (0, 1, 17):
            source = N + S * u
            endpoint = orbit(source, j)[0]
            assert endpoint == A + C * u
            lower = p0 + ps * u
            assert 0 < lower < source
            merged = orbit(lower, len(word))[0]
            assert merged == endpoint
            replays.append({
                "u": u,
                "source": str(source),
                "lower_source": str(lower),
                "common_endpoint": str(endpoint),
            })

        rows.append({
            "r": r,
            "source0": str(N),
            "source_slope": str(S),
            "prefix_depth": j,
            "endpoint0": str(A),
            "endpoint_slope": str(C),
            "q": q,
            "lower0": str(p0),
            "lower_slope": str(ps),
            "reverse_word": word,
            "reverse_steps": len(word),
            "odd_inverse": witness["oddInverse"],
            "even_lifts": witness["evenLifts"],
            "replays": replays,
        })

    result = {
        "schema": "COLLATZ_EARLIER_SOURCE_COLLISION_V65_PILOT",
        "parent_state_sha256": claimed,
        "protected_present": ["original_source", "current_endpoint"],
        "constructor": "uniform exact smaller-source coalescence",
        "input_cells": len(sample),
        "closures": len(rows),
        "closure_residues": [x["r"] for x in rows],
        "reverse_states": reverse_states,
        "max_reverse_word": max_word,
        "witnesses": rows[:32],
        "adaptation": (
            "REUSE existing exact coalescent constructor if closures>0; "
            "do not add a representation coordinate.  If closures=0, retain "
            "bounded negative evidence only and inspect the first protected "
            "future separator before expanding grammar."
        ),
        "promotion_boundary": (
            "Pilot only.  A hit is an exact affine-family candidate and must "
            "be reclosed on all 14934 V61 residual cells and kernel-bound "
            "before promotion."
        ),
        "global_collatz": "UNKNOWN",
        "qed": False,
    }
    result["certificate_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True).encode()
    ).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
