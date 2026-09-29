#!/usr/bin/env python3
"""V40: forced 2 mod 9 section as a source-relative Collatz closeout seam.

This gate has two roles.

1. Re-express the exact public strongly-sufficient section y == 2 (mod 9)
   in the source-relative language already used by Crystal.  The canonical
   odd predecessor is p=(2y-1)/3.  Thus a section hit is an immediate lower
   source merge exactly when 2y < 3n+1.

2. Falsify the cheapest remaining scalar rank on the frozen V23/V36/V26
   exact natural controls: after SourceProduct.tail=0, do successive
   pre-exit section predecessors p>=n strictly decrease?

The Lean theorem in formal/Collatz/Mod9Section.lean proves the exact bridge
"low 2 mod 9 hit -> Exit" and the conditional global closeout.  This Python
gate does not assume or re-prove the public theorem that every positive orbit
hits 2 mod 9, and survival on the frozen controls is never promoted to a
universal theorem.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_zero_tail_k_rank_v39 as v39
    import collatz_crystal_parameter_quotient_v25 as v25

T = v39.T


def section_pred(y: int) -> int:
    assert y % 9 == 2
    p = (2 * y - 1) // 3
    assert p > 0 and p % 2 == 1
    assert T(p) == y
    return p


def audit_source(name: str, n: int, cap: int):
    y = n
    zero_depth = n.bit_length()
    rows = []
    first_simple_exit = None

    for depth in range(cap + 1):
        if y % 9 == 2:
            p = section_pred(y)
            low = p < n
            # Exact equivalence for this section.
            assert low == (2 * y < 3 * n + 1)
            rows.append({
                "depth": depth,
                "endpoint": str(y),
                "pred": str(p),
                "pred_minus_source": str(p - n),
                "post_zero_tail": depth >= zero_depth,
                "pred_ge_source": p >= n,
                "low_section_exit": low,
                "height_barrier_gap": str(2 * y - (3 * n + 1)),
            })

        ex = v39.simple_exit(n, y, depth)
        if ex is not None:
            first_simple_exit = ex
            break

        if depth < cap:
            y = T(y)

    live = [
        r for r in rows
        if r["post_zero_tail"] and r["pred_ge_source"]
        and (first_simple_exit is None or r["depth"] <= first_simple_exit["depth"])
    ]
    inc, eq, dec = [], [], []
    for a, b in zip(live, live[1:]):
        pa, pb = int(a["pred"]), int(b["pred"])
        item = {
            "from_depth": a["depth"],
            "to_depth": b["depth"],
            "from_pred": a["pred"],
            "to_pred": b["pred"],
            "delta": str(pb - pa),
        }
        if pb > pa:
            inc.append(item)
        elif pb == pa:
            eq.append(item)
        else:
            dec.append(item)

    low_hits = [r for r in rows if r["low_section_exit"]]
    return {
        "name": name,
        "source": str(n),
        "source_bits": zero_depth,
        "cap": cap,
        "first_simple_exit": first_simple_exit,
        "section_hits_before_exit": len(rows),
        "post_zero_tail_section_pred_ge_source": len(live),
        "post_zero_tail_section_pred_transitions": {
            "decrease": len(dec),
            "equal": len(eq),
            "increase": len(inc),
        },
        "first_increases": inc[:20],
        "first_equals": eq[:20],
        "first_low_section_hit": low_hits[0] if low_hits else None,
        "section_rows": rows[:200],
    }


sources = [
    ("V23_MIN", v25.N0, 800),
    ("V36_SOURCE", v25.N0 + v25.NC * 1_018_706, 800),
    ("V26_HARD", v39.source_v26(), 900),
]
rows = [audit_source(*x) for x in sources]

increases = sum(
    r["post_zero_tail_section_pred_transitions"]["increase"] for r in rows
)
equals = sum(
    r["post_zero_tail_section_pred_transitions"]["equal"] for r in rows
)

result = {
    "schema": "COLLATZ_CRYSTAL_MOD9_SECTION_V40",
    "parent": "collatz-crystal-zero-tail-k-rank-v39@ca6723d8db2263217733ff7c8d6f85b7b2735520",
    "exact_bridge": {
        "section": "y == 2 (mod 9)",
        "canonical_predecessor": "p=(2y-1)/3",
        "one_step_identity": "T(p)=y",
        "source_exit_equivalence": "p<n iff 2y<3n+1",
        "lean_file": "formal/Collatz/Mod9Section.lean",
        "conditional_closeout": (
            "if every positive n has a 2 mod 9 hit y with 2y<3n+1, "
            "then positive Collatz follows"
        ),
    },
    "frozen_sources": rows,
    "candidate": (
        "after SourceProduct.tail=0, successive pre-exit 2 mod 9 "
        "section predecessors p>=source strictly decrease"
    ),
    "verdict": (
        "POST_ZERO_TAIL_MOD9_SECTION_PRED_RANK_REJECTED"
        if increases or equals else
        "NO_COUNTEREXAMPLE_ON_FROZEN_EXACT_SOURCES"
    ),
    "next_if_rejected": (
        "lift the section return to the already-earned product state "
        "DYADIC_SOURCE_GUARD x TRAJECTORY_HEADROOM x intrinsic Q2xQ3 future cell; "
        "compile protected first-return SCCs and feed an eventual macro-rank "
        "certificate into collatz_of_zero_tail_eventual_rank"
    ),
    "claim_boundary": (
        "Exact replay on three frozen adversarial/source-anchor naturals only. "
        "The public theorem that every positive orbit hits 2 mod 9 is external "
        "literature context, not authority for this run. Survival is discovery "
        "evidence only."
    ),
    "global_collatz": "UNKNOWN",
}
result["certificate_sha256"] = hashlib.sha256(
    json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
print(json.dumps(result, indent=2, sort_keys=True))
