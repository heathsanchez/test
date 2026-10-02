#!/usr/bin/env python3
"""V77: localize the minimum admission separator for V76's exact law-only witness.

V76 showed that if we retain only same-anchor affine law identity, the exact
witness L0->L1->L2->L3 admits two consecutive zero source-precision intervals.
V75 had no zero-zero path in the frozen source-free observed transition grammar.

This audit asks the smallest remaining question against the frozen V53 authority:
  1. Does each of the three witness law edges actually occur?
  2. If so, do they occur on one source/t lineage?
  3. If so, do the exact keys/row adjacencies compose?

The first failed condition is the minimum admission distinction forced by the
V76 separator. This is a bounded grammar result, not a Collatz proof.
"""
from __future__ import annotations

from collections import Counter, defaultdict
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
    import collatz_crystal_nonpositive_budget_kernel_v53 as v53

PARENT_V76_QUAL = "236b6feca88c68b81d2cacbccaff851449cb55f16c1c81c47b80933b9326f0db"
ANCHOR = 1
LAWS = [
    (2187, 1785, 2048, 11),
    (2187, 1417, 1024, 10),
    (81, 43, 64, 6),
    (729, 857, 512, 9),
]


def law(row):
    return (int(row["A"]), int(row["B"]), int(row["P"]), int(row["D"]))


def lineage(tr):
    return (int(tr["source"]), int(tr["t"]), int(tr["anchor"]))


def row_id(row):
    return (
        int(row["source"]), int(row["t"]), int(row["anchor"]),
        int(row["k0"]), int(row["k1"]), repr(row["key"]), law(row)
    )


def edge_record(tr):
    return {
        "source": str(tr["source"]),
        "t": str(tr["t"]),
        "anchor": int(tr["anchor"]),
        "src_depth": [int(tr["src"]["k0"]), int(tr["src"]["k1"])],
        "dst_depth": [int(tr["dst"]["k0"]), int(tr["dst"]["k1"])],
        "src_key": repr(tr["src"]["key"]),
        "dst_key": repr(tr["dst"]["key"]),
        "src_law": list(law(tr["src"])),
        "dst_law": list(law(tr["dst"])),
    }


residual = [
    tr for tr in v53.transitions
    if tr["anchor"] == ANCHOR
    and tr["kind"] == "RESIDUAL"
    and tr["dst"] is not None
    and tr["src"]["residual"]
    and tr["dst"]["residual"]
]

edge_specs = list(zip(LAWS, LAWS[1:]))
edge_rows = []
edge_lineages = []
successors = {}

for i, (a, b) in enumerate(edge_specs):
    matches = [tr for tr in residual if law(tr["src"]) == a and law(tr["dst"]) == b]
    edge_rows.append(matches)
    edge_lineages.append({lineage(tr) for tr in matches})

    succ = Counter(
        law(tr["dst"])
        for tr in residual
        if law(tr["src"]) == a
    )
    successors[str(i)] = {
        "src_law": list(a),
        "expected_dst_law": list(b),
        "src_transition_rows": sum(succ.values()),
        "distinct_successor_laws": len(succ),
        "expected_edge_rows": len(matches),
        "top_actual_successors": [
            {"law": list(L), "rows": n}
            for L, n in succ.most_common(20)
        ],
    }

# Build actual same-lineage ordered transition chains.
by_lineage = defaultdict(list)
for tr in residual:
    by_lineage[lineage(tr)].append(tr)
for xs in by_lineage.values():
    xs.sort(key=lambda tr: (
        tr["src"]["k0"], tr["src"]["k1"],
        tr["dst"]["k0"], tr["dst"]["k1"]
    ))

chains = []
for lin, xs in by_lineage.items():
    for i in range(len(xs) - 2):
        a, b, c = xs[i:i+3]
        if not (
            law(a["src"]) == LAWS[0] and law(a["dst"]) == LAWS[1]
            and law(b["src"]) == LAWS[1] and law(b["dst"]) == LAWS[2]
            and law(c["src"]) == LAWS[2] and law(c["dst"]) == LAWS[3]
        ):
            continue
        # Demand literal row composition, not merely three law edges on one source.
        if row_id(a["dst"]) != row_id(b["src"]):
            continue
        if row_id(b["dst"]) != row_id(c["src"]):
            continue
        chains.append({
            "lineage": [str(lin[0]), str(lin[1]), int(lin[2])],
            "edges": [edge_record(a), edge_record(b), edge_record(c)],
        })

pair_counts = [len(xs) for xs in edge_rows]
missing = [i for i, n in enumerate(pair_counts) if n == 0]
common_lineages = set.intersection(*edge_lineages) if all(edge_lineages) else set()

if missing:
    separator = "OBSERVED_EDGE_ADMISSION"
    first_failed_edge = missing[0]
elif not common_lineages:
    separator = "SOURCE_LINEAGE_COHERENCE"
    first_failed_edge = None
elif not chains:
    separator = "KEY_OR_TEMPORAL_ADJACENCY_COHERENCE"
    first_failed_edge = None
else:
    separator = "WITNESS_REALIZED_IN_FROZEN_V53"
    first_failed_edge = None

result = {
    "schema": "COLLATZ_V76_ADMISSION_SEPARATOR_V77",
    "parent_v76_qualification_sha256": PARENT_V76_QUAL,
    "anchor": ANCHOR,
    "witness_laws": [list(L) for L in LAWS],
    "frozen_v53_transition_rows": len(v53.transitions),
    "anchor_residual_transition_rows": len(residual),
    "witness_edge_row_counts": pair_counts,
    "witness_edge_unique_lineage_counts": [len(s) for s in edge_lineages],
    "witness_edge_samples": [
        [edge_record(tr) for tr in xs[:12]]
        for xs in edge_rows
    ],
    "successor_audit": successors,
    "common_source_t_anchor_lineages_across_all_three_edges": len(common_lineages),
    "common_lineage_samples": [
        [str(x[0]), str(x[1]), int(x[2])]
        for x in sorted(common_lineages)[:20]
    ],
    "exact_composed_three_edge_paths": len(chains),
    "exact_chain_samples": chains[:8],
    "minimum_admission_separator": separator,
    "first_failed_edge_index": first_failed_edge,
    "interpretation": (
        "The V76 law-only witness is intersected with the actual frozen V53 "
        "transition authority. The first failed condition determines whether "
        "law identity must be refined by observed edge admissibility, by "
        "same-source lineage coherence, or by finer key/temporal adjacency."
    ),
    "global_collatz": "UNKNOWN",
    "qed": False,
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
