#!/usr/bin/env python3
"""ACC GS-Sub V29: allocate recursive child time by actual competitive hits.

Verified residual motivating this phase:
- ac-03665 remains 435 while the stable weighted quotient baseline is 416;
- V28 root-hit sharding gave the strict 432 root hit the full parent budget;
- inside that root, the next local search found exactly one strict child hit at
  optimistic lower bound 434;
- V20 still divided the remaining child budget by three because its slot count
  used HIT_CAP rather than the number of competitive hits actually present;
- that unique 434 child then ended by time cap.

V29 changes only this verified allocation bug.  Search language, weighted
baseline, carried-state selector, local exact-surgery generator, recursive
rounds, official move replay, pinned verifier, live-record gate and publication
policy are unchanged.  A recursive level now divides time among the competitive
hits that really exist, not among unused hit-cap slots.
"""

from __future__ import annotations

import math
import os
import time

import solver_v20_gssub_recursive_suffix_surgery as v20
import solver_v28_gssub_root_hit_shard as v28


def competitive_slot_recursive_compile(
    core,
    ns,
    seed_state,
    seed_path,
    seed_cost,
    suffix_path,
    reverse_paths,
    total_cap,
    *,
    ceiling_exclusive,
    beam_width,
    deadline,
    label,
    rounds_left,
    round_index,
):
    remaining = deadline - time.time()
    if remaining < 1.0:
        return None, {
            "code": "time_cap",
            "label": label,
            "recursive_surgery": True,
            "round": round_index,
            "rounds_left": rounds_left,
            "allocation_mode": "actual_competitive_hits",
        }

    direct, direct_meta = v20._original_compile_seeded_suffix(
        core,
        ns,
        seed_state,
        seed_path,
        seed_cost,
        suffix_path,
        reverse_paths,
        total_cap,
        ceiling_exclusive=ceiling_exclusive,
        beam_width=beam_width,
        seconds=remaining,
        label=f"{label}-direct-r{round_index}",
    )
    if direct is not None:
        meta = dict(direct_meta)
        meta.update({
            "recursive_surgery": round_index > 0,
            "recursive_surgery_code": "ok",
            "recursive_surgery_rounds_used": round_index,
            "allocation_mode": "actual_competitive_hits",
        })
        return direct, meta

    if rounds_left <= 0 or len(suffix_path) <= 1:
        meta = dict(direct_meta)
        meta.update({
            "recursive_surgery": round_index > 0,
            "recursive_surgery_code": "round_limit",
            "recursive_surgery_rounds_used": round_index,
            "allocation_mode": "actual_competitive_hits",
        })
        return None, meta

    ranked_hits, search_meta = v20._collect_local_hits(
        core,
        ns,
        seed_state,
        seed_path,
        seed_cost,
        suffix_path,
        total_cap,
        ceiling_exclusive=ceiling_exclusive,
        deadline=deadline,
    )
    competitive = [h for h in ranked_hits if h["lower_bound"] < ceiling_exclusive]
    hit_cap = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_HIT_CAP", "6")))
    selected = competitive[:hit_cap]
    attempts = []

    for rank, hit in enumerate(selected, 1):
        remaining = deadline - time.time()
        if remaining < 2.0:
            break
        k = int(hit["rejoin_index"])
        if k <= 0 or k >= len(suffix_path):
            continue

        # Critical V29 change: allocate only across competitive children that
        # actually exist. V20 used hit_cap-rank+1, so a unique child still got
        # only one third of the remaining budget when HIT_CAP >= 3.
        remaining_competitive = len(selected) - rank + 1
        slots = max(1, min(3, remaining_competitive))
        child_seconds = max(2.0, remaining / slots)
        child_deadline = min(deadline, time.time() + child_seconds)

        cand, cm = competitive_slot_recursive_compile(
            core,
            ns,
            hit["state"],
            hit["path"],
            hit["cost"],
            suffix_path[k:],
            reverse_paths,
            total_cap,
            ceiling_exclusive=ceiling_exclusive,
            beam_width=beam_width,
            deadline=child_deadline,
            label=f"{label}-r{round_index + 1}-h{rank}-k{k}",
            rounds_left=rounds_left - 1,
            round_index=round_index + 1,
        )
        attempts.append({
            "rank": rank,
            "rejoin_index": k,
            "local_depth": hit["depth"],
            "local_cost": hit["cost"],
            "optimistic_final_lb": hit["lower_bound"],
            "slots": slots,
            "selected_competitive_hits": len(selected),
            "child_code": cm.get("code"),
            "child_recursive_code": cm.get("recursive_surgery_code"),
            "child_rounds_used": cm.get("recursive_surgery_rounds_used"),
        })
        if cand is not None:
            meta = dict(cm)
            meta.update({
                "recursive_surgery": True,
                "recursive_surgery_code": "ok",
                "recursive_surgery_rounds_used": int(
                    cm.get("recursive_surgery_rounds_used", round_index + 1)
                ),
                "recursive_surgery_parent_round": round_index,
                "recursive_surgery_rejoin_index": k,
                "recursive_surgery_local_depth": hit["depth"],
                "recursive_surgery_local_cost": hit["cost"],
                "recursive_surgery_optimistic_final_lb": hit["lower_bound"],
                "recursive_surgery_search": search_meta,
                "recursive_surgery_attempts": attempts,
                "direct_failure": direct_meta,
                "allocation_mode": "actual_competitive_hits",
            })
            return cand, meta

    meta = dict(direct_meta)
    meta.update({
        "recursive_surgery": True,
        "recursive_surgery_code": (
            "time_cap" if time.time() >= deadline else "no_recursive_steal"
        ),
        "recursive_surgery_rounds_used": round_index,
        "recursive_surgery_rounds_left": rounds_left,
        "recursive_surgery_search": search_meta,
        "recursive_surgery_attempts": attempts,
        "recursive_surgery_best_lb": (
            selected[0]["lower_bound"] if selected else math.inf
        ),
        "allocation_mode": "actual_competitive_hits",
        "selected_competitive_hits": len(selected),
    })
    return None, meta


# V28's root-hit sharder calls v20._recursive_compile dynamically, so replacing
# only that recursive allocation boundary preserves the entire V28 mechanism.
v20._recursive_compile = competitive_slot_recursive_compile
v20.v13.compile_seeded_suffix = v28.root_hit_sharded_compile


if __name__ == "__main__":
    v28.v26.v25.v23.v22.v20.v13.main()
