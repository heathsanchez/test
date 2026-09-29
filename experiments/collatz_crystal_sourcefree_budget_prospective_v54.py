#!/usr/bin/env python3
"""V54: prospective freeze of the V53 source-free bad-budget quotient.

V53 selected the coarsest tested source-free state with an acyclic observed
all-W<=0 graph and genuine cross-source reuse:

    (anchor, nearest frozen V45 3-adic centre, nearest radius,
     five owner bits beyond the current forced Q2 cylinder).

V54 freezes that schema, the V45 centre bank, c=5, and the V53 rank on all
already-seen abstract nodes. It then evaluates a disjoint 36-bit source family
without retuning.

Promotion criteria are fail-closed:
  * no censoring / zero-defect / missing frozen anchor;
  * every target bad->bad edge whose endpoints are both old nodes respects the
    frozen V53 rank;
  * adding every target bad->bad edge to the frozen graph creates no recurrent
    SCC.

New abstract nodes are allowed but remain UNKNOWN for universal rank; their
presence is reported explicitly. This is bounded prospective evidence only.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
from math import gcd
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_sourcefree_budget_graph_v53 as v53

v52 = v53.v52
v45 = v53.v45
v43 = v52.v43
v40 = v52.v40
v25 = v52.v25

MODE = "CENTRE_RADIUS_PORT"
C = 5
BASE_DEPTH = 9
SUFFIX_BITS = 36
MOD3 = 3**6
CAP = 1800

MOTIFS = {
    "P00010111": "00010111",
    "P11101000": "11101000",
    "P00110101": "00110101",
    "P11001010": "11001010",
    "P010001111": "010001111",
    "P101110000": "101110000",
}

assert v53.result["selected_coarsest_acyclic_reused_mode"] == MODE

def pattern_bits(pattern: str) -> int:
    return sum(int(pattern[i % len(pattern)]) << i for i in range(SUFFIX_BITS))

M2 = 1 << (BASE_DEPTH + SUFFIX_BITS)
INV2 = pow(M2, -1, MOD3)

def crt_parameter(r: int, a: int, pattern: str) -> int:
    t2 = r + (pattern_bits(pattern) << BASE_DEPTH)
    k = ((a - t2) * INV2) % MOD3
    t = t2 + M2 * k
    assert t % (1 << BASE_DEPTH) == r
    assert t % MOD3 == a
    return t

old_t = {z["t"] for z in v53.rows}

def normalize_center(A: int, B: int, D: int):
    C0 = (1 << D) - A
    assert C0 != 0
    num, den = B, C0
    if den < 0:
        num, den = -num, -den
    g = gcd(abs(num), den)
    return (num // g, den // g)

def frozen_nearest(anchor: int, m: int):
    bank = v45.centres.get(anchor)
    if bank is None:
        return None
    exact = []
    scored = []
    for centre in bank:
        cid = v45.center_id[(anchor, centre)]
        val = v45.center_distance_v3(m, centre)
        if val is None:
            exact.append(cid)
        else:
            scored.append((val, cid))
    if exact:
        ids = tuple(sorted(exact))
        return {"canonical": ids[0], "ids": ids, "radius": "INF"}
    assert scored
    best = max(v for v, _ in scored)
    ids = tuple(sorted(cid for val, cid in scored if val == best))
    return {"canonical": ids[0], "ids": ids, "radius": best}

def live_floor(anchor: int) -> int:
    return (v25.N0 + 1 + (1 << anchor) - 1) // (1 << anchor)

def budget(e) -> int:
    c = e["cert"]
    return ((1 << c["D"]) - c["A"]) * live_floor(e["anchor"]) - c["B"]

def key_from_event(e, ns):
    c = e["cert"]
    extra = (e["m0"] >> (c["D"] + 1)) & ((1 << C) - 1)
    return (e["anchor"], ns["canonical"], ns["radius"], extra)

# Rebuild frozen V53 bad graph and rank from exact parent rows.
frozen_succ = defaultdict(set)
frozen_nodes = set()
for g in v53.groups.values():
    for i, z in enumerate(g):
        if not z["bad"]:
            continue
        a = v53.state_key(z, MODE)
        frozen_nodes.add(a)
        if i + 1 < len(g) and g[i + 1]["bad"]:
            b = v53.state_key(g[i + 1], MODE)
            frozen_nodes.add(b)
            frozen_succ[a].add(b)
for x in frozen_nodes:
    frozen_succ.setdefault(x, set())
frozen_rank, frozen_residual, frozen_layers = v53.elimination_rank(
    frozen_nodes, frozen_succ
)
assert not frozen_residual
assert max(frozen_rank.values(), default=-1) == 5

fresh_rows = []
stats = Counter()
new_centres = defaultdict(set)
missing_anchor = []
zero_defects = []
censored = []
tested = 0
overlap_skipped = 0

for r in v43.LIVE:
    for a3 in range(MOD3):
        for motif, pattern in MOTIFS.items():
            t = crt_parameter(r, a3, pattern)
            if t in old_t:
                overlap_skipped += 1
                continue
            n = v25.N0 + v25.NC * t
            name = f"v54-r{r}-a{a3}-{motif}"
            rr = v40.actual_episode_returns(name, n, CAP)
            tested += 1

            if rr["note"] == "ordinary exit before zero-tail":
                stats["EXIT_PRE_ZERO"] += 1
                continue

            stats["POST_ZERO_SOURCE"] += 1
            if rr["first_exit"] is None:
                stats["SOURCE_CENSORED"] += 1
                if len(censored) < 20:
                    censored.append({
                        "source_name": name, "source": str(n), "t": str(t)
                    })

            by = defaultdict(list)
            for e in rr["events"]:
                if e["zero_defect"]:
                    stats["ZERO_DEFECT_EVENT"] += 1
                    if len(zero_defects) < 20:
                        zero_defects.append({
                            "source_name": name, "source": str(n), "t": str(t),
                            "anchor": e["anchor"], "depth": [e["k0"], e["k1"]],
                        })
                c = e["cert"]
                centre = normalize_center(c["A"], c["B"], c["D"])
                if centre not in v45.centres.get(e["anchor"], ()):
                    new_centres[e["anchor"]].add(centre)
                by[e["anchor"]].append(e)

            for anchor, es in by.items():
                es.sort(key=lambda z: (z["k0"], z["k1"]))
                for i, e in enumerate(es):
                    if i + 1 < len(es):
                        terminal = False
                    elif rr["first_exit"] is not None:
                        terminal = True
                    else:
                        stats["CENSORED_LAST_EVENT"] += 1
                        continue

                    ns = frozen_nearest(anchor, e["m0"])
                    if ns is None:
                        stats["MISSING_FROZEN_ANCHOR_ROW"] += 1
                        if len(missing_anchor) < 20:
                            missing_anchor.append({
                                "source_name": name, "source": str(n),
                                "t": str(t), "anchor": anchor,
                                "depth": [e["k0"], e["k1"]],
                            })
                        continue

                    fresh_rows.append({
                        "source_name": name,
                        "source": n,
                        "t": t,
                        "anchor": anchor,
                        "k0": e["k0"],
                        "k1": e["k1"],
                        "m0": e["m0"],
                        "m1": e["m1"],
                        "budget": budget(e),
                        "bad": budget(e) <= 0,
                        "key": key_from_event(e, ns),
                        "terminal": terminal,
                    })
                    stats["ROWS"] += 1

fresh_groups = defaultdict(list)
for z in fresh_rows:
    fresh_groups[(z["source_name"], z["anchor"])].append(z)
for g in fresh_groups.values():
    g.sort(key=lambda z: (z["k0"], z["k1"]))

target_succ = defaultdict(set)
target_nodes = set()
target_occ = Counter()
target_sources = defaultdict(set)
rank_checks = 0
rank_violations = []
old_to_new_edges = 0
new_to_old_edges = 0
new_to_new_edges = 0
positive_next = 0
terminal_after_bad = 0

for g in fresh_groups.values():
    for i, z in enumerate(g):
        if not z["bad"]:
            continue
        a = z["key"]
        target_nodes.add(a)
        target_occ[a] += 1
        target_sources[a].add(z["source"])

        if i + 1 < len(g):
            nxt = g[i + 1]
            if nxt["bad"]:
                b = nxt["key"]
                target_nodes.add(b)
                target_succ[a].add(b)
                if a in frozen_rank and b in frozen_rank:
                    rank_checks += 1
                    if not frozen_rank[b] < frozen_rank[a]:
                        if len(rank_violations) < 30:
                            rank_violations.append({
                                "source": str(z["source"]),
                                "t": str(z["t"]),
                                "from": repr(a), "to": repr(b),
                                "from_rank": frozen_rank[a],
                                "to_rank": frozen_rank[b],
                                "depth": [z["k0"], nxt["k0"]],
                                "from_budget": str(z["budget"]),
                                "to_budget": str(nxt["budget"]),
                            })
                elif a in frozen_nodes:
                    old_to_new_edges += 1
                elif b in frozen_nodes:
                    new_to_old_edges += 1
                else:
                    new_to_new_edges += 1
            else:
                positive_next += 1
        else:
            terminal_after_bad += 1

for x in target_nodes:
    target_succ.setdefault(x, set())

target_recurrent = v53.tarjan(target_nodes, target_succ)
target_rank, target_residual, target_layers = v53.elimination_rank(
    target_nodes, target_succ
)

combined_nodes = frozen_nodes | target_nodes
combined_succ = defaultdict(set)
for a, bs in frozen_succ.items():
    combined_succ[a].update(bs)
for a, bs in target_succ.items():
    combined_succ[a].update(bs)
for x in combined_nodes:
    combined_succ.setdefault(x, set())

combined_recurrent = v53.tarjan(combined_nodes, combined_succ)
combined_rank, combined_residual, combined_layers = v53.elimination_rank(
    combined_nodes, combined_succ
)

overlap_nodes = target_nodes & frozen_nodes
new_nodes = target_nodes - frozen_nodes
reused_target_nodes = {x for x in target_nodes if target_occ[x] > 1}
cross_source_target_nodes = {
    x for x in target_nodes if len(target_sources[x]) > 1
}

first_combined_scc = None
if combined_recurrent:
    cc = combined_recurrent[0]
    first_combined_scc = {
        "size": len(cc),
        "nodes": [repr(x) for x in sorted(cc, key=repr)[:30]],
    }

new_centres_count = sum(len(v) for v in new_centres.values())

if stats["SOURCE_CENSORED"] or stats["CENSORED_LAST_EVENT"]:
    verdict = "PROSPECTIVE_CENSORED_NO_PROMOTION"
elif stats["ZERO_DEFECT_EVENT"]:
    verdict = "ZERO_DEFECT_OBSTRUCTION_EMITTED"
elif stats["MISSING_FROZEN_ANCHOR_ROW"]:
    verdict = "FROZEN_CENTRE_BANK_NEW_ANCHOR_SEPARATOR"
elif rank_violations:
    verdict = "FROZEN_SOURCEFREE_RANK_REJECTED"
elif combined_recurrent:
    verdict = "SOURCEFREE_QUOTIENT_RECURRENT_SEPARATOR"
else:
    verdict = "SOURCEFREE_QUOTIENT_SURVIVES_PROSPECTIVE_CHALLENGE"

result = {
    "schema": "COLLATZ_CRYSTAL_SOURCEFREE_BUDGET_PROSPECTIVE_V54",
    "parents": {
        "V51": "collatz-crystal-affine-budget-v51@a384d326c0b8014249852d895f1afb791a5b2efc",
        "V53": "collatz-crystal-sourcefree-budget-graph-v53@4be90bc9005ee09bede896846ae4032e3b638812",
    },
    "frozen": {
        "mode": MODE,
        "port_bits": C,
        "centre_bank_size": sum(len(v) for v in v45.centres.values()),
        "frozen_bad_nodes": len(frozen_nodes),
        "frozen_bad_edges": sum(len(v) for v in frozen_succ.values()),
        "frozen_rank_layers": frozen_layers,
        "frozen_max_rank": max(frozen_rank.values(), default=None),
    },
    "challenge": {
        "live_binary_cells": len(v43.LIVE),
        "ternary_classes": MOD3,
        "suffix_bits": SUFFIX_BITS,
        "motifs": list(MOTIFS),
        "exact_sources_tested": tested,
        "overlap_skipped": overlap_skipped,
        "cap": CAP,
    },
    "stats": dict(sorted(stats.items())),
    "prospective": {
        "bad_occurrences": sum(target_occ.values()),
        "bad_nodes": len(target_nodes),
        "bad_edges": sum(len(v) for v in target_succ.values()),
        "node_overlap_with_frozen": len(overlap_nodes),
        "new_nodes": len(new_nodes),
        "reused_target_nodes": len(reused_target_nodes),
        "cross_source_target_nodes": len(cross_source_target_nodes),
        "old_old_rank_checks": rank_checks,
        "old_old_rank_violations": len(rank_violations),
        "first_rank_violations": rank_violations,
        "old_to_new_edges": old_to_new_edges,
        "new_to_old_edges": new_to_old_edges,
        "new_to_new_edges": new_to_new_edges,
        "positive_budget_next": positive_next,
        "terminal_or_exit_after_bad": terminal_after_bad,
        "target_recurrent_sccs": len(target_recurrent),
        "target_largest_scc": max((len(x) for x in target_recurrent), default=0),
        "target_residual_after_elimination": len(target_residual),
        "target_rank_layers": target_layers,
        "combined_recurrent_sccs": len(combined_recurrent),
        "combined_largest_scc": max((len(x) for x in combined_recurrent), default=0),
        "combined_residual_after_elimination": len(combined_residual),
        "combined_rank_layers": combined_layers,
        "combined_max_rank_if_acyclic": (
            max(combined_rank.values(), default=None)
            if not combined_recurrent else None
        ),
        "first_combined_scc": first_combined_scc,
    },
    "frozen_bank_growth": {
        "distinct_new_centres": new_centres_count,
        "new_centres_by_anchor": {
            str(a): len(v) for a, v in sorted(new_centres.items())
        },
        "new_anchor_ids": sorted(a for a in new_centres if a not in v45.centres),
    },
    "missing_anchor_rows": missing_anchor,
    "zero_defects": zero_defects,
    "censored_sources": censored,
    "verdict": verdict,
    "interpretation": (
        "V54 freezes the source-free V53 schema and old-node rank before a "
        "disjoint 36-bit challenge. New centre/radius/port states are retained "
        "as UNKNOWN nodes rather than mapped onto old ranks. Any recurrent SCC "
        "after union with the frozen graph is a direct quotient separator."
    ),
    "promotion_boundary": (
        "Acyclic prospective extension still does not prove an all-depth rank "
        "because the exact centre/radius state space may grow without bound. "
        "Universal closure requires a symbolic transition/rank law or the "
        "equivalent fixed-origin M>=0 anti-concentration theorem."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
