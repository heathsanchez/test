#!/usr/bin/env python3
"""ACC GS-Sub V25: local weighted-baseline sweep before changing the compiler.

Verified residual motivating this phase:
- ac-03665 remains at a live strict record of 435 atomic moves;
- the 0.012 weighted proposal gives a 416-step quotient baseline;
- focused recursive physical salvage repeatedly reaches exact optimistic lower
  bounds 432/433 but produces no pinned-verifier-clean candidate;
- increasing the same suffix-surgery depth to 7 exhausted every sub-435 first
  repair hit in the selected rank-5/rank-2 families without a steal.

Before changing the move language or exact compiler, V25 tests whether the
known 416-step quotient corridor is itself locally improvable.  It sweeps a
small deterministic neighborhood of depth weights, chooses the shortest
successful quotient path, and hands only that path to the unchanged V23/V22
exact carried-state + recursive-surgery compiler.  All final authority remains
with the pinned official verifier and the external strict-only publisher.
"""

from __future__ import annotations

import json
import os
import time

import solver_v2_gssub as v2
import solver_v23_gssub_optimistic_bridge_salvage as v23


def _weights():
    spec = os.environ.get(
        "ACC_WEIGHT_SWEEP",
        "0.011,0.0115,0.012,0.0125,0.013,0.0135,0.014",
    )
    out = []
    for tok in spec.split(","):
        tok = tok.strip()
        if not tok:
            continue
        w = float(tok)
        if w not in out:
            out.append(w)
    if not out:
        out = [0.012]
    return out


def swept_complete_suffix(ns, key, *, max_nodes, max_len):
    t0 = time.time()
    best_path = None
    best_weight = None
    best_steps = None
    total_nodes = 0
    rows = []

    for w in _weights():
        s0 = time.time()
        path, nodes, _seen = v2.solve_depth_weighted_gssub(
            ns,
            key[0],
            key[1],
            max_nodes=max_nodes,
            max_len=max_len,
            depth_weight=w,
        )
        total_nodes += int(nodes)
        steps = None if path is None else len(path) - 1
        rows.append(
            {
                "weight": w,
                "steps": steps,
                "nodes": int(nodes),
                "seconds": round(time.time() - s0, 3),
            }
        )
        if path is None:
            continue
        if best_steps is None or steps < best_steps or (
            steps == best_steps and (best_weight is None or abs(w - 0.012) < abs(best_weight - 0.012))
        ):
            best_path = path
            best_weight = w
            best_steps = steps

    elapsed = round(time.time() - t0, 3)
    print(
        "WEIGHT_SWEEP_BASELINE",
        json.dumps(
            {
                "results": rows,
                "selected_weight": best_weight,
                "selected_steps": best_steps,
                "total_nodes": total_nodes,
                "seconds": elapsed,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return best_path, total_nodes, elapsed


# V22 correctly wires V18's captured baseline hook. Replace only that proposal
# hook; V18's suffix cache and every downstream compiler/verifier remain intact.
v23.v22.v20.v18._original_complete_suffix = swept_complete_suffix
v23.v22.v20.v13.complete_suffix = v23.v22.v20.v18._cached_complete_suffix


if __name__ == "__main__":
    v23.v22.v20.v13.main()
