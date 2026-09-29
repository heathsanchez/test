#!/usr/bin/env python3
"""Crystal V42: normalized V23-parameter quotient for same-anchor futures.

V41 falsified the frozen V40 bank and exposed the first missing source
coordinate in the normalized V23 parameter
    n(t) = N0 + NC*t.
The first protected successor collision agrees on the frozen raw source key
but separates at t mod 4.

This gate does exactly one thing:
  * reconstruct exact post-zero-tail same-anchor return consequences on the
    full V41 training challenge plus the inherited V36/V26 controls;
  * find the smallest (a,b) such that
        (current exact return signature, t mod 2^a, t mod 3^b)
    is functional for the next same-anchor consequence;
  * freeze that pair before a disjoint held-out suffix-motif challenge;
  * fail closed on any held-out collision or censored terminal claim.

The exact return signature is source-independent:
  (anchor, A, B, D, rho, v3(defect), m mod 3^v3(defect)).
No frozen V40 law bank or raw n-residue is used in the candidate key.

Bounded functionality is not QED. The result is a separator/representation
gate for the all-depth theorem required by V37 hprogress.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
import hashlib
import io
import json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_parameter_quotient_v25 as v25
    import collatz_crystal_phase_normalized_return_v40 as v40

BASE_DEPTH = 9
SUFFIX_BITS = 18
CAP = 700
MOD3 = 3**4
MAX_A = BASE_DEPTH + SUFFIX_BITS
MAX_B = 4

TRAIN_MOTIFS = {
    "ZERO": "0",
    "ONES": "1",
    "110": "110",
    "101": "101",
    "011": "011",
    "ALT01": "01",
}
HOLDOUT_MOTIFS = {
    "001": "001",
    "010": "010",
    "100": "100",
    "ALT0011": "0011",
    "RUN000111": "000111",
    "THUE8": "01101001",
}


def live_frontier(depth: int):
    frontier = [0]
    for d in range(depth + 1):
        survivors = []
        nxt = []
        for r in frontier:
            z = v25.classify_cell(d, r, with_merge=True)
            if not z["terminal"]:
                survivors.append(r)
                if d < depth:
                    nxt.extend((r, r + (1 << d)))
        if d == depth:
            return survivors
        frontier = nxt
    raise AssertionError


LIVE = live_frontier(BASE_DEPTH)
assert len(LIVE) == 64, len(LIVE)

M2 = 1 << (BASE_DEPTH + SUFFIX_BITS)
INV2 = pow(M2, -1, MOD3)


def pattern_bits(pattern: str) -> int:
    assert pattern and set(pattern) <= {"0", "1"}
    x = 0
    for i in range(SUFFIX_BITS):
        x |= int(pattern[i % len(pattern)]) << i
    return x


def crt_parameter(r: int, a: int, pattern: str) -> int:
    suffix = pattern_bits(pattern)
    t2 = r + (suffix << BASE_DEPTH)
    assert t2 % (1 << BASE_DEPTH) == r
    k = ((a - t2) * INV2) % MOD3
    t = t2 + M2 * k
    assert t % M2 == t2
    assert t % MOD3 == a
    return t


def v3z(x: int):
    x = abs(x)
    if x == 0:
        return None
    v = 0
    while x % 3 == 0:
        x //= 3
        v += 1
    return v


def law_key(e):
    c = e["cert"]
    return (e["anchor"], c["A"], c["B"], c["D"], c["rho"])


def return_signature(e):
    """Bank-independent exact local return signature."""
    rad = v3z(e["defect"])
    if rad is None:
        q3 = (None, None)
    else:
        q3 = (rad, e["m0"] % (3**rad) if rad else 0)
    return law_key(e) + q3


def successor_label(e):
    """Exact next-return consequence; richer than the candidate key."""
    return ("RETURN",) + return_signature(e)


def source_t(n: int) -> int:
    assert n >= v25.N0
    d = n - v25.N0
    assert d % v25.NC == 0
    return d // v25.NC


def collect_run_rows(name: str, t: int, n: int, cap: int = CAP):
    rr = v40.actual_episode_returns(name, n, cap)
    rows = []
    stats = Counter()
    if rr["note"] == "ordinary exit before zero-tail":
        stats["EXIT_PRE_ZERO"] += 1
        return rows, stats, rr

    stats["POST_ZERO_SOURCE"] += 1
    if rr["first_exit"] is None:
        stats["SOURCE_CENSORED"] += 1
    else:
        stats["EXIT_" + rr["first_exit"]["kind"]] += 1

    by = defaultdict(list)
    for e in rr["events"]:
        if e["zero_defect"]:
            stats["ZERO_DEFECT_EVENT"] += 1
        by[e["anchor"]].append(e)

    for anchor, es in by.items():
        es.sort(key=lambda z: (z["k0"], z["k1"]))
        for i, e in enumerate(es):
            if i + 1 < len(es):
                lab = successor_label(es[i + 1])
            else:
                if rr["first_exit"] is None:
                    stats["CENSORED_LAST_EVENT"] += 1
                    continue
                lab = ("EXIT", rr["first_exit"]["kind"])
            rows.append({
                "source_name": name,
                "t": t,
                "source": n,
                "anchor": anchor,
                "k0": e["k0"],
                "k1": e["k1"],
                "sig": return_signature(e),
                "label": lab,
            })
            stats["ROWS"] += 1
    return rows, stats, rr


def build_corpus(motifs, tag):
    rows = []
    stats = Counter()
    sources = 0
    first_censored = None
    first_zero = None
    for r in LIVE:
        for a in range(MOD3):
            for mname, pattern in motifs.items():
                t = crt_parameter(r, a, pattern)
                n = v25.N0 + v25.NC * t
                name = f"{tag}-r{r}-a{a}-{mname}"
                rr_rows, rr_stats, rr = collect_run_rows(name, t, n)
                sources += 1
                rows.extend(rr_rows)
                stats.update(rr_stats)
                if rr_stats["SOURCE_CENSORED"] and first_censored is None:
                    first_censored = {
                        "r": r, "a": a, "motif": mname,
                        "t": str(t), "source": str(n),
                    }
                if rr_stats["ZERO_DEFECT_EVENT"] and first_zero is None:
                    z = next(e for e in rr["events"] if e["zero_defect"])
                    first_zero = {
                        "r": r, "a": a, "motif": mname,
                        "t": str(t), "source": str(n),
                        "anchor": z["anchor"], "k0": z["k0"], "k1": z["k1"],
                        "law": repr(law_key(z)),
                    }
    return {
        "rows": rows,
        "stats": stats,
        "sources": sources,
        "first_censored": first_censored,
        "first_zero": first_zero,
    }


def residue_key(row, a: int, b: int):
    t = row["t"]
    return (
        row["sig"],
        t % (1 << a) if a else 0,
        t % (3**b) if b else 0,
    )


def functionality(rows, a: int, b: int):
    outs = defaultdict(set)
    first_rows = {}
    for row in rows:
        k = residue_key(row, a, b)
        outs[k].add(row["label"])
        first_rows.setdefault((k, row["label"]), row)
    bad = [(k, vs) for k, vs in outs.items() if len(vs) > 1]
    bad.sort(key=lambda kv: (repr(kv[0]), repr(sorted(kv[1], key=repr))))
    first = None
    if bad:
        k, vs = bad[0]
        labs = sorted(vs, key=repr)
        witnesses = []
        for lab in labs[:3]:
            row = first_rows[(k, lab)]
            witnesses.append({
                "source_name": row["source_name"],
                "t": str(row["t"]),
                "source": str(row["source"]),
                "anchor": row["anchor"],
                "depth": [row["k0"], row["k1"]],
                "label": repr(row["label"]),
            })
        first = {
            "key": repr(k),
            "labels": [repr(x) for x in labs[:8]],
            "witnesses": witnesses,
        }
    return {
        "keys": len(outs),
        "collision_keys": len(bad),
        "first_collision": first,
    }


def select_minimal(rows):
    tested = []
    winners = []
    for a in range(MAX_A + 1):
        for b in range(MAX_B + 1):
            z = functionality(rows, a, b)
            tested.append((a, b, z["collision_keys"]))
            if z["collision_keys"] == 0:
                winners.append((a + b, a, b, z["keys"]))
    winners.sort()
    if not winners:
        best = sorted(tested, key=lambda x: (x[2], x[0] + x[1], x[0], x[1]))[0]
        return None, {
            "best_a": best[0], "best_b": best[1],
            "best_collision_keys": best[2],
        }, tested
    _, a, b, keys = winners[0]
    return (a, b), {"functional_keys": keys}, tested


def transport_stats(train_rows, hold_rows, a: int, b: int):
    train_map = defaultdict(set)
    for row in train_rows:
        train_map[residue_key(row, a, b)].add(row["label"])
    assert all(len(v) == 1 for v in train_map.values())

    seen = matched = contradicted = unseen = 0
    first_contradiction = None
    for row in hold_rows:
        k = residue_key(row, a, b)
        if k not in train_map:
            unseen += 1
            continue
        seen += 1
        expected = next(iter(train_map[k]))
        if row["label"] == expected:
            matched += 1
        else:
            contradicted += 1
            if first_contradiction is None:
                first_contradiction = {
                    "key": repr(k),
                    "expected": repr(expected),
                    "observed": repr(row["label"]),
                    "source_name": row["source_name"],
                    "t": str(row["t"]),
                    "source": str(row["source"]),
                    "anchor": row["anchor"],
                    "depth": [row["k0"], row["k1"]],
                }
    combined = functionality(train_rows + hold_rows, a, b)
    return {
        "holdout_rows": len(hold_rows),
        "seen_keys_rows": seen,
        "matched_seen_rows": matched,
        "contradicted_seen_rows": contradicted,
        "unseen_rows": unseen,
        "combined_collision_keys": combined["collision_keys"],
        "first_contradiction": first_contradiction,
        "first_combined_collision": combined["first_collision"],
    }


train = build_corpus(TRAIN_MOTIFS, "train")

# Inherited exact controls. These are prior authority, not held-out data.
control_stats = Counter()
for rr in v40.runs:
    if rr["name"] == "V23_MIN":
        continue
    t = source_t(rr["source"])
    rows, st, _ = collect_run_rows("control-" + rr["name"], t, rr["source"])
    train["rows"].extend(rows)
    control_stats.update(st)

selected, selection_meta, search_table = select_minimal(train["rows"])

hold = build_corpus(HOLDOUT_MOTIFS, "holdout")

if selected is None:
    verdict = "NORMALIZED_PARAMETER_QUOTIENT_NOT_FUNCTIONAL_ON_TRAINING"
    hold_transport = None
    postmortem = None
else:
    sa, sb = selected
    hold_transport = transport_stats(train["rows"], hold["rows"], sa, sb)
    if train["stats"]["SOURCE_CENSORED"] or control_stats["SOURCE_CENSORED"]:
        verdict = "TRAINING_CENSORED_NO_PROMOTION"
    elif hold["stats"]["SOURCE_CENSORED"]:
        verdict = "HOLDOUT_CENSORED_NO_PROMOTION"
    elif train["stats"]["ZERO_DEFECT_EVENT"] or hold["stats"]["ZERO_DEFECT_EVENT"]:
        verdict = "ZERO_DEFECT_OBSTRUCTION_EMITTED"
    elif hold_transport["combined_collision_keys"]:
        verdict = "FROZEN_PARAMETER_QUOTIENT_REJECTED_ON_HOLDOUT"
    else:
        verdict = "BOUNDED_NORMALIZED_PARAMETER_QUOTIENT_SURVIVES_HOLDOUT"

    # Diagnostic only: if the frozen pair fails, show the minimum pair on the
    # combined corpus. This does not retroactively promote a retuned quotient.
    if hold_transport["combined_collision_keys"]:
        post_sel, post_meta, _ = select_minimal(train["rows"] + hold["rows"])
        postmortem = {
            "combined_minimal_pair": list(post_sel) if post_sel else None,
            "meta": post_meta,
        }
    else:
        postmortem = None

# Compact collision frontier: for every a, minimum collisions across b and vice versa.
by_a = {}
for a in range(MAX_A + 1):
    vals = [(coll, b) for aa, b, coll in search_table if aa == a]
    coll, b = min(vals)
    by_a[str(a)] = {"min_collision_keys": coll, "best_b": b}
by_b = {}
for b in range(MAX_B + 1):
    vals = [(coll, a) for a, bb, coll in search_table if bb == b]
    coll, a = min(vals)
    by_b[str(b)] = {"min_collision_keys": coll, "best_a": a}

result = {
    "schema": "COLLATZ_CRYSTAL_NORMALIZED_PARAMETER_QUOTIENT_V42",
    "parent": "collatz-crystal-v40-bank-challenge-v41@2283822c221f17cce47c954c203036c5138a0ae2",
    "training": {
        "motifs": list(TRAIN_MOTIFS),
        "exact_challenge_sources": train["sources"],
        "rows": len(train["rows"]),
        "stats": dict(sorted(train["stats"].items())),
        "control_stats": dict(sorted(control_stats.items())),
        "first_censored": train["first_censored"],
        "first_zero_defect": train["first_zero"],
    },
    "candidate_space": {
        "a_range": [0, MAX_A],
        "b_range": [0, MAX_B],
        "selection_order": "minimize a+b, then a, then b",
        "base_signature": "(anchor,A,B,D,rho,v3(defect),m mod 3^v3(defect))",
        "source_coordinates": "(t mod 2^a, t mod 3^b)",
    },
    "selected_pair": list(selected) if selected else None,
    "selection_meta": selection_meta,
    "training_collision_frontier_by_a": by_a,
    "training_collision_frontier_by_b": by_b,
    "holdout": {
        "motifs": list(HOLDOUT_MOTIFS),
        "exact_sources": hold["sources"],
        "rows": len(hold["rows"]),
        "stats": dict(sorted(hold["stats"].items())),
        "first_censored": hold["first_censored"],
        "first_zero_defect": hold["first_zero"],
        "transport": hold_transport,
    },
    "postmortem_retune_diagnostic": postmortem,
    "verdict": verdict,
    "interpretation": (
        "V42 tests the V41-earned normalized V23 parameter coordinate directly. "
        "The quotient is frozen on the V41 motif family before a disjoint motif "
        "challenge. Unseen held-out keys remain UNKNOWN; any contradictory "
        "seen key or combined collision rejects the frozen pair."
    ),
    "promotion_boundary": (
        "Even a clean held-out result is bounded representation evidence only. "
        "QED still requires a symbolic/all-depth right-congruence and progress "
        "theorem for the normalized parameter quotient, then V37 hprogress."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()

print(json.dumps(result, indent=2, sort_keys=True))
