#!/usr/bin/env python3
"""Strict-only wrapper for ACC continuous publication.

The underlying V5 publisher already performs pinned-verifier replay, two fresh
live-record reads immediately before POST, authenticated quota accounting and
terminal submission checks.  This wrapper narrows its scoring policy so a live
tie is never publishable: only an unsolved row or a strict improvement can pass.
"""

import continuous_aggregate_v5 as v5

_base_scoring_candidate = v5.scoring_candidate


def strict_scoring_candidate(row, candidate_len, our_best=None):
    ok, reason = _base_scoring_candidate(row, candidate_len, our_best)
    if ok and reason == "scoring_tie":
        return False, "tie_disallowed_strict_only"
    return ok, reason


v5.scoring_candidate = strict_scoring_candidate

if __name__ == "__main__":
    v5.main()
