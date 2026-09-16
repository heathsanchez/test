#!/usr/bin/env python3
"""ACC GS-Sub V3: exact compiler that carries quotient symmetries forward.

The quotient search itself is unchanged from solver_v2_gssub.py.  The only
mechanism change is in exact compilation: cyclic rotations/inversions applied
to the *source* relator no longer have to be undone after every quotient
substitution.  They may remain in the exact state and be reused by subsequent
quotient steps.  Every candidate edge is still replayed through the pinned
official transition function, and the complete candidate is still admitted
only by the official verifier in solver_v2_gssub.py.

The legacy signed compiler candidates are retained as a subset, so this is a
strict candidate-space extension rather than a replacement.
"""

from __future__ import annotations

import solver_v2_gssub as v2


_BASE_CANDIDATES = v2.compiled_superneighbor_candidates
_BASE_COMPILE = v2.compile_quotient_path_optimized


def _replay_edge(core, state, atomics, total_cap):
    """Replay one proposed exact edge and reject any intermediate cap breach."""
    cur = state
    for m in atomics:
        cur = core.apply_move(cur, m)
        if v2.total_len(cur) > total_cap:
            return None
    return cur


def compiled_superneighbor_candidates_carry(core, ns, state, desired, total_cap):
    """Exact GS-Sub realizations with persistent source symmetry.

    V2 deliberately restored the source relator byte-for-byte after each
    quotient substitution.  That is locally safe but can repeatedly pay for
    the same cyclic conjugations.  The GS-Sub quotient already identifies
    cyclic rotations and inversions, so an exact representative with the
    source left rotated/inverted is equally valid for the next quotient layer.

    We therefore retain those transformed source representatives in the beam.
    The desired quotient key is checked explicitly, and every atomic edge is
    replayed exactly before admission.
    """
    best_exact = {}

    # Preserve every legacy candidate.  The new compiler can never lose V2's
    # coverage merely because carry-symmetry representatives were added.
    for nxt, edge in _BASE_CANDIDATES(core, ns, state, desired, total_cap):
        best_exact[nxt] = tuple(edge)

    for i in (0, 1):
        j = 1 - i
        target_opts = v2.orientation_options(core, state[i], i)
        # Unlike V2, source inversions are also legal physical states to carry.
        source_opts = v2.orientation_options(core, state[j], j)
        mul_pos = 2 if i == 0 else 4
        mul_neg = 3 if i == 0 else 5

        for tw, tseq in target_opts:
            if not tw:
                continue
            for sw, sseq in source_opts:
                if not sw:
                    continue

                # Direct multiplication and multiply-by-inverse are both exact
                # official moves.  In either case the physically transformed
                # source `sw` is retained instead of being restored.
                for source_word, mul in ((sw, mul_pos), (core.invert(sw), mul_neg)):
                    if tw[-1] != -source_word[0]:
                        continue
                    new_word = core.free_reduce(tw + source_word)
                    nxt = (new_word, sw) if i == 0 else (sw, new_word)
                    if v2.total_len(nxt) > total_cap:
                        continue
                    if v2.gssub_key(ns, nxt) != desired:
                        continue

                    # Operations on the two distinct relators commute here;
                    # use target then source consistently and prove the result
                    # by replay rather than relying on that observation.
                    atomics = tuple(tseq) + tuple(sseq) + (mul,)
                    chk = _replay_edge(core, state, atomics, total_cap)
                    if chk != nxt:
                        continue

                    prev = best_exact.get(nxt)
                    if prev is None or len(atomics) < len(prev):
                        best_exact[nxt] = atomics

    return [(nxt, edge) for nxt, edge in best_exact.items()]


def compile_quotient_path_carry(
    core, ns, exact_initial, quotient_path, reverse_paths, total_cap, beam_width=4
):
    atomics, meta = _BASE_COMPILE(
        core, ns, exact_initial, quotient_path, reverse_paths, total_cap, beam_width
    )
    if isinstance(meta, dict) and meta.get("code") == "ok":
        meta = dict(meta)
        meta["compiler"] = "carry-symmetry-exact-beam-v2"
        if atomics is not None:
            meta["atomic_per_quotient_step"] = (
                len(atomics) / max(1, int(meta.get("quotient_steps") or 0))
            )
    return atomics, meta


# Patch only the compiler hooks.  Search, live filtering, stable derivation,
# official replay, reporting, and submission behavior remain V2 authority.
v2.compiled_superneighbor_candidates = compiled_superneighbor_candidates_carry
v2.compile_quotient_path_optimized = compile_quotient_path_carry


if __name__ == "__main__":
    v2.main()
