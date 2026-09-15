#!/usr/bin/env python3
"""
Budgeted exact residue refinement over the shrinking-modular Collatz state.

This combines:
  * exact coefficient persistence on only the low state bits needed for the
    remaining parity word;
  * exact live-domain equivalence to no-descent below FIRST_DANGEROUS;
  * lawful residue-prefix quotienting;
  * conflict-budgeted SAT probes where UNKNOWN triggers refinement, never a
    verdict.

The full 72-bit seed remains present for interval constraints and witness
reconstruction; only the deterministic trajectory state is quotiented.
"""
import argparse
import json
import time
from pathlib import Path

from pysat.solvers import Glucose4

from collatz_exact_cnf_even import Circuit
from collatz_coefficient_cnf import replay
from collatz_prefix_residues import survives_prefix
from collatz_hybrid_adaptive import LIVE_LOWER, FIRST_DANGEROUS
from collatz_modular_coefficient import build_modular_persistence


def lawful_children(value, bits, next_bits):
    stride = 1 << bits
    return [
        value + stride * k
        for k in range(1 << (next_bits - bits))
        if survives_prefix(value + stride * k, next_bits)
    ]


def assumptions_for(seed, fixed_bits, value, bits):
    return [
        seed[i] if ((value >> i) & 1) else -seed[i]
        for i in range(fixed_bits, bits)
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", type=int, required=True)
    ap.add_argument("--lower", type=int, required=True)
    ap.add_argument("--upper", type=int, required=True)
    ap.add_argument("--horizon", type=int, required=True)
    ap.add_argument("--parent-bits", type=int, default=8)
    ap.add_argument("--parent-value", type=int, required=True)
    ap.add_argument("--start-bits", type=int, default=12)
    ap.add_argument("--max-bits", type=int, default=16)
    ap.add_argument("--step-bits", type=int, default=4)
    ap.add_argument("--conflicts", type=int, default=100)
    ap.add_argument("--propagations", type=int, default=100000)
    ap.add_argument("--replay-limit", type=int, default=5000)
    ap.add_argument("--protected-control", action="store_true")
    ap.add_argument("--out", default="modular-adaptive.json")
    A = ap.parse_args()

    K, H = A.bits, A.horizon
    assert 0 <= A.lower <= A.upper < (1 << K)
    assert 0 <= A.parent_bits < A.start_bits <= A.max_bits <= K
    assert A.step_bits > 0
    assert (A.start_bits - A.parent_bits) % A.step_bits == 0
    assert (A.max_bits - A.start_bits) % A.step_bits == 0
    assert 0 <= A.parent_value < (1 << A.parent_bits)
    assert survives_prefix(A.parent_value, A.parent_bits)
    assert A.conflicts > 0
    assert A.propagations > 0

    if A.protected_control:
        assert (K, A.lower, A.upper) == (20, 524288, 1048575)
        assert (A.parent_bits, A.parent_value) == (8, 103)
        assert H <= 183
        scope = "frozen-small-control"
    else:
        assert A.lower >= LIVE_LOWER, (A.lower, LIVE_LOWER)
        assert H < FIRST_DANGEROUS, (H, FIRST_DANGEROUS)
        scope = "certified-transfer-domain"

    start = time.time()
    exact_sat = []
    exact_unsat = []
    unresolved = []
    probes = []

    with Glucose4() as solver:
        C = Circuit(solver)
        seed = [C.var() for _ in range(K)]
        C.add([C.uge_const(seed, A.lower)])
        C.add([C.ule_const(seed, A.upper)])
        for i in range(A.parent_bits):
            C.add([seed[i] if ((A.parent_value >> i) & 1) else -seed[i]])

        widths = build_modular_persistence(C, seed, A.upper, H)
        build_seconds = time.time() - start

        print(
            f"MODULAR_ADAPTIVE_EXACT parent={A.parent_value}/2^{A.parent_bits} "
            f"H={H} start_bits={A.start_bits} max_bits={A.max_bits} "
            f"conf_budget={A.conflicts} prop_budget={A.propagations} vars={C.nv} clauses={C.nc} "
            f"width_sum={widths['width_sum']} width_max={widths['width_max']} "
            f"build_seconds={build_seconds:.6f}",
            flush=True,
        )

        stack = [
            (v, A.start_bits)
            for v in reversed(lawful_children(A.parent_value, A.parent_bits, A.start_bits))
        ]

        while stack:
            value, bits = stack.pop()
            asm = assumptions_for(seed, A.parent_bits, value, bits)
            before = solver.accum_stats()
            solver.conf_budget(A.conflicts)
            solver.prop_budget(A.propagations)
            s0 = time.time()
            ok = solver.solve_limited(assumptions=asm)
            sec = time.time() - s0
            after = solver.accum_stats()
            used = max(0, after.get("conflicts", 0) - before.get("conflicts", 0))
            props = max(0, after.get("propagations", 0) - before.get("propagations", 0))

            row = {
                "value": value,
                "bits": bits,
                "status": "SAT" if ok is True else "UNSAT" if ok is False else "UNKNOWN",
                "solve_seconds": sec,
                "conflicts": used,
                "propagations": props,
            }

            if ok is True:
                model = {v for v in solver.get_model() if v > 0}
                n = sum((1 << i) for i, var in enumerate(seed) if var in model)
                rep = replay(n, max(A.replay_limit, H + 1))
                assert A.lower <= n <= A.upper
                assert n % (1 << bits) == value, (n, value, bits)
                assert rep["first_contract"] is None or rep["first_contract"] > H, (n, H, rep)
                if not A.protected_control:
                    assert rep["first_descent"] is None or rep["first_descent"] > H, (n, H, rep)
                row["witness"] = str(n)
                row["replay"] = rep
                exact_sat.append(row)
                print("SAT_LEAF", json.dumps(row, separators=(",", ":")), flush=True)

            elif ok is False:
                exact_unsat.append(row)
                print("UNSAT_LEAF", json.dumps(row, separators=(",", ":")), flush=True)

            elif bits < A.max_bits:
                nb = min(A.max_bits, bits + A.step_bits)
                kids = lawful_children(value, bits, nb)
                row["refined_to_bits"] = nb
                row["lawful_children"] = len(kids)
                print("REFINE", json.dumps(row, separators=(",", ":")), flush=True)
                for child in reversed(kids):
                    stack.append((child, nb))

            else:
                unresolved.append(row)
                print("UNRESOLVED_LEAF", json.dumps(row, separators=(",", ":")), flush=True)

            probes.append(row)

    summary = {
        "kind": "exact_modular_budgeted_residue_refinement",
        "scope": scope,
        "bits": K,
        "lower": str(A.lower),
        "upper": str(A.upper),
        "horizon": H,
        "parent_bits": A.parent_bits,
        "parent_value": A.parent_value,
        "start_bits": A.start_bits,
        "max_bits": A.max_bits,
        "step_bits": A.step_bits,
        "conflict_budget": A.conflicts,
        "propagation_budget": A.propagations,
        "status": "SAT" if exact_sat else "UNRESOLVED" if unresolved else "UNSAT",
        "sat_leaves": exact_sat,
        "unsat_leaf_count": len(exact_unsat),
        "unresolved_leaves": unresolved,
        "probe_count": len(probes),
        "vars": C.nv,
        "clauses": C.nc,
        "width_sum": widths["width_sum"],
        "width_max": widths["width_max"],
        "build_seconds": build_seconds,
        "wall_seconds": time.time() - start,
    }
    Path(A.out).write_text(json.dumps(summary, indent=2) + "\n")
    print("RESULT_JSON", json.dumps(summary, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
