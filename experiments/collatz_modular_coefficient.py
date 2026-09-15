#!/usr/bin/env python3
"""
Exact shrinking-modular coefficient-persistence CNF for shortcut Collatz.

To determine the remaining parity word from time t through horizon H, it is
sufficient to know x_t modulo 2^(H-t).  Independently, an all-odd recurrence
gives an absolute bit-length upper bound B_t for every possible x_t.

Therefore the exact state width is
    W_t = min(B_t, H-t)
for t=0..H-1.

If W_t=B_t the represented state is the exact integer (higher bits are known
zero).  Otherwise it is the exact residue modulo 2^(H-t).  In either case the
next parity and the next required residue are exact.  No magnitude trajectory
is retained.

On the certified live interval, for H below FIRST_DANGEROUS, coefficient
persistence is equivalent to no descent through H by the transfer theorem.
"""
import argparse
import json
import time
from pathlib import Path

from pysat.solvers import Cadical195

from collatz_exact_cnf_even import Circuit
from collatz_coefficient_cnf import req_odds, replay
from collatz_hybrid_adaptive import inc_if, step_conditional, LIVE_LOWER, FIRST_DANGEROUS


def absolute_widths(upper: int, horizon: int):
    """Bit-length bounds under the monotone all-odd envelope."""
    m = upper
    out = [max(1, m.bit_length())]
    for _ in range(horizon):
        m = (3 * m + 1) // 2
        out.append(max(1, m.bit_length()))
    return out


def modular_widths(upper: int, horizon: int):
    """
    Width of x_t needed to determine parities t..H-1 exactly.
    There is no state needed after the H-th parity decision.
    """
    b = absolute_widths(upper, horizon)
    return [max(1, min(b[t], horizon - t)) for t in range(horizon)]


def build_modular_persistence(C, seed, upper: int, horizon: int):
    """Add exact coefficient-persistence constraints; return width statistics."""
    req = req_odds(horizon)
    bounds = absolute_widths(upper, horizon)
    widths = [max(1, min(bounds[t], horizon - t)) for t in range(horizon)]
    qw = (horizon + 1).bit_length() + 1

    # x_0 modulo 2^W0.  If W0<K, discarding higher seed bits is exact for
    # the remaining parity word; the full seed remains available to range
    # constraints and witness reconstruction.
    x = list(seed[: widths[0]])
    qbits = [C.F] * qw
    parity = []

    for step in range(1, horizon + 1):
        p = x[0]
        parity.append(p)
        qbits = inc_if(C, qbits, p)
        C.add([C.uge_const(qbits, req[step])])

        if step == horizon:
            break

        # Need x_step modulo 2^W_step. step_conditional uses exactly the
        # low W_step+1 source bits; if fewer source bits exist, the current
        # state is exact and the missing high bits are known zero.
        x = step_conditional(C, x, widths[step])

    return {
        "absolute_widths": bounds,
        "modular_widths": widths,
        "width_sum": sum(widths),
        "width_max": max(widths),
        "parity": parity,
    }


def solve(A):
    K, H = A.bits, A.horizon
    assert 0 <= A.lower <= A.upper < (1 << K)
    assert H >= 1
    assert 0 <= A.low_bits <= K
    assert (0 <= A.low_value < (1 << A.low_bits)) if A.low_bits else A.low_value == 0

    if A.protected_control:
        assert (K, A.lower, A.upper) == (20, 524288, 1048575)
        assert H <= 183
        scope = "frozen-small-control"
    else:
        assert A.lower >= LIVE_LOWER, (A.lower, LIVE_LOWER)
        assert H < FIRST_DANGEROUS, (H, FIRST_DANGEROUS)
        scope = "certified-transfer-domain"

    start = time.time()
    with Cadical195() as solver:
        C = Circuit(solver)
        seed = [C.var() for _ in range(K)]
        C.add([C.uge_const(seed, A.lower)])
        C.add([C.ule_const(seed, A.upper)])
        for i in range(A.low_bits):
            C.add([seed[i] if ((A.low_value >> i) & 1) else -seed[i]])

        meta = build_modular_persistence(C, seed, A.upper, H)
        build_seconds = time.time() - start

        s0 = time.time()
        ok = solver.solve()
        solve_seconds = time.time() - s0
        row = {
            "kind": "exact_shrinking_modular_coefficient_persistence",
            "scope": scope,
            "bits": K,
            "lower": str(A.lower),
            "upper": str(A.upper),
            "horizon": H,
            "low_bits": A.low_bits,
            "low_value": A.low_value,
            "vars": C.nv,
            "clauses": C.nc,
            "width_sum": meta["width_sum"],
            "width_max": meta["width_max"],
            "absolute_width_max": max(meta["absolute_widths"]),
            "status": "SAT" if ok else "UNSAT",
            "build_seconds": build_seconds,
            "solve_seconds": solve_seconds,
            "wall_seconds": time.time() - start,
        }

        if ok:
            model = {v for v in solver.get_model() if v > 0}
            n = sum((1 << i) for i, var in enumerate(seed) if var in model)
            rep = replay(n, max(A.replay_limit, H + 1))
            assert A.lower <= n <= A.upper
            if A.low_bits:
                assert n % (1 << A.low_bits) == A.low_value, (n, A.low_value)
            assert rep["first_contract"] is None or rep["first_contract"] > H, (n, H, rep)
            if not A.protected_control:
                assert rep["first_descent"] is None or rep["first_descent"] > H, (n, H, rep)
            row["witness"] = str(n)
            row["replay"] = rep

        Path(A.out).write_text(json.dumps(row, indent=2) + "\n")
        print("MODULAR_RESULT", json.dumps(row, separators=(",", ":")), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", type=int, required=True)
    ap.add_argument("--lower", type=int, required=True)
    ap.add_argument("--upper", type=int, required=True)
    ap.add_argument("--horizon", type=int, required=True)
    ap.add_argument("--low-bits", type=int, default=0)
    ap.add_argument("--low-value", type=int, default=0)
    ap.add_argument("--replay-limit", type=int, default=5000)
    ap.add_argument("--protected-control", action="store_true")
    ap.add_argument("--out", default="modular-coefficient.json")
    A = ap.parse_args()
    solve(A)


if __name__ == "__main__":
    main()
