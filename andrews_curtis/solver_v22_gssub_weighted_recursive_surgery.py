#!/usr/bin/env python3
"""ACC GS-Sub V22: weighted 418-step baseline + recursive exact suffix surgery.

Verified residual motivating this composition:
- ac-03665 has a live strict record of 435 atomic moves.
- V21 found a pinned-verifier-clean 418-step quotient baseline, so the old
  quotient-length obstruction is gone.
- V21's exact carried-prefix search found bridges with optimistic lower bound
  426/427, but every strict continuation hit a physical lower bound of exactly
  435 at the first rigid suffix transition. Deeper prefix search did not move
  that compatibility boundary.

V22 changes only the verified failure boundary: after choosing a carried exact
state on the weighted baseline, it reuses V20's bounded recursive suffix surgery
instead of committing immediately to the rigid weighted suffix. The candidate
language, grouped exact edge replay, strict live ceiling, and pinned official
verification remain unchanged.
"""

from __future__ import annotations

# Importing V20 installs recursive exact suffix surgery as V13's seeded suffix
# compiler. Importing V21 installs the 0.010 depth-weighted quotient proposal as
# V13's suffix search. They share the same imported V13 module object, so these
# two verified mechanisms compose without widening the move language.
import solver_v20_gssub_recursive_suffix_surgery as v20
import solver_v21_gssub_weighted_bound_rejoin as v21  # noqa: F401


if __name__ == "__main__":
    v20.v13.main()
