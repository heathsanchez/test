#!/usr/bin/env python3
"""
Exact theorem-strengthened Collatz residue refinement with assumption reuse.

One worker owns a lawful low-8 parent class.  It builds the H-step CNF once,
then partitions that parent into all lawful low-12 children.  Each child is
queried by SAT assumptions on the four additional seed bits, so learned
clauses are reused across sibling regions.

On the certified live domain and H < FIRST_DANGEROUS, no-descent implies
coefficient persistence.  Therefore children that fail the prefix-density
test are impossible and the lawful low-12 children exactly cover every
no-descent model of the parent.
"""
import argparse
import json
import time
from pathlib import Path

from pysat.solvers import Cadical195
from collatz_exact_cnf_even import Circuit, worst_widths, replay
from collatz_coefficient_cnf import req_odds
from collatz_prefix_residues import survives_prefix
from collatz_hybrid_adaptive import inc_if, step_conditional, LIVE_LOWER, FIRST_DANGEROUS


def lawful_children(parent_bits: int, parent_value: int, split_bits: int):
    mod = 1 << parent_bits
    assert split_bits >= parent_bits
    return [
        r for r in range(1 << split_bits)
        if r % mod == parent_value and survives_prefix(r, split_bits)
    ]


def solve_partition(A):
    K, H = A.bits, A.horizon
    assert 0 <= A.lower <= A.upper < (1 << K)
    assert 0 <= A.parent_bits <= A.split_bits <= K
    assert 0 <= A.parent_value < (1 << A.parent_bits)

    control = A.protected_control
    if control:
        assert (K, A.lower, A.upper) == (20, 524288, 1048575)
        assert (A.parent_bits, A.parent_value, A.split_bits) == (8, 103, 12)
        assert H <= 183
        scope = "frozen-small-control"
    else:
        assert A.lower >= LIVE_LOWER
        assert H < FIRST_DANGEROUS
        scope = "certified-transfer-domain"

    children = lawful_children(A.parent_bits, A.parent_value, A.split_bits)
    assert children, (A.parent_bits, A.parent_value, A.split_bits)

    widths = worst_widths(A.upper, H)
    req = req_odds(H)
    qw = (H + 1).bit_length() + 1
    start = time.time()
    rows = []

    with Cadical195() as solver:
        C = Circuit(solver)
        seed = [C.var() for _ in range(K)]
        C.add([C.uge_const(seed, A.lower)])
        C.add([C.ule_const(seed, A.upper)])
        for i in range(A.parent_bits):
            C.add([seed[i] if ((A.parent_value >> i) & 1) else -seed[i]])

        x = list(seed)
        qbits = [C.F] * qw

        for t in range(1, H + 1):
            p = x[0]
            u = x[1:]

            low = u[:K] + [C.F] * max(0, K - len(u))
            low_ge = C.uge_bits(low, seed)
            high = u[K:] if len(u) > K else []
            C.add([p, low_ge] + high)

            qbits = inc_if(C, qbits, p)
            C.add([C.uge_const(qbits, req[t])])

            x = step_conditional(C, x, widths[t])

        build_seconds = time.time() - start
        print(
            f"RESIDUE_SPLIT_EXACT parent={A.parent_value}/2^{A.parent_bits} "
            f"children={len(children)} split_bits={A.split_bits} H={H} "
            f"vars={C.nv} clauses={C.nc} build_seconds={build_seconds:.6f}",
            flush=True,
        )

        for child in children:
            assumptions = [
                seed[i] if ((child >> i) & 1) else -seed[i]
                for i in range(A.parent_bits, A.split_bits)
            ]
            s0 = time.time()
            ok = solver.solve(assumptions=assumptions)
            sec = time.time() - s0
            row = {
                "child": child,
                "status": "SAT" if ok else "UNSAT",
                "solve_seconds": sec,
            }
            if ok:
                model = set(v for v in solver.get_model() if v > 0)
                n = sum((1 << i) for i, v in enumerate(seed) if v in model)
                rep = replay(n, A.replay_limit)
                assert A.lower <= n <= A.upper
                assert n % (1 << A.split_bits) == child, (n, child)
                assert rep["first_descent"] is None or rep["first_descent"] > H, (n, H, rep)
                row["witness"] = str(n)
                row["replay"] = rep
            rows.append(row)
            print("CHILD", json.dumps(row, separators=(",", ":")), flush=True)

    sat = [r for r in rows if r["status"] == "SAT"]
    summary = {
        "kind": "exact_hybrid_assumption_residue_partition",
        "scope": scope,
        "bits": K,
        "lower": str(A.lower),
        "upper": str(A.upper),
        "horizon": H,
        "parent_bits": A.parent_bits,
        "parent_value": A.parent_value,
        "split_bits": A.split_bits,
        "lawful_children": children,
        "lawful_child_count": len(children),
        "sat_child_count": len(sat),
        "sat_children": [r["child"] for r in sat],
        "status": "SAT" if sat else "UNSAT",
        "results": rows,
        "build_seconds": build_seconds,
        "wall_seconds": time.time() - start,
    }
    Path(A.out).write_text(json.dumps(summary, indent=2) + "\n")
    print("RESULT_JSON", json.dumps(summary, separators=(",", ":")), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", type=int, required=True)
    ap.add_argument("--lower", type=int, required=True)
    ap.add_argument("--upper", type=int, required=True)
    ap.add_argument("--horizon", type=int, required=True)
    ap.add_argument("--parent-bits", type=int, default=8)
    ap.add_argument("--parent-value", type=int, required=True)
    ap.add_argument("--split-bits", type=int, default=12)
    ap.add_argument("--replay-limit", type=int, default=5000)
    ap.add_argument("--protected-control", action="store_true")
    ap.add_argument("--out", default="residue-split.json")
    A = ap.parse_args()
    solve_partition(A)


if __name__ == "__main__":
    main()
