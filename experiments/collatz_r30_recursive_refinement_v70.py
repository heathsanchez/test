#!/usr/bin/env python3
"""V70: repair the V69 recursive refinement controller and replay the same evidence.

V69's numerical controller advanced from depth h to h+1 without first exposing
bit h. That off-by-one error was invisible for the first two expected separators
because their new low bit was 0, then failed exactly when the depth-33 separator
required that bit to be 1.

This file changes only that controller step. It reuses V69's exact reverse
audits and the already kernel-checked split consumers. Global Collatz remains
UNKNOWN.
"""
from __future__ import annotations

import hashlib
import json

import collatz_r30_recursive_refinement_v69 as v69
import collatz_r30_separator_v68 as v68

R = 30


def assert_descendant_cover(live, root_h, depth):
    """The live residues must be exactly distinct descendants of r=30.

    A residue at depth d names one congruence cell modulo 2^d. Descendants of
    the root depth h therefore differ from R by a multiple of 2^h and, before
    any closure, there must be 2^(d-h) distinct such residues.
    """
    assert len(live) == len(set(live))
    assert len(live) == 2 ** (depth - root_h)
    mod = 2 ** root_h
    bound = 2 ** depth
    for r in live:
        assert r % mod == R % mod
        delta = r - R
        assert 0 <= delta < bound
        assert delta % mod == 0


def first_split(root_h, target_h):
    # At entry, live is the one residual cell at depth root_h.
    live = [R]
    levels = []
    first = None

    for h in range(root_h + 1, target_h + 1):
        # Correct refinement: expose the bit at position h-1 BEFORE evaluating
        # consequences at depth h.
        live = [x for r in live for x in (r, r + 2 ** (h - 1))]
        assert_descendant_cover(live, root_h, h)

        closed = []
        residual = []
        for r in live:
            c = v68.simple_certificate(r, h)
            qhits = v68.q7_mergers(r, h)
            if c is None and not qhits:
                residual.append(r)
                continue
            row = dict(c if c is not None else qhits[0])
            row["q7_hits"] = len(qhits)
            closed.append(row)

        levels.append(
            dict(
                depth=h,
                input_cells=len(live),
                expected_descendant_cells=2 ** (h - root_h),
                closed=len(closed),
                residual=len(residual),
                closed_residues=[z["r"] for z in closed],
            )
        )

        if closed:
            assert len(closed) == 1
            first = closed[0]
            break

        live = residual

    assert first is not None
    e = v69.EXPECTED_SPLITS[root_h]
    assert h == e["depth"]
    assert first["r"] == e["residue"]
    assert first["kind"] == e["kind"]
    assert first["k"] == e["k"]

    suffix = (first["r"] - R) // 2 ** root_h
    assert suffix == e["suffix"]
    assert first["q7_hits"] >= 1

    return dict(
        root_depth=root_h,
        levels=levels,
        first_consequential_depth=h,
        extra_parameter_bits=h - root_h,
        suffix_value=suffix,
        child=first,
    )


def main():
    audits = []
    splits = []
    for h in (22, 25, 29, 33):
        audits.append(v69.audit_root(h))
        splits.append(first_split(h, v69.EXPECTED_SPLITS[h]["depth"]))

    suffixes = [z["suffix_value"] for z in splits]
    assert suffixes == [6, 6, 1, 21]

    # Explicitly prove the V69 failure mode was indexing, not a missing
    # consequence at the third/fourth expected separators.
    assert splits[2]["child"]["r"] == 536_870_942
    assert splits[2]["child"]["kind"] == "D"
    assert splits[2]["child"]["k"] == 92
    assert splits[3]["child"]["r"] == 180_388_626_462
    assert splits[3]["child"]["kind"] == "D"
    assert splits[3]["child"]["k"] == 97

    result = {
        "schema": "COLLATZ_R30_RECURSIVE_REFINEMENT_V70",
        "parent_failed_v69_head": "f11398b611add1d6606c181ebbf8a0a71af359d4",
        "parent_warranted_v68_head": "8bff295a9c4167f819520d86b2ce4052460598d3",
        "protected_present": ["original_source", "current_endpoint"],
        "controller_correction": {
            "v69_failure_class": "OFF_BY_ONE_REFINEMENT_BIT_EXPOSURE",
            "old_effect": "depth h+1 was evaluated before exposing bit h",
            "correct_rule": "children at depth h are r and r + 2^(h-1)",
            "coverage_invariant": "2^(depth-root_depth) distinct descendants before first closure",
        },
        "unsplit_reverse_audits": audits,
        "consequence_forced_splits": splits,
        "total_exact_reverse_states": sum(z["exact_reverse_states"] for z in audits),
        "all_nonexpanding_candidates_are_identity": all(
            z["nonexpanding_candidates"] == z["identity_candidates"]
            and z["strict_lower_source_candidates"] == 0
            for z in audits
        ),
        "periodic_suffix_6_candidate": "REJECTED_PROSPECTIVELY",
        "periodic_suffix_sequence": suffixes,
        "warranted_bounded_interpretation": (
            "After correcting the refinement controller, the same four ancestry-only "
            "unsplit audits remain negative and the first protected separator on each "
            "tested zero sibling is recovered at depths 25, 29, 33 and 38 with suffixes "
            "6, 6, 1 and 21. No fixed cadence or suffix law is promoted."
        ),
        "next_residual": (
            "Continue from the depth-38 zero sibling. Before adding any semantic "
            "coordinate, test whether ancestry-only reverse candidates are a structural "
            "obstruction for that lineage, or expose only the next consequence-forced "
            "source bit until an existing class-merger capability applies."
        ),
        "status": "CANDIDATE_PENDING_HOSTED_QUALIFICATION",
        "global_collatz": "UNKNOWN",
        "qed": False,
    }

    result["certificate_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
