"""V66: compile V65 reverse-word discoveries and reclose the full V61 residual.

This is the "never pay twice" step.  V65 spent expensive reverse-search states on
128 calibration cells and discovered exact uniform earlier-source collision
words.  V66 freezes those words before seeing the remaining V61 cells, then
tests only their exact affine applicability on the 14,806 held-out cells.

No new semantic coordinate is introduced.  Every positive hit is an exact
candidate for EarlierSourceCollision(source,current).
"""
import argparse
import hashlib
import json
from collections import Counter

import collatz_crystal_parameter_quotient_v25 as bank
from collatz_consequential_splice_reuse_v57 import orbit

DEPTH = 18
CALIBRATION = 128
STATE_SHA = "a4dcc7bd5d51e6eb5f375140fd29ed722c9337bb11fde9c14ce6e6e9d51353b6"
PILOT_SHA = "7bc9b4e396cfd05130957dfec3a75b43769799a0642471f8291857d1405bd1d8"


def checked_json(path, expected):
    d = json.load(open(path))
    claimed = d.pop("certificate_sha256")
    actual = hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()
    assert claimed == actual == expected
    d["certificate_sha256"] = claimed
    return d


def apply_word(a, c, word):
    """Apply one frozen exact reverse word to the affine endpoint a+c*u."""
    for ch in word:
        if ch == "E":
            a *= 2
            c *= 2
        elif ch == "O":
            # Uniform odd predecessor exists exactly when every endpoint is 2 mod 3.
            if a % 3 != 2 or c % 3:
                return None
            a = (2 * a - 1) // 3
            c = (2 * c) // 3
            assert a % 2 == 1 and c % 2 == 0
        else:
            raise AssertionError(ch)
    return a, c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--pilot", required=True)
    args = ap.parse_args()

    state = checked_json(args.state, STATE_SHA)
    pilot = checked_json(args.pilot, PILOT_SHA)

    live = state["joined_reclosure"]["residual_residues"]
    assert len(live) == 14934
    calibration = set(live[:CALIBRATION])
    heldout = set(live[CALIBRATION:])

    # Freeze before held-out evaluation; cheapest exact representative first.
    discovered = [x["reverse_word"] for x in pilot["witnesses"]]
    assert len(discovered) == pilot["closures"] == 15
    words = sorted(set(discovered), key=lambda w: (len(w), w))
    assert len(words) == 15

    S = bank.NC * (1 << DEPTH)
    hits = {}
    usage = Counter()
    word_tests = 0
    replayed = []

    for r in live:
        N = bank.N0 + bank.NC * r
        pref = bank.fixed_prefix(N, S)
        j, A, C, q = pref[-1]
        assert j == 59 + DEPTH

        for word in words:
            word_tests += 1
            z = apply_word(A, C, word)
            if z is None:
                continue
            p0, ps = z
            if p0 <= 0:
                continue
            if not ((p0 < N and ps <= S) or (p0 <= N and ps < S)):
                continue

            # Exact affine inequalities imply 0 < p(u) < source(u) for every u.
            hits[r] = {
                "word": word,
                "word_len": len(word),
                "prefix_depth": j,
                "endpoint0": str(A),
                "endpoint_slope": str(C),
                "lower0": str(p0),
                "lower_slope": str(ps),
            }
            usage[word] += 1

            # Replay a bounded, predeclared audit sample; applicability itself is
            # symbolic/exact and not inferred from these samples.
            if len(replayed) < 96 and r in heldout:
                rr = []
                for u in (0, 1, 17):
                    source = N + S * u
                    endpoint = orbit(source, j)[0]
                    lower = p0 + ps * u
                    assert endpoint == A + C * u
                    assert 0 < lower < source
                    assert orbit(lower, len(word))[0] == endpoint
                    rr.append([u, str(source), str(lower), str(endpoint)])
                replayed.append({"r": r, "replays": rr})
            break

    pilot_residues = set(pilot["closure_residues"])
    assert pilot_residues <= set(hits)

    cal_hits = sorted(calibration & set(hits))
    hold_hits = sorted(heldout & set(hits))
    residual = [r for r in live if r not in hits]

    result = {
        "schema": "COLLATZ_COMPILED_COLLISION_RECLOSURE_V66",
        "parent_state_sha256": STATE_SHA,
        "discovery_pilot_sha256": PILOT_SHA,
        "frozen_capability_count": len(words),
        "frozen_words": words,
        "selection_rule": "shortest reverse word, then lexicographic",
        "input_residual_cells": len(live),
        "calibration_cells": CALIBRATION,
        "heldout_cells": len(heldout),
        "calibration_closures": len(cal_hits),
        "heldout_closures": len(hold_hits),
        "total_closures": len(hits),
        "remaining_cells": len(residual),
        "heldout_closure_residues": hold_hits,
        "remaining_residues": residual,
        "word_usage": dict(sorted(usage.items(), key=lambda kv: (len(kv[0]), kv[0]))),
        "word_tests": word_tests,
        "discovery_reverse_states": pilot["reverse_states"],
        "prospective_replays": replayed,
        "protected_present": ["original_source", "current_endpoint"],
        "status": (
            "PROSPECTIVE_EXACT_COLLISION_REUSE" if hold_hits
            else "BOUNDED_NO_TRANSFER"
        ),
        "promotion_boundary": (
            "Exact Python affine applicability and orbit replays.  Held-out hits "
            "must be compiled through the existing Lean EarlierSourceCollision/"
            "ExitCertificate interface before WARRANTED promotion.  Surviving "
            "cells remain UNKNOWN."
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
