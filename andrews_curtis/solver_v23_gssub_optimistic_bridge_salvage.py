#!/usr/bin/env python3
"""ACC GS-Sub V23: salvage low-optimistic bridges under recursive suffix surgery.

Verified residual motivating this phase:
- the corrected V22 run uses the pinned 418-step weighted baseline;
- rigid compatibility ranking still selects only the best short-horizon baseline
  followers before recursive surgery is attempted;
- V22 found no strict candidate and its selected best bridge hit a physical
  lower bound of exactly 435 against the live 435 record;
- yet the same exact bridge generator reports an optimistic bridge lower bound
  of 426, so low-optimistic carried states are being discarded before the new
  recursive-surgery continuation mechanism can evaluate them.

V23 changes only bridge *selection*.  It keeps the exact carried-state search,
weighted 418-step baseline, grouped official-move compiler, recursive suffix
surgery, strict live ceiling, and pinned verifier unchanged.  The short rigid
compatibility probe is still executed and preserved as evidence, but finalists
are ranked by their exact optimistic lower bound so the new surgery mechanism
gets a chance to salvage states that the old rigid-suffix selector rejected.

No candidate produced here has authority until V13/V20 replays it and the pinned
official verifier accepts it; publication remains the external strict-only gate.
"""

from __future__ import annotations

import math

import solver_v16_gssub_compatible_rejoin as v16
import solver_v22_gssub_weighted_recursive_surgery as v22


_original_probe = v16.compatibility_probe


def optimistic_selection_probe(
    core,
    ns,
    bridge,
    baseline_keys,
    total_cap,
    *,
    lookahead,
    beam_width,
):
    """Preserve rigid compatibility evidence but rank by optimistic exact LB."""
    pm = dict(
        _original_probe(
            core,
            ns,
            bridge,
            baseline_keys,
            total_cap,
            lookahead=lookahead,
            beam_width=beam_width,
        )
    )
    physical_lb = pm.get("lower_bound", math.inf)
    optimistic_lb = int(bridge["optimistic_baseline_cost"])
    pm["physical_lower_bound"] = physical_lb
    pm["selection_lower_bound"] = optimistic_lb
    pm["selection_mode"] = "optimistic_residual_salvage"
    # V16 sorts finalists by the field named lower_bound.  Override that field
    # only for selector ranking; the physical value above remains in evidence.
    pm["lower_bound"] = optimistic_lb
    return pm


v16.compatibility_probe = optimistic_selection_probe

_base_exact_prefix_search = v22.v20.v13.exact_prefix_search


def exact_prefix_search_with_selector_evidence(*args, **kwargs):
    finals, meta = _base_exact_prefix_search(*args, **kwargs)
    meta = dict(meta)
    meta["bridge_selection_mode"] = "optimistic_residual_salvage"
    meta["selection_note"] = (
        "rigid compatibility was retained as physical_lower_bound evidence; "
        "finalist ranking used optimistic_baseline_cost so recursive surgery "
        "can evaluate previously discarded bridges"
    )
    for f in finals:
        pm = f.get("compatibility_probe") or {}
        if "physical_lower_bound" in pm:
            f["physical_compatibility_lb"] = pm["physical_lower_bound"]
            f["selection_lower_bound"] = pm.get("selection_lower_bound")
    return finals, meta


v22.v20.v13.exact_prefix_search = exact_prefix_search_with_selector_evidence


if __name__ == "__main__":
    v22.v20.v13.main()
