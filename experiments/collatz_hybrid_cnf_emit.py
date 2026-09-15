#!/usr/bin/env python3
"""
Emit the exact theorem-strengthened shortcut-Collatz no-descent CNF.

The base predicate is goal-native: at every even iterate x, require x/2 >= seed.
On the certified live domain and below the first dangerous transfer resonance,
no-descent implies coefficient persistence, so the prefix odd-density bounds are
added as redundant clauses to improve propagation without changing the model set.

The emitted DIMACS is solver-independent and suitable for standalone CaDiCaL
plus independent DRAT-trim verification.
"""
import argparse
import json
import time
from pathlib import Path

from collatz_exact_cnf_even import Circuit, worst_widths
from collatz_coefficient_cnf import req_odds
from collatz_hybrid_adaptive import inc_if, step_conditional, LIVE_LOWER, FIRST_DANGEROUS


class ClauseSink:
    def __init__(self):
        self.clauses = []

    def add_clause(self, clause):
        self.clauses.append(list(clause))


def write_dimacs(path, nv, clauses):
    with open(path, "w", encoding="ascii") as f:
        f.write(f"p cnf {nv} {len(clauses)}\n")
        for clause in clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", type=int, required=True)
    ap.add_argument("--lower", type=int, required=True)
    ap.add_argument("--upper", type=int, required=True)
    ap.add_argument("--horizon", type=int, required=True)
    ap.add_argument("--low-bits", type=int, default=0)
    ap.add_argument("--low-value", type=int, default=0)
    ap.add_argument("--protected-control", action="store_true")
    ap.add_argument("--out-dir", required=True)
    A = ap.parse_args()

    K, H = A.bits, A.horizon
    assert 0 <= A.lower <= A.upper < (1 << K)
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

    out = Path(A.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    start = time.time()

    sink = ClauseSink()
    C = Circuit(sink)
    seed = [C.var() for _ in range(K)]
    C.add([C.uge_const(seed, A.lower)])
    C.add([C.ule_const(seed, A.upper)])
    for i in range(A.low_bits):
        C.add([seed[i] if ((A.low_value >> i) & 1) else -seed[i]])

    widths = worst_widths(A.upper, H)
    req = req_odds(H)
    qbits = [C.F] * ((H + 1).bit_length() + 1)
    x = list(seed)

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

    cnf = out / "problem.cnf"
    write_dimacs(cnf, C.nv, sink.clauses)
    meta = {
        "kind": "exact_hybrid_no_descent_transfer_density_cnf",
        "scope": scope,
        "bits": K,
        "lower": str(A.lower),
        "upper": str(A.upper),
        "horizon": H,
        "low_bits": A.low_bits,
        "low_value": A.low_value,
        "vars": C.nv,
        "clauses": len(sink.clauses),
        "build_seconds": time.time() - start,
        "cnf": cnf.name,
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    print("HYBRID_CNF_JSON", json.dumps(meta, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
