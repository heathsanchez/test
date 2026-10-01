#!/usr/bin/env python3
"""V71: close the literal zero-tail continuation of r=30 with existing capability.

The corrected V70 recursive controller leaves the all-zero child r=30 as a
survivor at depth 38. This experiment changes no representation and adds no
merger constructor. It asks only when the already-compiled D/M1/S + q7 bank
first distinguishes that exact zero continuation.
"""
from __future__ import annotations

import hashlib
import json

import collatz_r30_separator_v68 as v68

R = 30
START = 38
STOP = 42


def classify(h: int):
    c = v68.simple_certificate(R, h)
    qhits = v68.q7_mergers(R, h)
    return c, qhits


def main():
    rows = []
    for h in range(START, STOP + 1):
        c, qhits = classify(h)
        rows.append(
            {
                "depth": h,
                "simple_kind": None if c is None else c["kind"],
                "simple_k": None if c is None else c["k"],
                "simple_q": None if c is None else c["q"],
                "simple_p": None if c is None else c["p"],
                "q7_hits": len(qhits),
                "q7_first": None if not qhits else qhits[0],
            }
        )

    for row in rows[:-1]:
        assert row["simple_kind"] is None
        assert row["q7_hits"] == 0

    c, qhits = classify(STOP)
    assert c is not None
    assert c["kind"] == "S"
    assert c["r"] == R
    assert c["h"] == 42
    assert c["n"] == 113503680976663326228507
    assert c["k"] == 101
    assert c["y"] == 153723649420054465951604
    assert c["q"] == 64
    assert c["p"] == 102482432946702977301069
    assert c["source_slope"] == 16634111176194826206439739460943872

    assert len(qhits) == 1
    q = qhits[0]
    assert q["prefix_steps"] == 101
    assert q["word"] == "O"
    assert q["lower0"] == 102482432946702977301069

    result = {
        "schema": "COLLATZ_R30_ZERO_TAIL_CLOSURE_V71",
        "parent_v70_run": 36927944566,
        "parent_v70_head": "705f07591145cb9992d356fdcd3786c33aec9c52",
        "protected_present": ["original_source", "current_endpoint"],
        "tested_depths": rows,
        "first_zero_tail_merger_depth": 42,
        "silent_depths": [38, 39, 40, 41],
        "merger_kind": "S_AND_Q7_OVERLAP",
        "source": c["n"],
        "source_slope": c["source_slope"],
        "orbit_steps": c["k"],
        "endpoint": c["y"],
        "odd_count": c["q"],
        "lower_source": c["p"],
        "new_merger_constructors": 0,
        "new_state_coordinates": 0,
        "interpretation": (
            "The canonical all-zero continuation of r=30 is not an infinite "
            "survivor. Existing compiled merger capability is silent through "
            "depth 41 and first closes the zero tail at depth 42."
        ),
        "next_residual": (
            "Do not deepen r=30 further. Reclose the residual frontier with this "
            "compiled depth-42 merger, then take the first surviving natural-compatible "
            "prefix and ask for its exact zero-tail obstruction. A universal claim still "
            "requires excluding every eventually-zero survivor, not only r=30."
        ),
        "status": "CANDIDATE_PENDING_KERNEL",
        "global_collatz": "UNKNOWN",
        "qed": False,
    }
    result["certificate_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
