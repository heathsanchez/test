#!/usr/bin/env python3
"""Compose exact reverse EXIT certificates on the late 24-bit live-origin adversaries.

This tests the actual residual, not residue-population entropy.  For each source
whose first coefficient crossing occurs at depth >=230 in the independent
2^24 cover, recursively compose first-contracting reverse certificates.  Every
composition is an exact predecessor chain; reaching p<n is therefore an
OrdinaryExit/lower-merge witness.

Q14 is the qualified bank.  Q18 is an explicitly bounded stronger diagnostic
using the same exact certificate generator.  Non-emptiness is a negative
result, never a global Collatz claim.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from collatz_reverse_predecessor_tree import T, Cert, enumerate_first_contractions

NODE_CAP = 200_000


def thresholds(J: int) -> list[int]:
    out = [0] * (J + 1)
    q = 0
    p3 = 1
    for j in range(1, J + 1):
        while p3 < (1 << j):
            p3 *= 3
            q += 1
        out[j] = q
    return out


def build_bank(Q: int):
    certs = enumerate_first_contractions(Q)
    idx: dict[tuple[int, int], list[Cert]] = defaultdict(list)
    p3 = [1]
    for _ in range(Q):
        p3.append(p3[-1] * 3)
    for c in certs:
        idx[(c.odd_inverse_steps, c.residue)].append(c)

    @lru_cache(maxsize=None)
    def neighbors(x: int):
        by_p: dict[int, Cert] = {}
        for r in range(1, Q + 1):
            for c in idx.get((r, x % p3[r]), ()):
                num = c.a * x - c.c
                assert num % c.d == 0
                p = num // c.d
                if 0 < p < x:
                    by_p.setdefault(p, c)
        return tuple(sorted(by_p.items()))

    def find_below(y: int, source: int):
        stack = [y]
        seen = {y}
        expanded = 0
        while stack:
            x = stack.pop()
            expanded += 1
            if expanded > NODE_CAP:
                return {"status": "NODE_CAP", "expanded": expanded, "seen": len(seen)}
            for p, c in neighbors(x):
                if p < source:
                    # Exact replay of this last edge.
                    z = p
                    for _ in c.word:
                        z = T(z)
                    assert z == x
                    return {
                        "status": "EXIT",
                        "predecessor": p,
                        "entered_endpoint": x,
                        "word": c.word,
                        "odd_inverse_steps": c.odd_inverse_steps,
                        "expanded": expanded,
                        "seen": len(seen),
                    }
                if p not in seen:
                    seen.add(p)
                    stack.append(p)
        return {"status": "NO_EXIT_IN_Q_CLOSURE", "expanded": expanded, "seen": len(seen)}

    return certs, find_below


def earliest_merge(source: int, crossing: int, find_below):
    y = source
    max_expanded = 0
    for k in range(crossing):  # strictly before coefficient crossing
        z = find_below(y, source)
        max_expanded = max(max_expanded, z.get("expanded", 0))
        if z["status"] == "NODE_CAP":
            return {"status": "NODE_CAP", "depth": k, "endpoint": y, **z}
        if z["status"] == "EXIT":
            return {"status": "EXIT", "depth": k, "endpoint": y, **z}
        y = T(y)
    return {
        "status": "SURVIVES_TO_CROSSING",
        "checked_prefix_depths": crossing,
        "max_closure_nodes_expanded": max_expanded,
    }


def boundary_state(source: int, crossing: int, qm: list[int]):
    y = source
    q = 0
    prev = source
    q_prev = 0
    for j in range(1, crossing + 1):
        prev = y
        q_prev = q
        odd = y & 1
        y = T(y)
        q += odd
    assert q < qm[crossing]
    return {
        "pre_cross_depth": crossing - 1,
        "pre_cross_endpoint": prev,
        "pre_cross_odd_count": q_prev,
        "qmin_pre": qm[crossing - 1],
        "qmin_cross": qm[crossing],
        "coefficient_surplus_pre": q_prev - qm[crossing - 1],
        "pre_cross_parity": prev & 1,
        "crossing_endpoint_recomputed": y,
        "direct_descent_at_crossing": y < source,
        "pre_cross_ge_2source": prev >= 2 * source,
        "two_source_minus_pre_cross": 2 * source - prev,
    }


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: collatz_noexit_late_boundary_v0.py late.json")
    obj = json.loads(Path(sys.argv[1]).read_text())
    assert obj["schema"] == "COLLATZ_24BIT_LATE_SOURCE_EXTRACT_V0"
    assert obj["unresolved"] == 0 and obj["overflow"] == 0
    rows = obj["late_sources"]
    assert rows and max(r["first_crossing"] for r in rows) == 287

    qm = thresholds(512)
    q14, find14 = build_bank(14)
    assert len(q14) == 14764

    stage14 = {}
    q18_needed = []
    for r in rows:
        n = r["source"]
        fc = r["first_crossing"]
        a = earliest_merge(n, fc, find14)
        stage14[n] = a
        if a["status"] == "SURVIVES_TO_CROSSING":
            q18_needed.append(r)

    q18, find18 = build_bank(18)
    stage18 = {}
    for r in q18_needed:
        stage18[r["source"]] = earliest_merge(r["source"], r["first_crossing"], find18)

    out_rows = []
    survivors = []
    for r in rows:
        n = r["source"]
        fc = r["first_crossing"]
        b = boundary_state(n, fc, qm)
        assert b["crossing_endpoint_recomputed"] == r["crossing_endpoint"]
        q18res = stage18.get(n, {"status": "NOT_NEEDED_Q14_ALREADY_EXITED"})
        row = {
            **r,
            "q14_recursive_reverse_closure": stage14[n],
            "q18_recursive_reverse_closure": q18res,
            "boundary": b,
        }
        if q18res.get("status") == "SURVIVES_TO_CROSSING":
            survivors.append(n)
        out_rows.append(row)

    result = {
        "schema": "COLLATZ_NOEXIT_LATE_BOUNDARY_V0",
        "source_cover": {
            "source_bits": obj["source_bits"],
            "late_threshold": obj["late_threshold"],
            "max_first_crossing": obj["max_first_crossing"],
            "late_source_count": len(rows),
        },
        "reverse_banks": {
            "q14_first_contraction_certificates": len(q14),
            "q18_first_contraction_certificates": len(q18),
            "composition": "strictly decreasing predecessor closure",
            "node_cap": NODE_CAP,
        },
        "rows": out_rows,
        "q18_survivors_to_first_crossing": survivors,
        "status": (
            "Q18_REVERSE_CLOSURE_DOES_NOT_REMOVE_LONGEST_LATE_BOUNDARY"
            if survivors else
            "FINITE_LATE_BOUNDARY_REMOVED_BY_Q18_REVERSE_CLOSURE"
        ),
        "residual": {
            "name": "ACTUAL_FIXED_SOURCE_BOUNDARY_WAIT",
            "statement": (
                "A finite reverse EXIT bank, even recursively composed, does not "
                "force the longest late singleton to lower-merge before its actual "
                "coefficient crossing. The remaining source exits only because the "
                "forced even boundary crossing has pre-height < 2*n. A global close "
                "must prove that an actual no-Exit fixed-source path cannot postpone "
                "or survive these zero-surplus boundary events indefinitely."
            ),
            "next": (
                "Compile zero-surplus/qmin-jump boundary events as the protected "
                "transition and search for a source/carry invariant that forces "
                "pre-cross endpoint < 2*n or a lower merge."
            ),
        },
        "global_collatz": "UNKNOWN",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
