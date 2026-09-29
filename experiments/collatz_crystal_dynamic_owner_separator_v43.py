#!/usr/bin/env python3
"""Crystal V43: dynamic owner/carry separator after V42.

V42 showed that no static normalized-source residue pair
  (t mod 2^a, t mod 3^b), a<=27, b<=4
makes the exact same-anchor successor consequence functional. Collision count
plateaus even when the V41 challenge source t is identified exactly.

This gate isolates the missing dynamic coordinate. It keeps exact t (so no
source alias remains), then searches the smallest current-owner refinement:
  * c extra Q2 bits beyond the return law's forced D+1 cylinder bits;
  * d absolute current-owner Q3 trits.

The candidate state is
  (exact return signature, exact normalized source t, extra2_c, owner mod 3^d).
The pair (c,d) is frozen on the V41 training motifs, then challenged on the
same disjoint held-out motifs used by V42.

Diagnostics also test exact current owner, post-zero phase, occurrence index,
and one-step previous-law history. These are not promoted automatically; they
identify the next missing coordinate if bounded owner residues fail.

Bounded functionality is discovery evidence only, not Collatz QED.
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
MAX_C = 64
MAX_D = 6

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
    for k in range(depth + 1):
        survivors = []
        nxt = []
        for r in frontier:
            z = v25.classify_cell(k, r, with_merge=True)
            if not z["terminal"]:
                survivors.append(r)
                if k < depth:
                    nxt.extend((r, r + (1 << k)))
        if k == depth:
            return survivors
        frontier = nxt
    raise AssertionError


LIVE = live_frontier(BASE_DEPTH)
assert len(LIVE) == 64
M2 = 1 << (BASE_DEPTH + SUFFIX_BITS)
INV2 = pow(M2, -1, MOD3)


def pattern_bits(pattern: str) -> int:
    x = 0
    for i in range(SUFFIX_BITS):
        x |= int(pattern[i % len(pattern)]) << i
    return x


def crt_parameter(r: int, a: int, pattern: str) -> int:
    t2 = r + (pattern_bits(pattern) << BASE_DEPTH)
    k = ((a - t2) * INV2) % MOD3
    t = t2 + M2 * k
    assert t % (1 << BASE_DEPTH) == r
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
    rad = v3z(e["defect"])
    if rad is None:
        q3 = (None, None)
    else:
        q3 = (rad, e["m0"] % (3**rad) if rad else 0)
    return law_key(e) + q3


def successor_label(e):
    return ("RETURN",) + return_signature(e)


def source_t(n: int) -> int:
    d = n - v25.N0
    assert d >= 0 and d % v25.NC == 0
    return d // v25.NC


def collect_run_rows(name: str, t: int, n: int):
    rr = v40.actual_episode_returns(name, n, CAP)
    rows = []
    stats = Counter()

    if rr["note"] == "ordinary exit before zero-tail":
        stats["EXIT_PRE_ZERO"] += 1
        return rows, stats

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
                label = successor_label(es[i + 1])
            elif rr["first_exit"] is not None:
                label = ("EXIT", rr["first_exit"]["kind"])
            else:
                stats["CENSORED_LAST_EVENT"] += 1
                continue

            sig = return_signature(e)
            prev = ("START",) if i == 0 else return_signature(es[i - 1])
            rows.append({
                "source_name": name,
                "t": t,
                "source": n,
                "sig": sig,
                "label": label,
                "m0": e["m0"],
                "forced_bits": e["cert"]["D"] + 1,
                "k0": e["k0"],
                "k1": e["k1"],
                "zero_depth": rr["zero_depth"],
                "phase": e["k0"] - rr["zero_depth"],
                "occurrence": i,
                "prev_sig": prev,
            })
            stats["ROWS"] += 1
    return rows, stats


def build_corpus(motifs, tag):
    rows = []
    stats = Counter()
    sources = 0
    for r in LIVE:
        for a in range(MOD3):
            for mname, pattern in motifs.items():
                t = crt_parameter(r, a, pattern)
                n = v25.N0 + v25.NC * t
                rr_rows, rr_stats = collect_run_rows(
                    f"{tag}-r{r}-a{a}-{mname}", t, n
                )
                rows.extend(rr_rows)
                stats.update(rr_stats)
                sources += 1
    return rows, stats, sources


def dynamic_key(row, c: int, d: int):
    extra2 = 0
    if c:
        extra2 = (row["m0"] >> row["forced_bits"]) & ((1 << c) - 1)
    extra3 = row["m0"] % (3**d) if d else 0
    return (row["sig"], row["t"], extra2, extra3)


def alt_key(row, mode: str):
    if mode == "EXACT_OWNER":
        return (row["sig"], row["t"], row["m0"])
    if mode == "PHASE":
        return (row["sig"], row["t"], row["phase"])
    if mode == "OCCURRENCE":
        return (row["sig"], row["t"], row["occurrence"])
    if mode == "PREV_SIG":
        return (row["sig"], row["t"], row["prev_sig"])
    if mode == "PHASE_PREV":
        return (row["sig"], row["t"], row["phase"], row["prev_sig"])
    raise KeyError(mode)


def functional(rows, keyfn):
    outs = defaultdict(set)
    first = {}
    for row in rows:
        k = keyfn(row)
        outs[k].add(row["label"])
        first.setdefault((k, row["label"]), row)
    bad = [(k, v) for k, v in outs.items() if len(v) > 1]
    bad.sort(key=lambda kv: repr(kv[0]))
    witness = None
    if bad:
        k, labels = bad[0]
        ls = sorted(labels, key=repr)
        ws = []
        for label in ls[:4]:
            row = first[(k, label)]
            ws.append({
                "source_name": row["source_name"],
                "t": str(row["t"]),
                "source": str(row["source"]),
                "m0": str(row["m0"]),
                "forced_bits": row["forced_bits"],
                "phase": row["phase"],
                "occurrence": row["occurrence"],
                "depth": [row["k0"], row["k1"]],
                "prev_sig": repr(row["prev_sig"]),
                "label": repr(label),
            })
        witness = {
            "key": repr(k),
            "labels": [repr(x) for x in ls[:8]],
            "witnesses": ws,
        }
    return {
        "keys": len(outs),
        "collision_keys": len(bad),
        "first_collision": witness,
    }


def search_dynamic(rows):
    results = []
    winners = []
    for c in range(MAX_C + 1):
        for d in range(MAX_D + 1):
            z = functional(rows, lambda row, c=c, d=d: dynamic_key(row, c, d))
            results.append((c, d, z["collision_keys"]))
            if z["collision_keys"] == 0:
                winners.append((c + d, c, d, z["keys"]))
    winners.sort()
    if winners:
        _, c, d, keys = winners[0]
        return (c, d), {"functional_keys": keys}, results
    best = min(results, key=lambda z: (z[2], z[0] + z[1], z[0], z[1]))
    return None, {
        "best_c": best[0],
        "best_d": best[1],
        "best_collision_keys": best[2],
    }, results


def transport(train, hold, c: int, d: int):
    train_map = defaultdict(set)
    for row in train:
        train_map[dynamic_key(row, c, d)].add(row["label"])
    assert all(len(x) == 1 for x in train_map.values())

    seen = match = conflict = unseen = 0
    first_conflict = None
    for row in hold:
        k = dynamic_key(row, c, d)
        if k not in train_map:
            unseen += 1
            continue
        seen += 1
        expected = next(iter(train_map[k]))
        if expected == row["label"]:
            match += 1
        else:
            conflict += 1
            if first_conflict is None:
                first_conflict = {
                    "key": repr(k),
                    "expected": repr(expected),
                    "observed": repr(row["label"]),
                    "source_name": row["source_name"],
                    "t": str(row["t"]),
                    "source": str(row["source"]),
                    "m0": str(row["m0"]),
                    "depth": [row["k0"], row["k1"]],
                }

    combined = functional(
        train + hold,
        lambda row: dynamic_key(row, c, d),
    )
    return {
        "holdout_rows": len(hold),
        "seen_rows": seen,
        "matched_seen_rows": match,
        "conflicted_seen_rows": conflict,
        "unseen_rows": unseen,
        "combined_collision_keys": combined["collision_keys"],
        "first_conflict": first_conflict,
        "first_combined_collision": combined["first_collision"],
    }


train_rows, train_stats, train_sources = build_corpus(TRAIN_MOTIFS, "train")

control_stats = Counter()
for rr in v40.runs:
    if rr["name"] == "V23_MIN":
        continue
    rows, st = collect_run_rows(
        "control-" + rr["name"], source_t(rr["source"]), rr["source"]
    )
    train_rows.extend(rows)
    control_stats.update(st)

baseline = functional(train_rows, lambda row: (row["sig"], row["t"]))
selected, selection_meta, grid = search_dynamic(train_rows)

diagnostics = {}
for mode in ("EXACT_OWNER", "PHASE", "OCCURRENCE", "PREV_SIG", "PHASE_PREV"):
    diagnostics[mode] = functional(train_rows, lambda row, mode=mode: alt_key(row, mode))

hold_rows, hold_stats, hold_sources = build_corpus(HOLDOUT_MOTIFS, "holdout")

if selected is None:
    verdict = "BOUNDED_OWNER_RESIDUES_NOT_FUNCTIONAL"
    hold_transport = None
    postmortem = None
else:
    c, d = selected
    hold_transport = transport(train_rows, hold_rows, c, d)
    if train_stats["SOURCE_CENSORED"] or control_stats["SOURCE_CENSORED"]:
        verdict = "TRAINING_CENSORED_NO_PROMOTION"
    elif hold_stats["SOURCE_CENSORED"]:
        verdict = "HOLDOUT_CENSORED_NO_PROMOTION"
    elif train_stats["ZERO_DEFECT_EVENT"] or hold_stats["ZERO_DEFECT_EVENT"]:
        verdict = "ZERO_DEFECT_OBSTRUCTION_EMITTED"
    elif hold_transport["combined_collision_keys"]:
        verdict = "FROZEN_DYNAMIC_OWNER_QUOTIENT_REJECTED_ON_HOLDOUT"
    else:
        verdict = "BOUNDED_DYNAMIC_OWNER_QUOTIENT_SURVIVES_HOLDOUT"

    if hold_transport["combined_collision_keys"]:
        post_sel, post_meta, _ = search_dynamic(train_rows + hold_rows)
        postmortem = {
            "combined_minimal_pair": list(post_sel) if post_sel else None,
            "meta": post_meta,
        }
    else:
        postmortem = None

by_c = {}
for c in range(MAX_C + 1):
    vals = [(coll, d) for cc, d, coll in grid if cc == c]
    coll, d = min(vals)
    by_c[str(c)] = {"min_collision_keys": coll, "best_d": d}

result = {
    "schema": "COLLATZ_CRYSTAL_DYNAMIC_OWNER_SEPARATOR_V43",
    "parent": "collatz-crystal-normalized-parameter-quotient-v42@c0819c838847738051cd6cd814e406db262b7fec",
    "training": {
        "motifs": list(TRAIN_MOTIFS),
        "exact_challenge_sources": train_sources,
        "rows": len(train_rows),
        "stats": dict(sorted(train_stats.items())),
        "control_stats": dict(sorted(control_stats.items())),
    },
    "baseline_exact_t": baseline,
    "candidate_space": {
        "c_range": [0, MAX_C],
        "d_range": [0, MAX_D],
        "key": "(return_signature, exact_t, next c owner bits after D+1, owner mod 3^d)",
        "selection_order": "minimize c+d, then c, then d",
    },
    "selected_pair": list(selected) if selected else None,
    "selection_meta": selection_meta,
    "collision_frontier_by_c": by_c,
    "diagnostics": diagnostics,
    "holdout": {
        "motifs": list(HOLDOUT_MOTIFS),
        "exact_sources": hold_sources,
        "rows": len(hold_rows),
        "stats": dict(sorted(hold_stats.items())),
        "transport": hold_transport,
    },
    "postmortem_retune_diagnostic": postmortem,
    "verdict": verdict,
    "interpretation": (
        "V42 proved the missing distinction is not a static source residue. "
        "V43 isolates dynamic owner/carry information beyond the current return "
        "law's forced Q2 cylinder, with exact source t held fixed."
    ),
    "promotion_boundary": (
        "A bounded dynamic separator is not an all-depth rank. A QED route still "
        "requires a symbolic right-congruence/progress law and V37 hprogress."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
