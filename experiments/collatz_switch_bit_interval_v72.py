#!/usr/bin/env python3
"""V72: test the smallest source-bit invariant left by V60/V71.

V60 proves on the frozen prospective corpus that every genuine centre switch
strictly increases 2-adic precision around one fixed starting owner m0.
A tempting finish would say every switch reveals at least one new 1-bit of m0.
The already-qualified V60 artifact contains counterexamples to that strong law.

V72 therefore tests the next strictly weaker sufficient candidate:
  no two genuine switches can consecutively refine only through zero bits.

Because switch precision intervals are disjoint and strictly increasing, a
universal no-two-zero-only law would force infinitely many nonzero bit
intervals along any infinite switch sequence. A natural m0 has only finitely
many 1-bits, so that would exclude infinite switching once same-centre chains
are handled by the already-proved fixed-centre exhaustion theorem.

This is bounded theorem discovery on the exact V60 corpus, not Collatz QED.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
import os
import sys

# Qualification may bind this analysis to the exact V60 source commit rather
# than whatever Collatz modules happen to exist on the current branch.
frozen = os.environ.get("V60_EXPERIMENTS_DIR")
if frozen:
    sys.path.insert(0, frozen)

with redirect_stdout(io.StringIO()):
    import collatz_crystal_pulled_centre_height_v60 as v60

PARENT_CERT = "0983c58430f54935a9af9d5f115e44653831c6770aec57eb1593df4a93816ac0"


def interval_bits(num: int, den: int, lo: int, hi: int):
    assert 0 <= lo < hi
    assert den & 1
    modulus = 1 << hi
    residue = (num * pow(den, -1, modulus)) % modulus
    width = hi - lo
    bits = (residue >> lo) & ((1 << width) - 1)
    return residue, bits


def main():
    assert v60.result["certificate_sha256"] == PARENT_CERT
    assert v60.result["centre_switches"] == 613
    assert v60.result["every_switch_strictly_increases_source_precision"]
    assert v60.result["same_center_preserves_pulled_center_and_precision"]

    total = 0
    zero_only = 0
    nonzero = 0
    zero_witnesses = []
    consecutive_zero_witnesses = []
    max_zero_run = 0

    for streak in v60.streaks:
        rows = streak["rows"]
        prev = None
        switch_labels = []
        switch_rows = []

        for row in rows:
            if prev is None:
                prev = row
                continue

            relation = row["relation_from_previous"]
            if relation == "SAME_CENTER":
                assert row["source_precision_v2"] == prev["source_precision_v2"]
                prev = row
                continue

            if relation != "SWITCH":
                prev = row
                continue

            lo = prev["source_precision_v2"]
            hi = row["source_precision_v2"]
            assert hi > lo >= 0

            num, den = row["pulled_center"]
            residue, bits = interval_bits(num, den, lo, hi)
            is_zero = bits == 0

            rec = {
                "source": streak["source"],
                "anchor": streak["anchor"],
                "from_depth": prev["depth"],
                "to_depth": row["depth"],
                "from_precision": lo,
                "to_precision": hi,
                "width": hi - lo,
                "new_interval_bits": bits,
                "new_interval_popcount": bits.bit_count(),
                "pulled_center": row["pulled_center"],
                "previous_pulled_center": prev["pulled_center"],
                "law": row["law"],
                "previous_law": prev["law"],
            }

            total += 1
            if is_zero:
                zero_only += 1
                if len(zero_witnesses) < 20:
                    zero_witnesses.append(rec)
            else:
                nonzero += 1

            switch_labels.append(is_zero)
            switch_rows.append(rec)
            prev = row

        run = 0
        for i, is_zero in enumerate(switch_labels):
            if is_zero:
                run += 1
                max_zero_run = max(max_zero_run, run)
                if run >= 2 and len(consecutive_zero_witnesses) < 20:
                    consecutive_zero_witnesses.append(
                        {
                            "source": streak["source"],
                            "anchor": streak["anchor"],
                            "first": switch_rows[i - 1],
                            "second": switch_rows[i],
                            "run_length_at_witness": run,
                        }
                    )
            else:
                run = 0

    assert total == 613
    assert zero_only > 0  # strong one-bit-per-switch law is already falsified.

    result = {
        "schema": "COLLATZ_SWITCH_BIT_INTERVAL_V72",
        "parent": "COLLATZ_CRYSTAL_PULLED_CENTRE_HEIGHT_V60",
        "parent_certificate_sha256": PARENT_CERT,
        "qualified_switches_replayed": total,
        "strong_candidate_every_switch_has_nonzero_new_interval": "REJECTED",
        "zero_only_switches": zero_only,
        "nonzero_interval_switches": nonzero,
        "max_consecutive_zero_only_switches": max_zero_run,
        "candidate_no_two_consecutive_zero_only": max_zero_run <= 1,
        "zero_only_witnesses": zero_witnesses,
        "consecutive_zero_witnesses": consecutive_zero_witnesses,
        "candidate_consequence_if_universal": (
            "Together with fixed-centre exhaustion, no two consecutive zero-only "
            "switch refinements would force infinitely many disjoint nonzero bit "
            "intervals along any infinite switch sequence, impossible for a finite "
            "natural starting owner."
        ),
        "promotion_boundary": (
            "Exact replay of the frozen 613-switch V60 corpus only. Even if the "
            "weaker candidate survives, QED still requires a universal source-admitted "
            "switch classification and a proof that every infinite no-exit zero-tail "
            "continuation is covered by same-centre exhaustion, a contracting exit, "
            "or these switch refinements."
        ),
        "global_collatz": "UNKNOWN",
        "qed": False,
    }
    result["certificate_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
