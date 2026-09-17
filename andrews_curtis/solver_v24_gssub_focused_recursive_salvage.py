#!/usr/bin/env python3
"""ACC GS-Sub V24: focus recursive suffix surgery on the verified 434 residual.

V23 changed bridge selection and exposed the first *strictly competitive* physical
continuation lower bound for ac-03665: finalist rank 5 reaches an exact local
rejoin with optimistic final lower bound 434 against the live record 435.
The candidate still dies after that rejoin because the next recursive repair
finds no competitive continuation within the tested depth/beam.

V24 does not change the move language, baseline, compiler, verifier, or scoring.
It only concentrates the existing recursive exact-surgery budget on selected
V23 finalist ranks so deeper local search is spent on the one bridge family that
has already crossed the strict record bound.
"""

from __future__ import annotations

import os

import solver_v23_gssub_optimistic_bridge_salvage as v23


_base_exact_prefix_search = v23.v22.v20.v13.exact_prefix_search


def focused_exact_prefix_search(*args, **kwargs):
    finals, meta = _base_exact_prefix_search(*args, **kwargs)
    spec = os.environ.get("ACC_V24_FINAL_RANKS", "5")
    wanted = []
    for tok in spec.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            r = int(tok)
        except ValueError:
            continue
        if r > 0 and r not in wanted:
            wanted.append(r)

    selected = []
    selected_ranks = []
    for r in wanted:
        if r <= len(finals):
            f = dict(finals[r - 1])
            f["v24_original_rank"] = r
            selected.append(f)
            selected_ranks.append(r)

    meta = dict(meta)
    meta["v24_focus_mode"] = "verified_strict_lb_residual"
    meta["v24_requested_ranks"] = wanted
    meta["v24_selected_ranks"] = selected_ranks
    meta["v24_pre_focus_finalists"] = len(finals)
    meta["v24_focus_note"] = (
        "V23 rank 5 produced an exact recursive-surgery lower bound 434 < 435; "
        "V24 spends deeper unchanged surgery only on selected verified ranks"
    )
    return selected, meta


v23.v22.v20.v13.exact_prefix_search = focused_exact_prefix_search


if __name__ == "__main__":
    v23.v22.v20.v13.main()
