#!/usr/bin/env python3
"""
Emit the exact goal-native no-descent CNF without trusting a SAT solver.

The encoding is the even-step contraction from collatz_exact_cnf_even.py:
an odd shortcut step is strictly increasing for x>1, so a first descent can
only occur when the current iterate is even.  At each step we therefore
require x/2 >= seed whenever x is even, then encode the exact next iterate.

Optional fixed low seed bits support exact parity-prefix quotienting.
"""
import argparse
import json
import time
from pathlib import Path

from collatz_exact_cnf_even import Circuit, worst_widths


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
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--low-bits", type=int, default=0)
    ap.add_argument("--low-value", type=int, default=0)
    A = ap.parse_args()

    K, H = A.bits, A.horizon
    assert 0 <= A.lower <= A.upper < (1 << K)
    assert 0 <= A.low_bits <= K
    assert (0 <= A.low_value < (1 << A.low_bits)) if A.low_bits else A.low_value == 0

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
    x = list(seed)

    for _t in range(1, H + 1):
        p = x[0]
        u = x[1:]

        # If the current iterate is even, the next iterate is u=x/2.
        # Requiring u>=seed at every even step is exactly "no descent yet".
        low = u[:K] + [C.F] * max(0, K - len(u))
        low_ge = C.uge_bits(low, seed)
        high = u[K:] if len(u) > K else []
        C.add([p, low_ge] + high)

        ow = widths[_t]
        uu = u[:ow] + [C.F] * max(0, ow - len(u))
        twice = ([C.F] + u)[:ow]
        twice += [C.F] * max(0, ow - len(twice))
        odd = C.add_const(C.add2(uu, twice, ow), 2, ow)
        x = [C.mux(p, uu[i], odd[i]) for i in range(ow)]

    cnf = out / "problem.cnf"
    write_dimacs(cnf, C.nv, sink.clauses)
    meta = {
        "kind": "exact_even_step_no_descent_cnf",
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
    print("NO_DESCENT_CNF_JSON", json.dumps(meta, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
