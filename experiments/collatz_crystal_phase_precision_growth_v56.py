#!/usr/bin/env python3
"""V56: reject fixed 3-adic precision on consecutive exact CEGAR seams."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json

import collatz_crystal_owner_cylinder_reclosure_v54 as v54
import collatz_crystal_owner_phase_separator_v55 as v55
import collatz_crystal_parameter_quotient_v25 as v25


def summarize(rows):
    groups = Counter(row["parent_phase"] for row in rows)
    profiles = defaultdict(set)
    for row in rows:
        profiles[row["parent_phase"]].add(tuple(map(tuple, row["children"])))
    scan = []
    selected = None
    for trits in range(8):
        classes, collisions = v55.collision_rows(rows, trits)
        scan.append({
            "trits": trits,
            "modulus": 3**trits,
            "classes": classes,
            "collision_count": len(collisions),
            "first_collision": collisions[0] if collisions else None,
        })
        if not collisions and selected is None:
            selected = trits
    return {
        "parent_cells": len(rows),
        "phase_groups": [
            {"phase": [b, str(s)], "count": n,
             "future_profiles": len(profiles[(b, s)])}
            for (b, s), n in sorted(groups.items(), key=lambda x: (-x[1], x[0]))
        ],
        "separator_scan": scan,
        "minimum_trits": selected,
        "minimum_modulus": None if selected is None else 3**selected,
    }


def main():
    live = [v54.Family(0, 0, v25.N0, v25.NC, v25.N0, v25.NC, 0)]
    root_status, root = v55.reclose(live[0])
    assert root_status == "LIVE"
    live = [root]
    reports = {}

    for depth in range(0, 11):
        rows = []
        next_live = []
        for f in live:
            children = []
            for bit in (0, 1):
                child = v54.split(f, bit)
                status, end = v55.reclose(child)
                if status == "EXIT":
                    children.append(("EXIT",))
                else:
                    assert status == "LIVE" and end is not None
                    children.append(("LIVE",) + v55.phase(end))
                    next_live.append(end)
            rows.append({"r": f.r, "parent_phase": v55.phase(f),
                         "children": children})
        if depth in (9, 10):
            reports[str(depth)] = summarize(rows)
        live = next_live

    d9, d10 = reports["9"], reports["10"]
    assert d9["parent_cells"] == 64
    assert [g["count"] for g in d9["phase_groups"]] == [61, 3]
    assert d9["minimum_trits"] == 5
    assert d10["parent_cells"] == 115
    assert [g["count"] for g in d10["phase_groups"]] == [102, 9, 4]
    assert d10["separator_scan"][5]["collision_count"] == 5
    assert d10["minimum_trits"] == 6

    result = {
        "schema": "COLLATZ_CRYSTAL_PHASE_PRECISION_GROWTH_V56",
        "reports": reports,
        "precision_sequence": [d9["minimum_trits"], d10["minimum_trits"]],
        "fixed_mod_243_status": "REJECTED_BY_DEPTH10_SUCCESSOR_COLLISIONS",
        "unknown_boundary_policy": "SELF_LOOP_EACH_LIVE_DEPTH11_PHASE",
        "future_kernel_empty": False,
        "verdict": "FIXED_3ADIC_PRECISION_REJECTED",
        "next_representation": (
            "Normalize the source-relative 3-adic coordinate under the return map, "
            "or prove a well-founded rule for its precision growth."
        ),
        "promotion_boundary": (
            "Two consecutive bounded seams establish precision growth 5 to 6 only; "
            "they do not prove unbounded growth or Collatz."
        ),
        "universal_status": "UNKNOWN",
        "global_collatz": "UNKNOWN",
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["certificate_sha256"] = hashlib.sha256(payload).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
