#!/usr/bin/env python3
"""V55: minimum 3-adic separator for the V54R owner-phase collision.

This is a bounded diagnostic.  It constructs the exact V54R frontier through
depth 9, expands exactly one forced parameter bit, and compares protected
child consequences.  Every unresolved depth-10 child is retained as a live
unknown state (a boundary self-loop), so truncation cannot empty the kernel.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json

import collatz_crystal_owner_cylinder_reclosure_v54 as v54
import collatz_crystal_parameter_quotient_v25 as v25


PARENT_DEPTH = 9
BLOCK_CAP = 128


def phase(f: v54.Family):
    return f.blocks, f.current_slope


def reclose(f: v54.Family):
    old = v25.classify_cell(f.d, f.r, with_merge=True)
    if old["terminal"]:
        return "EXIT", None
    status, end, _ = v54.advance_until_seam(f, BLOCK_CAP)
    if status in ("OWNER_LOWER", "OWNER_3Q"):
        return "EXIT", None
    if status == "BLOCK_CAP":
        return "UNKNOWN_CAP", end
    assert status == "SPLIT"
    return "LIVE", end


def build_parent_frontier():
    frontier = [v54.Family(0, 0, v25.N0, v25.NC, v25.N0, v25.NC, 0)]
    for depth in range(PARENT_DEPTH + 1):
        live = []
        for f in frontier:
            status, end = reclose(f)
            if status == "LIVE":
                live.append(end)
            elif status == "UNKNOWN_CAP":
                raise AssertionError((depth, f.r, "block cap"))
        if depth == PARENT_DEPTH:
            return live
        frontier = [v54.split(f, bit) for f in live for bit in (0, 1)]
    raise AssertionError("unreachable")


def child_consequence(f: v54.Family, bit: int):
    child = v54.split(f, bit)
    status, end = reclose(child)
    if status == "EXIT":
        return ("EXIT",)
    assert end is not None
    # Unknown boundary nodes remain live.  Their canonical owner phase is the
    # observable successor; the implicit self-loop prevents false closure.
    return ("LIVE",) + phase(end)


def collision_rows(rows, trits: int):
    modulus = 3**trits
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["parent_phase"], row["r"] % modulus)].append(row)
    collisions = []
    for key, group in grouped.items():
        futures = {tuple(map(tuple, row["children"])) for row in group}
        if len(futures) > 1:
            collisions.append({
                "key": [list(key[0]), key[1]],
                "rows": [{"r": row["r"], "children": row["children"]}
                         for row in group],
            })
    return len(grouped), collisions


def main():
    parents = build_parent_frontier()
    rows = []
    for f in parents:
        rows.append({
            "r": f.r,
            "parent_phase": phase(f),
            "children": [child_consequence(f, 0), child_consequence(f, 1)],
        })

    parent_groups = Counter(row["parent_phase"] for row in rows)
    future_profiles = defaultdict(set)
    for row in rows:
        future_profiles[row["parent_phase"]].add(tuple(map(tuple, row["children"])))

    separator_scan = []
    selected = None
    for trits in range(0, 8):
        classes, collisions = collision_rows(rows, trits)
        separator_scan.append({
            "trits": trits, "modulus": 3**trits,
            "classes": classes, "collision_count": len(collisions),
            "first_collision": collisions[0] if collisions else None,
        })
        if not collisions and selected is None:
            selected = trits

    assert len(parents) == 64
    assert sorted(parent_groups.values(), reverse=True) == [61, 3]
    assert sorted(map(len, future_profiles.values()), reverse=True) == [8, 1]
    assert selected == 5

    result = {
        "schema": "COLLATZ_CRYSTAL_OWNER_PHASE_SEPARATOR_V55",
        "parent_depth": PARENT_DEPTH,
        "child_depth": PARENT_DEPTH + 1,
        "block_cap": BLOCK_CAP,
        "parent_cells": len(parents),
        "parent_phase_groups": [
            {"phase": [blocks, str(slope)], "count": count,
             "future_profiles": len(future_profiles[(blocks, slope)])}
            for (blocks, slope), count in sorted(
                parent_groups.items(), key=lambda item: (-item[1], item[0]))
        ],
        "separator_scan": separator_scan,
        "selected_separator": {
            "coordinate": "source_parameter_r_mod_3^k",
            "minimum_k_on_frozen_boundary": selected,
            "modulus": 3**selected,
        },
        "unknown_boundary_policy": "SELF_LOOP_EACH_LIVE_DEPTH10_PHASE",
        "future_kernel_empty": False,
        "verdict": "BOUNDED_3ADIC_SEPARATOR_WITH_LIVE_KERNEL",
        "promotion_boundary": (
            "r mod 243 separates the frozen depth-9 successor collision only. "
            "It is not an all-depth quotient and the live boundary kernel is retained."
        ),
        "universal_status": "UNKNOWN",
        "global_collatz": "UNKNOWN",
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["certificate_sha256"] = hashlib.sha256(payload).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
