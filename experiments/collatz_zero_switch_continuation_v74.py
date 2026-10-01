#!/usr/bin/env python3
"""V74: extend only the V73 zero-only switches whose frozen streak had no next switch.

V72 found no consecutive zero-only genuine centre switches in the qualified
613-switch V60 corpus. V73 showed that 44/48 zero-only switches sit at the end
of their observed pulled-centre streak, so the pair law is under-tested exactly
where it matters.

V74 changes no state and no merger law. It extends only those 44 exact natural
sources under the unchanged return machinery. Each target is classified by the
first consequential continuation after the zero-only switch:
  * protected progress / exit,
  * next genuine switch with nonzero or zero-only newly earned source bits,
  * a pulled-centre streak boundary/reset,
  * or still censored at the extended cap.

A next zero-only switch rejects the surviving V72 pair candidate. A reset is a
different residual: transport of protected source precision across the streak
boundary must be proved before the pair law can be used globally.

Bounded continuation experiment only. Global Collatz remains UNKNOWN.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
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
    import collatz_crystal_nonpositive_budget_kernel_v53 as v53
    import collatz_crystal_phase_normalized_return_v40 as v40

PARENT_V60_CERT = "0983c58430f54935a9af9d5f115e44653831c6770aec57eb1593df4a93816ac0"
PARENT_V72_QUAL = "fe3149242a1499e40efcab04c0c9da908984304de974613d924361b9d8ee9946"
PARENT_V73_QUAL = "f565153ca7b22adbeaea591ec0b781e0973b8e744c625285c9c1b68cf9db9d7b"
EXTENDED_CAP = 5000


def interval_bits(num: int, den: int, lo: int, hi: int):
    assert 0 <= lo < hi
    assert den & 1
    mod = 1 << hi
    residue = (num * pow(den, -1, mod)) % mod
    width = hi - lo
    bits = (residue >> lo) & ((1 << width) - 1)
    return residue, bits


def switch_records_from_rows(streak):
    rows = streak["rows"]
    prev = None
    out = []
    for row in rows:
        if prev is None:
            prev = row
            continue
        rel = row["relation_from_previous"]
        if rel == "SAME_CENTER":
            prev = row
            continue
        if rel != "SWITCH":
            prev = row
            continue
        lo = prev["source_precision_v2"]
        hi = row["source_precision_v2"]
        num, den = row["pulled_center"]
        _, bits = interval_bits(num, den, lo, hi)
        out.append({
            "source": streak["source"],
            "anchor": streak["anchor"],
            "from_depth": prev["depth"],
            "to_depth": row["depth"],
            "from_precision": lo,
            "to_precision": hi,
            "width": hi - lo,
            "bits": bits,
            "zero_only": bits == 0,
            "law": list(map(int, row["law"])),
            "previous_law": list(map(int, prev["law"])),
        })
        prev = row
    return out


def frozen_terminal_zero_targets():
    out = []
    for streak in v60.streaks:
        sw = switch_records_from_rows(streak)
        for i, rec in enumerate(sw):
            if rec["zero_only"] and i + 1 == len(sw):
                out.append(rec)
    assert len(out) == 44
    return out


def event_row(e):
    k = v53.reduced_key(e)
    if k is None:
        return None
    cl = v53.classify_event(e)
    return {
        "anchor": e["anchor"],
        "k0": e["k0"],
        "k1": e["k1"],
        "m0": e["m0"],
        "m1": e["m1"],
        "key": k,
        **cl,
    }


def center(row):
    return Fraction(row["B"], row["P"] - row["A"])


def rat_v2(x: Fraction):
    if x == 0:
        return None
    def v2z(n):
        n = abs(n)
        return (n & -n).bit_length() - 1
    return v2z(x.numerator) - v2z(x.denominator)


def build_extended_streaks(source: int, anchor: int):
    rr = v40.actual_episode_returns(f"v74-{source}-{anchor}", source, EXTENDED_CAP)
    rows = []
    for e in rr["events"]:
        if e["anchor"] != anchor:
            continue
        z = event_row(e)
        if z is not None:
            rows.append(z)
    rows.sort(key=lambda z: (z["k0"], z["k1"]))

    # Exact V53 residual-to-residual transitions.
    trs = []
    for i, cur in enumerate(rows):
        if not cur["residual"]:
            continue
        if i + 1 >= len(rows):
            continue
        nxt = rows[i + 1]
        if nxt["residual"]:
            trs.append({"src": cur, "dst": nxt})

    chunks = []
    cur = []
    for tr in trs:
        if cur and cur[-1]["dst"]["k0"] != tr["src"]["k0"]:
            chunks.append(cur)
            cur = []
        cur.append(tr)
    if cur:
        chunks.append(cur)

    streaks = []
    for chunk in chunks:
        states = [chunk[0]["src"]] + [tr["dst"] for tr in chunk]
        m_start = states[0]["m0"]
        Abar, Bbar, Pbar = 1, 0, 1
        outrows = []
        prev_pull = None
        prev_prec = None
        prev_local = None
        for i, s in enumerate(states):
            c = center(s)
            pulled = (Pbar * c - Bbar) / Abar
            prec = rat_v2(Fraction(m_start) - pulled)
            assert prec is not None
            relation = "START"
            if prev_pull is not None:
                if c == prev_local:
                    assert pulled == prev_pull
                    assert prec == prev_prec
                    relation = "SAME_CENTER"
                else:
                    assert prec > prev_prec
                    relation = "SWITCH"
            outrows.append({
                "index": i,
                "depth": [s["k0"], s["k1"]],
                "law": [str(s["A"]), str(s["B"]), str(s["P"]), s["D"]],
                "local_center": [c.numerator, c.denominator],
                "pulled_center": [pulled.numerator, pulled.denominator],
                "source_precision_v2": prec,
                "relation_from_previous": relation,
            })
            Abar, Bbar, Pbar = (
                s["A"] * Abar,
                s["A"] * Bbar + s["B"] * Pbar,
                s["P"] * Pbar,
            )
            prev_pull, prev_prec, prev_local = pulled, prec, c
        streaks.append({
            "source": str(source),
            "anchor": anchor,
            "rows": outrows,
            "states": len(outrows),
        })
    return rr, rows, streaks


def first_after_target(target, rr, event_rows, streaks):
    target_depth = target["to_depth"]

    # First try to find the same switch in an extended pulled-centre streak and
    # inspect the next genuine switch in that same lawful coordinate system.
    for st in streaks:
        sw = switch_records_from_rows(st)
        for i, rec in enumerate(sw):
            if (
                rec["to_depth"] == target_depth
                and rec["law"] == target["law"]
                and rec["zero_only"]
            ):
                if i + 1 < len(sw):
                    nxt = sw[i + 1]
                    return {
                        "outcome": "NEXT_SWITCH_ZERO" if nxt["zero_only"] else "NEXT_SWITCH_NONZERO",
                        "target": target,
                        "next_switch": nxt,
                    }

    # If the old pulled streak does not continue, classify the first exact
    # same-anchor event after the target. A protected-progress event closes the
    # residual; a later residual separated by a gap is a transport/reset
    # obligation rather than evidence for or against the within-streak pair law.
    after = [r for r in event_rows if [r["k0"], r["k1"]] > target_depth]
    if after:
        nxt = after[0]
        if not nxt["residual"]:
            return {
                "outcome": "PROTECTED_PROGRESS",
                "target": target,
                "next_event_depth": [nxt["k0"], nxt["k1"]],
                "immediate_progress": nxt["immediate_progress"],
                "floor_progress": nxt["floor_progress"],
            }
        return {
            "outcome": "STREAK_RESET_TO_RESIDUAL",
            "target": target,
            "next_event_depth": [nxt["k0"], nxt["k1"]],
            "next_event_law": [nxt["A"], nxt["B"], nxt["P"], nxt["D"]],
        }

    ex = rr["first_exit"]
    if ex is not None and ex["depth"] >= target_depth[1]:
        return {
            "outcome": "ORDINARY_EXIT",
            "target": target,
            "exit": ex,
        }

    return {
        "outcome": "STILL_CENSORED",
        "target": target,
        "cap": EXTENDED_CAP,
        "note": rr["note"],
    }


def main():
    assert v60.result["certificate_sha256"] == PARENT_V60_CERT
    targets = frozen_terminal_zero_targets()

    outcomes = []
    counts = Counter()
    for target in targets:
        source = int(target["source"])
        anchor = target["anchor"]
        rr, event_rows, streaks = build_extended_streaks(source, anchor)
        out = first_after_target(target, rr, event_rows, streaks)
        outcomes.append(out)
        counts[out["outcome"]] += 1

    next_zero = [x for x in outcomes if x["outcome"] == "NEXT_SWITCH_ZERO"]
    next_nonzero = [x for x in outcomes if x["outcome"] == "NEXT_SWITCH_NONZERO"]
    reset = [x for x in outcomes if x["outcome"] == "STREAK_RESET_TO_RESIDUAL"]
    censored = [x for x in outcomes if x["outcome"] == "STILL_CENSORED"]

    result = {
        "schema": "COLLATZ_ZERO_SWITCH_CONTINUATION_V74",
        "parent_v60_certificate_sha256": PARENT_V60_CERT,
        "parent_v72_qualification_sha256": PARENT_V72_QUAL,
        "parent_v73_qualification_sha256": PARENT_V73_QUAL,
        "extended_cap": EXTENDED_CAP,
        "terminal_zero_targets": len(targets),
        "outcome_counts": dict(sorted(counts.items())),
        "next_zero_switches": len(next_zero),
        "next_nonzero_switches": len(next_nonzero),
        "streak_resets_to_residual": len(reset),
        "still_censored": len(censored),
        "pair_candidate_status": (
            "REJECTED" if next_zero else
            "SURVIVES_WHERE_COORDINATE_CONTINUES"
        ),
        "sample_next_zero": next_zero[:10],
        "sample_next_nonzero": next_nonzero[:10],
        "sample_resets": reset[:10],
        "sample_censored": censored[:10],
        "interpretation": (
            "This is the prospective continuation of exactly the 44 V73 cases "
            "for which the frozen V60 pulled-centre streak ended immediately after "
            "a zero-only switch. A same-streak next zero directly falsifies the V72 "
            "pair law. A streak reset instead localizes the missing theorem to lawful "
            "transport of source precision across representation re-anchoring."
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
