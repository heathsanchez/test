#!/usr/bin/env python3
"""ACC GS-Sub V28: root-hit sharding for the verified strict 432 residual.

Verified residual motivating this phase:
- ac-03665 still has a strict live record of 435 atomic moves;
- the 416-step weighted baseline and exact carried-state selector are stable;
- V27 rank 5 found five strict first recursive-surgery hits below 435,
  with optimistic exact lower bounds 432, 433, 434, 434, 434;
- four of those five child branches ended by time cap after V20 split the
  remaining compiler budget among several root hits.

V28 changes allocation only.  It keeps the official move language, weighted
baseline, carried-state search, local exact-surgery generator, recursive child
compiler, and pinned verifier unchanged.  A workflow shard chooses one strict
root hit and gives that child the full remaining compile deadline instead of
sharing the root budget with its siblings.
"""

from __future__ import annotations

import json
import math
import os
import time

import solver_v20_gssub_recursive_suffix_surgery as v20
import solver_v26_gssub_rank_sharded_424 as v26


def root_hit_sharded_compile(
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
    seconds,
    label,
):
    rounds = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_ROUNDS", "2")))
    deadline = time.time() + max(1.0, float(seconds))
    remaining = deadline - time.time()
    if remaining < 1.0:
        return None, {
            "code": "time_cap",
            "label": label,
            "recursive_surgery": True,
            "recursive_surgery_code": "time_cap",
            "root_hit_sharded": True,
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
        label=f"{label}-direct-r0",
    )
    if direct is not None:
        meta = dict(direct_meta)
        meta.update(
            {
                "recursive_surgery": False,
                "recursive_surgery_code": "ok",
                "recursive_surgery_rounds_used": 0,
                "root_hit_sharded": True,
            }
        )
        return direct, meta

    if len(suffix_path) <= 1:
        meta = dict(direct_meta)
        meta.update(
            {
                "recursive_surgery": True,
                "recursive_surgery_code": "no_suffix",
                "recursive_surgery_rounds_used": 0,
                "root_hit_sharded": True,
            }
        )
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
    requested = max(1, int(os.environ.get("ACC_SUFFIX_SURGERY_ROOT_HIT_RANK", "1")))

    if requested > len(competitive):
        meta = dict(direct_meta)
        meta.update(
            {
                "recursive_surgery": True,
                "recursive_surgery_code": "root_hit_rank_out_of_range",
                "recursive_surgery_rounds_used": 0,
                "recursive_surgery_search": search_meta,
                "recursive_surgery_best_lb": (
                    competitive[0]["lower_bound"] if competitive else math.inf
                ),
                "root_hit_sharded": True,
                "requested_root_hit_rank": requested,
                "competitive_root_hits": len(competitive),
            }
        )
        print(
            "ROOT_HIT_SHARD",
            json.dumps(
                {
                    "requested": requested,
                    "competitive_root_hits": len(competitive),
                    "selected": None,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return None, meta

    hit = competitive[requested - 1]
    k = int(hit["rejoin_index"])
    print(
        "ROOT_HIT_SHARD",
        json.dumps(
            {
                "requested": requested,
                "competitive_root_hits": len(competitive),
                "selected": {
                    "lower_bound": hit["lower_bound"],
                    "cost": hit["cost"],
                    "depth": hit["depth"],
                    "rejoin_index": k,
                    "total": hit["total"],
                },
            },
            sort_keys=True,
        ),
        flush=True,
    )

    remaining = deadline - time.time()
    if remaining < 2.0 or k <= 0 or k >= len(suffix_path):
        meta = dict(direct_meta)
        meta.update(
            {
                "recursive_surgery": True,
                "recursive_surgery_code": "time_cap" if remaining < 2.0 else "bad_rejoin",
                "recursive_surgery_rounds_used": 0,
                "recursive_surgery_search": search_meta,
                "root_hit_sharded": True,
                "requested_root_hit_rank": requested,
                "competitive_root_hits": len(competitive),
                "root_hit_lower_bound": hit["lower_bound"],
                "root_hit_rejoin_index": k,
            }
        )
        return None, meta

    cand, child_meta = v20._recursive_compile(
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
        deadline=deadline,
        label=f"{label}-root-h{requested}-k{k}",
        rounds_left=max(0, rounds - 1),
        round_index=1,
    )
    meta = dict(child_meta)
    meta.update(
        {
            "root_hit_sharded": True,
            "requested_root_hit_rank": requested,
            "competitive_root_hits": len(competitive),
            "root_hit_lower_bound": hit["lower_bound"],
            "root_hit_cost": hit["cost"],
            "root_hit_depth": hit["depth"],
            "root_hit_rejoin_index": k,
            "recursive_surgery_parent_search": search_meta,
            "direct_failure": direct_meta,
        }
    )
    if cand is not None:
        meta["recursive_surgery_code"] = "ok"
    return cand, meta


v20.v13.compile_seeded_suffix = root_hit_sharded_compile


if __name__ == "__main__":
    v26.v25.v23.v22.v20.v13.main()
