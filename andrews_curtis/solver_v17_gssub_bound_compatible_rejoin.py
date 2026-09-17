#!/usr/bin/env python3
"""ACC GS-Sub V17: strict-bound compatibility screening for carried rejoins.

V15 produced the strongest competitive residual so far on ac-04501: an exact
carried bridge survived four suffix steps with a raw lower bound equal to the
live record (464), i.e. one atomic move short of a strict steal.  V16 therefore
ranked all carried rejoins by short exact suffix compatibility, but its probe
has no live-record lower-bound pruning and can spend most of a workflow probing
states that are already mathematically incapable of a strict improvement.

V17 changes only that implementation boundary.  It keeps V16 bridge generation,
exact carried states, candidate-edge language, suffix route, compiler, official
verifier, near-miss salvage and publication gate unchanged.  During the V16
compatibility probe it applies the admissible bound

    exact_cost_so_far + remaining_baseline_steps < live_record

at every layer.  Because every future quotient transition costs at least one
official atomic move, this lower bound is monotone and pruning at equality is
safe for a strict-record objective.  Bound-pruned bridges retain their exact
lower bound for ranking, so the unchanged downstream near-miss compiler can
still salvage the best non-strict rows after the mechanism change.
"""

from __future__ import annotations

import math
import os

import solver_v16_gssub_compatible_rejoin as v16
import solver_v2_gssub as v2
import solver_v9_gssub_skeleton_lookahead as v9


def bounded_compatibility_probe(
    core,
    ns,
    bridge,
    baseline_keys,
    total_cap,
    *,
    lookahead,
    beam_width,
):
    """V16 exact probe with an admissible strict-live-record lower bound."""
    j = int(bridge["rejoin_index"])
    baseline_steps = len(baseline_keys) - 1
    max_steps = min(max(0, int(lookahead)), baseline_steps - j)
    ceiling = int(os.environ.get("ACC_REJOIN_STRICT_CEILING", "0") or 0)

    initial_cost = int(bridge["cost"])
    initial_remaining = baseline_steps - j
    initial_lb = initial_cost + initial_remaining
    if ceiling > 0 and initial_lb >= ceiling:
        return {
            "code": "strict_bound",
            "steps": 0,
            "lower_bound": int(initial_lb),
            "best_cost": initial_cost,
            "beam": 0,
            "raw_candidates": 0,
            "bound_prunes": 1,
            "strict_ceiling_exclusive": ceiling,
            "layers": [],
        }

    if max_steps <= 0:
        return {
            "code": "terminal_rejoin",
            "steps": 0,
            "lower_bound": initial_cost,
            "best_cost": initial_cost,
            "beam": 1,
            "raw_candidates": 0,
            "bound_prunes": 0,
            "strict_ceiling_exclusive": ceiling or None,
            "layers": [],
        }

    beam = [(bridge["state"], initial_cost)]
    raw_total = 0
    bound_prunes = 0
    layers = []

    for off in range(1, max_steps + 1):
        desired = baseline_keys[j + off]
        remaining = baseline_steps - (j + off)
        by_exact = {}
        raw = 0
        layer_prunes = 0
        min_rejected_lb = math.inf

        for state, cost in beam:
            for nxt, edge in v9.candidate_edges(core, ns, state, desired, total_cap):
                raw += 1
                raw_total += 1
                nc = cost + len(edge)
                lb = nc + remaining
                if ceiling > 0 and lb >= ceiling:
                    layer_prunes += 1
                    bound_prunes += 1
                    if lb < min_rejected_lb:
                        min_rejected_lb = lb
                    continue
                prev = by_exact.get(nxt)
                if prev is None or nc < prev:
                    by_exact[nxt] = nc

        if not by_exact:
            if math.isfinite(min_rejected_lb):
                return {
                    "code": "strict_bound",
                    "steps": off,
                    "failed_step": off,
                    "lower_bound": int(min_rejected_lb),
                    "best_cost": None,
                    "beam": 0,
                    "raw_candidates": raw_total,
                    "bound_prunes": bound_prunes,
                    "strict_ceiling_exclusive": ceiling or None,
                    "layers": layers + [{
                        "step": off,
                        "raw": raw,
                        "distinct_exact": 0,
                        "beam": 0,
                        "bound_prunes": layer_prunes,
                        "min_rejected_lb": int(min_rejected_lb),
                    }],
                }
            return {
                "code": "dead",
                "steps": off - 1,
                "failed_step": off,
                "lower_bound": math.inf,
                "best_cost": None,
                "beam": 0,
                "raw_candidates": raw_total,
                "bound_prunes": bound_prunes,
                "strict_ceiling_exclusive": ceiling or None,
                "layers": layers,
            }

        ranked = sorted(
            ((nc, v2.total_len(nxt), nxt) for nxt, nc in by_exact.items()),
            key=lambda x: (x[0], x[1], x[2]),
        )
        kept = ranked[: max(1, int(beam_width))]
        beam = [(nxt, nc) for nc, _total, nxt in kept]
        best_cost = min(cost for _state, cost in beam)
        layers.append({
            "step": off,
            "raw": raw,
            "distinct_exact": len(by_exact),
            "beam": len(beam),
            "best_cost": best_cost,
            "lower_bound": best_cost + remaining,
            "bound_prunes": layer_prunes,
        })

    best_cost = min(cost for _state, cost in beam)
    remaining = baseline_steps - (j + max_steps)
    return {
        "code": "ok",
        "steps": max_steps,
        "lower_bound": int(best_cost + remaining),
        "best_cost": int(best_cost),
        "beam": len(beam),
        "raw_candidates": raw_total,
        "bound_prunes": bound_prunes,
        "strict_ceiling_exclusive": ceiling or None,
        "layers": layers,
    }


# Preserve all of V16 except the physically exact compatibility evaluator.
v16.compatibility_probe = bounded_compatibility_probe

if __name__ == "__main__":
    v16.v13.main()
