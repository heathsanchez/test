#!/usr/bin/env python3
"""ACC GS-Sub V21: weighted shallow baseline + V17 exact carried rejoin compiler.

Verified residual motivating this change:
- ac-03665 live strict record: 435 atomic moves.
- ordinary GS-Sub baseline: 438 quotient steps, so strict improvement was
  impossible even under a hypothetical one-atomic-per-quotient compiler.
- depth-weighted GS-Sub at weight 0.010 found a pinned-verifier-clean route in
  418 quotient steps. The quotient lower-bound obstruction is therefore gone,
  while the legacy physical compilation is still 3153 atomics.

This module changes only the baseline search objective. It reuses V17's exact
carried-state bridge generation, compatibility lower bound, candidate-edge
language, live-bound compiler and official verifier unchanged. The intent is to
measure whether the 418-step quotient route has a physically compatible
representative corridor under the strict 435 ceiling.
"""

from __future__ import annotations

import os
import time

import solver_v2_gssub as v2
import solver_v17_gssub_bound_compatible_rejoin as v17


def weighted_complete_suffix(ns, key, *, max_nodes, max_len):
    weight = float(os.environ.get("ACC_WEIGHTED_BASELINE_DEPTH_WEIGHT", "0.010"))
    t0 = time.time()
    path, nodes, _seen = v2.solve_depth_weighted_gssub(
        ns,
        key[0],
        key[1],
        max_nodes=max_nodes,
        max_len=max_len,
        depth_weight=weight,
    )
    return path, int(nodes), round(time.time() - t0, 3)


# V16/V17 call v13.complete_suffix to construct the quotient baseline. Replace
# only that proposal step; all exact physical search/compiler behavior remains
# V17 and is still replayed by the pinned official verifier.
v17.v16.v13.complete_suffix = weighted_complete_suffix

if __name__ == "__main__":
    v17.v16.v13.main()
