#!/usr/bin/env python3
"""
Exact adaptive shortcut-Collatz no-descent search strengthened by the certified
first-contraction transfer theorem.

On the certified live domain
    n >= 2075*2^60
and for
    H < 114208327604,
no-descent through H implies coefficient persistence at every prefix.  We add
those coefficient-density inequalities as redundant SAT clauses.  They do not
change the live model set; they expose theorem-level structure to propagation.

A single frozen small control is permitted only to protect the encoding:
bits=20, interval [524288,1048575], low8=103, H<=183.
"""
import argparse
import json
import time
from pathlib import Path

from pysat.solvers import Cadical195
from collatz_exact_cnf_even import Circuit, worst_widths, replay
from collatz_coefficient_cnf import req_odds

LIVE_LOWER = 2075 * (1 << 60)
FIRST_DANGEROUS = 114208327604


def inc_if(c: Circuit, bits, cond):
    out = []
    carry = cond
    for x in bits:
        out.append(c.lxor(x, carry))
        carry = c.land(x, carry)
    return out


def step_conditional(c: Circuit, x, wnext):
    """Exact shortcut step with conditional increment plus one full adder."""
    p = x[0]
    u = x[1:]
    u = u[:wnext] + [c.F] * max(0, wnext - len(u))

    # w = p ? (u+1) : 0
    carry = p
    w = []
    for ui in u:
        inc = c.lxor(ui, carry)
        w.append(c.land(p, inc))
        carry = c.land(ui, carry)

    # p=0 -> u; p=1 -> u + 2(u+1) = 3u+2.
    addend = [c.F] + w[:-1]
    return c.add2(u, addend, wnext)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", type=int, required=True)
    ap.add_argument("--lower", type=int, required=True)
    ap.add_argument("--upper", type=int, required=True)
    ap.add_argument("--start-horizon", type=int, required=True)
    ap.add_argument("--max-horizon", type=int, default=1000)
    ap.add_argument("--min-jump", type=int, default=16)
    ap.add_argument("--replay-limit", type=int, default=5000)
    ap.add_argument("--low-bits", type=int, default=0)
    ap.add_argument("--low-value", type=int, default=0)
    ap.add_argument("--protected-control", action="store_true")
    ap.add_argument("--out", default="hybrid-adaptive.json")
    A = ap.parse_args()

    K = A.bits
    assert 0 <= A.lower <= A.upper < (1 << K)
    assert 1 <= A.start_horizon <= A.max_horizon
    assert 0 <= A.low_bits <= K
    assert (0 <= A.low_value < (1 << A.low_bits)) if A.low_bits else A.low_value == 0

    if A.protected_control:
        assert (K, A.lower, A.upper) == (20, 524288, 1048575)
        assert (A.low_bits, A.low_value) == (8, 103)
        assert A.max_horizon <= 183
        scope = "frozen-small-control"
    else:
        assert A.lower >= LIVE_LOWER, (A.lower, LIVE_LOWER)
        assert A.max_horizon < FIRST_DANGEROUS
        scope = "certified-transfer-domain"

    widths = worst_widths(A.upper, A.max_horizon)
    req = req_odds(A.max_horizon)
    qw = (A.max_horizon + 1).bit_length() + 1
    results = []
    start = time.time()
    next_check = A.start_horizon

    with Cadical195() as solver:
        C = Circuit(solver)
        seed = [C.var() for _ in range(K)]
        C.add([C.uge_const(seed, A.lower)])
        C.add([C.ule_const(seed, A.upper)])
        for i in range(A.low_bits):
            C.add([seed[i] if ((A.low_value >> i) & 1) else -seed[i]])

        x = list(seed)
        qbits = [C.F] * qw

        print(
            f"HYBRID_ADAPTIVE_EXACT bits={K} lower={A.lower} upper={A.upper} "
            f"start={A.start_horizon} max={A.max_horizon} "
            f"low_bits={A.low_bits} low_value={A.low_value} scope={scope}",
            flush=True,
        )

        for t in range(1, A.max_horizon + 1):
            p = x[0]
            u = x[1:]

            # Goal-native constraint: a first descent can only occur on an
            # even input, so if p=0 require x/2 >= seed.
            low = u[:K] + [C.F] * max(0, K - len(u))
            low_ge = C.uge_bits(low, seed)
            high = u[K:] if len(u) > K else []
            C.add([p, low_ge] + high)

            # Transfer-derived redundant lemma: every no-descent live model
            # must retain coefficient persistence at this prefix.
            qbits = inc_if(C, qbits, p)
            C.add([C.uge_const(qbits, req[t])])

            # Exact arithmetic, using the one-adder conditional form.
            x = step_conditional(C, x, widths[t])

            if t != next_check:
                continue

            s0 = time.time()
            ok = solver.solve()
            sec = time.time() - s0
            row = {
                "horizon": t,
                "status": "SAT" if ok else "UNSAT",
                "solve_seconds": sec,
                "vars": C.nv,
                "clauses": C.nc,
                "wall_seconds": time.time() - start,
            }

            if not ok:
                results.append(row)
                print("CHECK", json.dumps(row, separators=(",", ":")), flush=True)
                break

            model = set(v for v in solver.get_model() if v > 0)
            n = sum((1 << i) for i, v in enumerate(seed) if v in model)
            rep = replay(n, A.replay_limit)
            fd = rep["first_descent"]
            assert A.lower <= n <= A.upper
            assert n % (1 << A.low_bits) == A.low_value if A.low_bits else True
            assert fd is None or fd > t, (n, t, rep)
            row["witness"] = n
            row["replay"] = rep
            results.append(row)
            print("CHECK", json.dumps(row, separators=(",", ":")), flush=True)

            if t >= A.max_horizon:
                break
            candidate = t + A.min_jump
            if fd is not None:
                candidate = max(candidate, fd + 1)
            next_check = min(A.max_horizon, candidate)
            print(f"NEXT_CHECK {next_check}", flush=True)

        status = results[-1]["status"] if results else "NO_CHECK"
        summary = {
            "kind": "exact_hybrid_no_descent_plus_transfer_density",
            "scope": scope,
            "bits": K,
            "lower": str(A.lower),
            "upper": str(A.upper),
            "start_horizon": A.start_horizon,
            "max_horizon": A.max_horizon,
            "min_jump": A.min_jump,
            "low_bits": A.low_bits,
            "low_value": A.low_value,
            "status": status,
            "results": results,
            "wall_seconds": time.time() - start,
        }
        Path(A.out).write_text(json.dumps(summary, indent=2) + "\n")
        print("RESULT_JSON", json.dumps(summary, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
