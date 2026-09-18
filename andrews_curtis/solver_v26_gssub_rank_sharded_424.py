#!/usr/bin/env python3
"""ACC GS-Sub V26: rank-sharded exploitation of the verified 424 residual.

Verified residual motivating this phase:
- ac-03665 still has a live strict record of 435 atomic moves;
- V25 found three successful 416-step weighted quotient baselines at depth
  weights 0.011, 0.0115, and 0.012;
- the unchanged optimistic bridge search then reached an exact physical
  compatibility lower bound of 424, giving 11 moves of strict slack;
- the monolithic V25 job was cancelled by the workflow wall-clock limit before
  it could finish compiling its 12 finalists, and emitted no candidate.

V26 changes allocation only.  It keeps the V25 weighted proposal, V23 bridge
selector, V20 recursive exact suffix surgery, official move language, and pinned
verifier unchanged.  A workflow shard chooses one weighted corridor and one
finalist rank so each promising residual receives its own compiler budget rather
than competing serially inside one job.
"""

from __future__ import annotations

import json
import os

import solver_v25_gssub_weight_sweep_baseline as v25


_base_exact_prefix_search = v25.v23.v22.v20.v13.exact_prefix_search


def rank_sharded_exact_prefix_search(*args, **kwargs):
    finals, meta = _base_exact_prefix_search(*args, **kwargs)
    rank = max(1, int(os.environ.get("ACC_PREFIX_RANK", "1")))
    if not finals:
        return finals, meta

    summaries = []
    for i, f in enumerate(finals, 1):
        pm = f.get("compatibility_probe") or {}
        summaries.append(
            {
                "rank": i,
                "cost": f.get("cost"),
                "total": f.get("total"),
                "excess": f.get("excess"),
                "optimistic_baseline_cost": f.get("optimistic_baseline_cost"),
                "selection_lower_bound": f.get("selection_lower_bound", pm.get("selection_lower_bound")),
                "physical_compatibility_lb": f.get("physical_compatibility_lb", pm.get("physical_lower_bound")),
                "rejoin_index": f.get("rejoin_index"),
            }
        )

    out_meta = dict(meta)
    out_meta["rank_sharded"] = True
    out_meta["available_finalists"] = len(finals)
    out_meta["requested_rank"] = rank
    out_meta["finalist_summaries"] = summaries

    if rank > len(finals):
        out_meta["rank_shard_code"] = "rank_out_of_range"
        print("RANK_SHARD", json.dumps(out_meta, sort_keys=True), flush=True)
        return [], out_meta

    selected = finals[rank - 1]
    out_meta["rank_shard_code"] = "ok"
    out_meta["selected_rank"] = rank
    out_meta["selected_summary"] = summaries[rank - 1]
    print(
        "RANK_SHARD",
        json.dumps(
            {
                "requested_rank": rank,
                "available_finalists": len(finals),
                "selected": summaries[rank - 1],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return [selected], out_meta


v25.v23.v22.v20.v13.exact_prefix_search = rank_sharded_exact_prefix_search


if __name__ == "__main__":
    v25.v23.v22.v20.v13.main()
