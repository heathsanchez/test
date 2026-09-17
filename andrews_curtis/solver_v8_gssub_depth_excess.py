#!/usr/bin/env python3
"""ACC GS-Sub V8: depth-rewarded low-excess true-carry search.

V7 established a new verified residual: all six excess-guided searches spent
2,400 seconds inside a huge shallow low-excess plateau.  Despite millions of
exact states and compiled edges, the deepest popped state was only depth 11.
That is incompatible with the known competitive quotient skeleton depths
(392 for ac-01910 and 438 for ac-04501).

This wrapper keeps V7's exact-state dominance, true-carry compiler, reverse
atlas, live/near-miss bounds, pinned official replay, and verifier authority.
It changes only queue order: depth is rewarded inside low-excess corridors so
search can actually follow long chains of one-atomic-move GS-Sub transitions.

    priority = excess_weight * (atomic_cost - quotient_depth)
             + guide_weight * max(total_relator_length - 2, 0)
             - depth_reward * quotient_depth
             + 0.001 * atomic_cost

The workflow portfolios excess_weight while fixing depth_reward=1.0.  Thus it
tests several explicit overhead-vs-depth exchange rates without relaxing any
certificate or publication gate.
"""

from __future__ import annotations

import os

import solver_v7_gssub_excess_guided as v7


def depth_rewarded_priority(g, depth, state, excess_weight, guide_weight):
    depth_reward = float(os.environ.get("ACC_DEPTH_REWARD", "1.0"))
    excess = max(0, g - depth)
    return (
        excess_weight * excess
        + guide_weight * max(0, v7.v2.total_len(state) - 2)
        - depth_reward * depth
        + 0.001 * g
    )


v7.priority = depth_rewarded_priority


if __name__ == "__main__":
    print(
        "DEPTH_EXCESS_POLICY",
        {
            "depth_reward": float(os.environ.get("ACC_DEPTH_REWARD", "1.0")),
            "authority": "v7 exact true-carry + pinned verifier",
        },
        flush=True,
    )
    v7.main()
