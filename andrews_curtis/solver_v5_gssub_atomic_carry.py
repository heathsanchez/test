#!/usr/bin/env python3
"""ACC GS-Sub V5: true carry-symmetry representative-aware atomic search.

V4's stated mechanism was representative-aware search using the V3 carry
compiler, but its grouped transition enumerator accidentally restored source
orientation after every quotient step (the V2 behavior).  This wrapper changes
only that verified implementation mismatch: source cyclic/inverse symmetry is
retained in the exact state, every candidate edge is replayed through the
pinned official transition function, and the V4 live-record bound/search logic
is otherwise unchanged.
"""

from __future__ import annotations

import solver_v4_gssub_atomic as v4

carry = v4.carry
v2 = v4.v2


def compiled_superneighbors_grouped_carry(core, ns, state, desired_keys, total_cap):
    """Enumerate requested GS-Sub neighbors once, retaining source symmetry.

    This is the grouped form of V3's carry compiler.  Unlike V4's original
    grouped enumerator, it does not undo source rotations and it allows source
    inversion to persist as an exact representative.  The legacy V3 single-key
    compiler remains a coverage fallback for any desired quotient key missed by
    the grouped pass.
    """
    desired_keys = set(desired_keys)
    if not desired_keys:
        return {}

    grouped = {key: {} for key in desired_keys}
    for i in (0, 1):
        j = 1 - i
        target_opts = v2.orientation_options(core, state[i], i)
        source_opts = v2.orientation_options(core, state[j], j)
        mul_pos = 2 if i == 0 else 4
        mul_neg = 3 if i == 0 else 5

        for tw, tseq in target_opts:
            if not tw:
                continue
            for sw, sseq in source_opts:
                if not sw:
                    continue
                for source_word, mul in ((sw, mul_pos), (core.invert(sw), mul_neg)):
                    if tw[-1] != -source_word[0]:
                        continue
                    atomics = tuple(tseq) + tuple(sseq) + (mul,)
                    nxt = carry._replay_edge(core, state, atomics, total_cap)
                    if nxt is None:
                        continue
                    key = v2.gssub_key(ns, nxt)
                    if key not in desired_keys:
                        continue
                    prev = grouped[key].get(nxt)
                    if prev is None or len(atomics) < len(prev):
                        grouped[key][nxt] = atomics

    # Coverage fallback uses the already-proven V3 carry compiler one key at a
    # time only where the grouped pass found nothing.
    missing = [key for key, by_exact in grouped.items() if not by_exact]
    for key in missing:
        for nxt, edge in carry.compiled_superneighbor_candidates_carry(
            core, ns, state, key, total_cap
        ):
            prev = grouped[key].get(nxt)
            if prev is None or len(edge) < len(prev):
                grouped[key][nxt] = tuple(edge)

    return {
        key: list(by_exact.items())
        for key, by_exact in grouped.items()
        if by_exact
    }


v4.compiled_superneighbors_grouped = compiled_superneighbors_grouped_carry


if __name__ == "__main__":
    v4.main()
