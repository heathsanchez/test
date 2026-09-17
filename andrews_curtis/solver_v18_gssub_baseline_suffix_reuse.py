#!/usr/bin/env python3
"""ACC GS-Sub V18: reuse the known baseline suffix exactly.

V17 closed the short carried-rejoin + fixed-baseline compatibility screen at the
strict boundary: the best exact lower bound was 464 against the live record
464.  The downstream V13 driver then called ACSolverX again from each rejoin
key.  That fresh solve is not required to reproduce the already-known baseline
continuation and can return an equal-or-longer quotient route.  When the margin
is one atomic move, even one gratuitous quotient step can erase a steal.

V18 changes only that handoff.  It keeps V17 bridge generation, carried exact
states, candidate-edge language, strict live-bound compiler, pinned verifier,
near-miss salvage, quota gate and strict-only publisher unchanged.  It freezes
the original ACSolverX baseline once, maps every quotient key on that path to
its *latest* occurrence, and serves the exact stored suffix for compatible
rejoins.  Non-baseline keys still use the original ACSolverX completion.
"""

from __future__ import annotations

import solver_v2_gssub as v2
import solver_v13_gssub_exact_prefix as v13
import solver_v17_gssub_bound_compatible_rejoin as v17


_original_complete_suffix = v13.complete_suffix
_baseline_suffixes = {}
_baseline_meta = {"nodes": 0, "seconds": 0.0, "steps": None}


def _cached_complete_suffix(ns, key, *, max_nodes, max_len):
    hit = _baseline_suffixes.get(key)
    if hit is not None:
        return hit, int(_baseline_meta["nodes"]), 0.0
    return _original_complete_suffix(ns, key, max_nodes=max_nodes, max_len=max_len)


def exact_prefix_search(
    core,
    ns,
    exact_initial,
    *,
    target_depth,
    beam_width,
    exact_per_key,
    prefix_count,
    qcap,
    total_cap,
    overhead_weight,
    atomic_ceiling_exclusive,
    seconds,
):
    """Run V17, but make the known baseline suffix authoritative downstream."""
    global _baseline_suffixes, _baseline_meta

    initial_key = v2.gssub_key(ns, exact_initial)
    baseline_path, nodes, elapsed = _original_complete_suffix(
        ns, initial_key, max_nodes=100000, max_len=qcap
    )
    _baseline_suffixes = {}
    _baseline_meta = {
        "nodes": int(nodes),
        "seconds": float(elapsed),
        "steps": None if baseline_path is None else len(baseline_path) - 1,
    }

    if baseline_path is not None:
        # Use the latest occurrence when a quotient key repeats.  This is the
        # shortest exact suffix already witnessed on the frozen baseline.
        latest = {}
        for i, state in enumerate(baseline_path):
            latest[v2.path_state_key(ns, state)] = i
        for key, i in latest.items():
            _baseline_suffixes[key] = baseline_path[i:]

        # V17 internally asks V13 for the initial baseline.  Serve the frozen
        # copy so we do not pay for a second equivalent solve.
        v13.complete_suffix = _cached_complete_suffix

    finals, meta = v17.v16.exact_prefix_search(
        core,
        ns,
        exact_initial,
        target_depth=target_depth,
        beam_width=beam_width,
        exact_per_key=exact_per_key,
        prefix_count=prefix_count,
        qcap=qcap,
        total_cap=total_cap,
        overhead_weight=overhead_weight,
        atomic_ceiling_exclusive=atomic_ceiling_exclusive,
        seconds=seconds,
    )
    meta = dict(meta)
    meta.update({
        "baseline_suffix_reuse": True,
        "baseline_suffix_keys": len(_baseline_suffixes),
        "baseline_suffix_steps": _baseline_meta.get("steps"),
        "baseline_suffix_nodes": _baseline_meta.get("nodes"),
        "baseline_suffix_seconds": _baseline_meta.get("seconds"),
    })
    return finals, meta


# V13 remains the authoritative driver/compiler/verifier.  Only its prefix
# selector and suffix handoff are replaced.
v13.exact_prefix_search = exact_prefix_search
v13.complete_suffix = _cached_complete_suffix

if __name__ == "__main__":
    v13.main()
