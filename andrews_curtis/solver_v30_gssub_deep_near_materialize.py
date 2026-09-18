#!/usr/bin/env python3
"""ACC GS-Sub V30: materialize the verified 434 near-miss corridor.

V29 removed the child-budget confounder for ac-03665.  With the stable 416
quotient baseline and the rank-5 / root-hit-1 corridor, strict recursive
surgery reaches 432, then a unique competitive child at optimistic lower bound
434, and exhausts that child with the full actual competitive-slot budget.
The next exact frozen-suffix continuation reports a minimum raw lower bound of
438 against live 435.  There is therefore no remaining justification for
spending another phase on the identical strict search scope.

V30 changes only the justified boundary: on the already-exhausted strict call,
re-run the same root-hit-sharded exact compiler with a *small relaxed ceiling*
so it can materialize a verifier-valid near-miss certificate for proof-atlas
and peephole salvage.  It does not widen the move language, quotient proposal,
prefix selector, root-hit selector, or recursive surgery.  The workflow still
replays every emitted candidate with the pinned official verifier and only the
fresh strict publisher may submit a row.
"""

from __future__ import annotations

import os

import solver_v20_gssub_recursive_suffix_surgery as v20
import solver_v28_gssub_root_hit_shard as v28
import solver_v29_gssub_competitive_slot_budget as v29


# Preserve V29's corrected recursive allocation inside V28's root sharder.
v20._recursive_compile = v29.competitive_slot_recursive_compile


def deep_near_materialize_compile(
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
    strict_ceiling = int(os.environ.get("ACC_REJOIN_STRICT_CEILING", str(ceiling_exclusive)))

    # Only replace the deterministic strict scope that V29 has already closed.
    # V13's ordinary near pass (larger ceiling) remains untouched.
    if int(ceiling_exclusive) != strict_ceiling:
        return v28.root_hit_sharded_compile(
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
            seconds=seconds,
            label=label,
        )

    margin = max(1, int(os.environ.get("ACC_DEEP_NEAR_MARGIN", "4")))
    relaxed_ceiling = strict_ceiling + margin
    cand, meta = v28.root_hit_sharded_compile(
        core,
        ns,
        seed_state,
        seed_path,
        seed_cost,
        suffix_path,
        reverse_paths,
        total_cap,
        ceiling_exclusive=relaxed_ceiling,
        beam_width=beam_width,
        seconds=seconds,
        label=f"{label}-deep-near-m{margin}",
    )
    out = dict(meta)
    out.update({
        "deep_near_materialize": True,
        "deep_near_margin": margin,
        "strict_scope_exhausted_by_v29": True,
        "original_strict_ceiling_exclusive": strict_ceiling,
        "materialize_ceiling_exclusive": relaxed_ceiling,
        "materialized_candidate": cand is not None,
        "materialized_candidate_length": len(cand) if cand is not None else None,
    })
    return cand, out


# V13 main remains authoritative for pinned official replay and for separating
# best_any from best_strict.  A materialized non-record can only reach
# candidate_any.txt; the workflow's fortifier + fresh strict publisher decides
# whether a shortened derivative is competitive.
v20.v13.compile_seeded_suffix = deep_near_materialize_compile


if __name__ == "__main__":
    v28.v26.v25.v23.v22.v20.v13.main()
