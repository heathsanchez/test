#!/usr/bin/env python3
"""V73: contract the surviving V72 no-two-zero-switch candidate to algebra.

Parent V72, on the frozen qualified V60 corpus, found 48 genuine centre
switches whose newly earned 2-adic precision interval contains only zero bits,
565 switches whose interval contains a 1, and no consecutive pair of zero-only
switches.

This experiment adds no state coordinate. It asks whether those 48 exceptional
switches share an already-existing affine-law signature, and what the next
genuine switch must expose when one exists. The goal is to find the smallest
algebraic statement worth formalizing, not another empirical feature.

Bounded theorem discovery only; global Collatz remains UNKNOWN.
"""
from __future__ import annotations

from collections import Counter
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
import sys

frozen = os.environ.get("V60_EXPERIMENTS_DIR")
if frozen:
    sys.path.insert(0, frozen)

with redirect_stdout(io.StringIO()):
    import collatz_crystal_pulled_centre_height_v60 as v60

PARENT_V60_CERT = "0983c58430f54935a9af9d5f115e44653831c6770aec57eb1593df4a93816ac0"
PARENT_V72_QUAL = "fe3149242a1499e40efcab04c0c9da908984304de974613d924361b9d8ee9946"


def interval_bits(num: int, den: int, lo: int, hi: int):
    assert 0 <= lo < hi
    assert den & 1
    mod = 1 << hi
    residue = (num * pow(den, -1, mod)) % mod
    width = hi - lo
    bits = (residue >> lo) & ((1 << width) - 1)
    return residue, bits


def sig(row):
    A, B, P, D = map(int, row["law"])
    return (row.get("anchor"), A, B, P, D)


def basic_anchor_law(row):
    anchor, A, B, P, D = sig(row)
    return (
        anchor is not None
        and A == 3 ** anchor
        and B == 1
        and P == 2 ** (anchor + 1)
        and D == anchor + 1
    )


def switch_records(streak):
    out = []
    prev = None
    for row in streak["rows"]:
        if prev is None:
            prev = row
            continue
        rel = row["relation_from_previous"]
        if rel == "SAME_CENTER":
            assert row["source_precision_v2"] == prev["source_precision_v2"]
            prev = row
            continue
        if rel != "SWITCH":
            prev = row
            continue
        lo = prev["source_precision_v2"]
        hi = row["source_precision_v2"]
        num, den = row["pulled_center"]
        _, bits = interval_bits(num, den, lo, hi)
        rec = {
            "source": streak["source"],
            "anchor": streak["anchor"],
            "from_depth": prev["depth"],
            "to_depth": row["depth"],
            "from_precision": lo,
            "to_precision": hi,
            "width": hi - lo,
            "bits": bits,
            "popcount": bits.bit_count(),
            "zero_only": bits == 0,
            "law": list(map(int, row["law"])),
            "previous_law": list(map(int, prev["law"])),
            "local_center": row["local_center"],
            "previous_local_center": prev["local_center"],
            "pulled_center": row["pulled_center"],
            "previous_pulled_center": prev["pulled_center"],
            "basic_anchor_law": basic_anchor_law({**row, "anchor": streak["anchor"]}),
        }
        out.append(rec)
        prev = row
    return out


def main():
    assert v60.result["certificate_sha256"] == PARENT_V60_CERT
    assert v60.result["centre_switches"] == 613

    all_switches = []
    zero_rows = []
    successor_rows = []
    terminal_zero = []

    zero_law_hist = Counter()
    zero_anchor_hist = Counter()
    zero_width_hist = Counter()
    successor_law_hist = Counter()
    successor_lsb_hist = Counter()
    pair_hist = Counter()
    previous_law_hist = Counter()

    for streak in v60.streaks:
        sw = switch_records(streak)
        all_switches.extend(sw)
        for i, rec in enumerate(sw):
            if not rec["zero_only"]:
                continue
            zero_rows.append(rec)
            zero_law_hist[tuple(rec["law"])] += 1
            zero_anchor_hist[rec["anchor"]] += 1
            zero_width_hist[rec["width"]] += 1
            previous_law_hist[tuple(rec["previous_law"])] += 1

            if i + 1 >= len(sw):
                terminal_zero.append(rec)
                continue

            nxt = sw[i + 1]
            successor_rows.append({
                "zero": rec,
                "next": nxt,
            })
            assert not nxt["zero_only"]  # parent V72 bounded authority
            successor_law_hist[tuple(nxt["law"])] += 1
            successor_lsb_hist[nxt["bits"] & 1] += 1
            pair_hist[(tuple(rec["law"]), tuple(nxt["law"]))] += 1

    assert len(all_switches) == 613
    assert len(zero_rows) == 48

    zero_basic = sum(r["basic_anchor_law"] for r in zero_rows)
    successor_all_lsb_one = bool(successor_rows) and all(
        p["next"]["bits"] & 1 for p in successor_rows
    )

    # Smallest signature tournament.
    if zero_basic == len(zero_rows):
        zero_signature_status = "ALL_ZERO_ONLY_ARE_BASIC_ANCHOR_LAW"
    else:
        zero_signature_status = "BASIC_ANCHOR_LAW_NOT_COMPLETE"

    result = {
        "schema": "COLLATZ_ZERO_SWITCH_SUCCESSOR_V73",
        "parent_v60_certificate_sha256": PARENT_V60_CERT,
        "parent_v72_qualification_sha256": PARENT_V72_QUAL,
        "switches_replayed": len(all_switches),
        "zero_only_switches": len(zero_rows),
        "zero_only_with_observed_next_switch": len(successor_rows),
        "zero_only_terminal_in_observed_streak": len(terminal_zero),
        "zero_signature_status": zero_signature_status,
        "zero_only_basic_anchor_law_count": zero_basic,
        "zero_only_law_histogram": {
            repr(k): v for k, v in sorted(zero_law_hist.items(), key=lambda z: repr(z[0]))
        },
        "zero_only_anchor_histogram": dict(sorted(zero_anchor_hist.items())),
        "zero_only_width_histogram": dict(sorted(zero_width_hist.items())),
        "zero_only_previous_law_histogram": {
            repr(k): v for k, v in sorted(previous_law_hist.items(), key=lambda z: (-z[1], repr(z[0])))
        },
        "successor_law_histogram": {
            repr(k): v for k, v in sorted(successor_law_hist.items(), key=lambda z: (-z[1], repr(z[0])))
        },
        "successor_new_interval_lsb_histogram": dict(sorted(successor_lsb_hist.items())),
        "all_observed_successors_have_new_interval_lsb_one": successor_all_lsb_one,
        "zero_to_successor_pair_histogram": {
            repr(k): v for k, v in sorted(pair_hist.items(), key=lambda z: (-z[1], repr(z[0])))
        },
        "sample_zero_only": zero_rows[:12],
        "sample_zero_successors": successor_rows[:12],
        "candidate_consequence": (
            "If the exact zero-only signature and a forced nonzero successor can "
            "be proved for every source-admitted genuine centre switch, then an "
            "infinite switch execution forces infinitely many nonzero source-bit "
            "intervals. Together with fixed-centre exhaustion this would exclude "
            "an eventually-zero natural owner."
        ),
        "next_rule": (
            "Formalize only the smallest exact signature that survives this gate. "
            "If zero-only cases do not collapse to an existing affine law, reject "
            "the pair theorem route and return to the first exact separator."
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
