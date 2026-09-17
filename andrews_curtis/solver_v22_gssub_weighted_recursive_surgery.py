#!/usr/bin/env python3
"""ACC GS-Sub V22: weighted <=418-step baseline + recursive exact suffix surgery.

Verified residual motivating this composition:
- ac-03665 has a live strict record of 435 atomic moves.
- V21 found a pinned-verifier-clean 418-step quotient baseline, so the old
  quotient-length obstruction is gone.
- V21's exact carried-prefix search found bridges with optimistic lower bound
  426/427, but every strict continuation hit a physical lower bound of exactly
  435 at the first rigid suffix transition. Deeper prefix search did not move
  that compatibility boundary.
- The baseline-diversity probe later found an even shorter 416-step weighted
  proposal at depth weight 0.012. That is an improvement, not a composition
  regression, so the guard must accept weighted baselines no longer than the
  verified 418-step reference while still rejecting fallback/failed proposals.

V22 changes only the verified failure boundary: after choosing a carried exact
state on the weighted baseline, it reuses V20's bounded recursive suffix surgery
instead of committing immediately to the rigid weighted suffix. The candidate
language, grouped exact edge replay, strict live ceiling, and pinned official
verification remain unchanged.

Composition note: V18 freezes its baseline proposal by capturing
``_original_complete_suffix`` at import time. Importing V21 later therefore does
not by itself replace the baseline used by V18. V22 explicitly wires V21's
weighted proposal into that captured hook and guards against silent fallback to
the old 438-step route.
"""

from __future__ import annotations

import solver_v20_gssub_recursive_suffix_surgery as v20
import solver_v21_gssub_weighted_bound_rejoin as v21


# V20 imports V18, whose exact_prefix_search calls this captured hook directly.
# Point it at the verified weighted proposal, then keep V18's cache authoritative
# for downstream rejoin suffixes. This is the composition boundary V22 intended.
v20.v18._original_complete_suffix = v21.weighted_complete_suffix
v20.v13.complete_suffix = v20.v18._cached_complete_suffix

_v18_exact_prefix_search = v20.v18.exact_prefix_search


def weighted_recursive_exact_prefix_search(*args, **kwargs):
    finals, meta = _v18_exact_prefix_search(*args, **kwargs)
    got = meta.get("baseline_suffix_steps")
    if got is None or got > 418:
        raise RuntimeError(
            f"weighted baseline composition regression: expected <=418 steps, got {got}"
        )
    return finals, meta


v20.v13.exact_prefix_search = weighted_recursive_exact_prefix_search


if __name__ == "__main__":
    v20.v13.main()
