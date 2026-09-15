#!/usr/bin/env python3
"""
Proof-producing exact coefficient-persistence checker.

Uses the same exact CNF construction as collatz_coefficient_cnf_v2.py, but
records the final DIMACS formula and, on UNSAT, CaDiCaL's DRUP refutation.
A downstream proof checker can therefore validate UNSAT without trusting
this Python process or CaDiCaL's answer.
"""
import argparse, json, time
from pathlib import Path
from pysat.solvers import Cadical195
from collatz_coefficient_cnf import C, req_odds, replay
from collatz_coefficient_cnf_v2 import worst_widths, step_conditional

class RecordingSolver:
    def __init__(self):
        self.inner = Cadical195(with_proof=True)
        self.clauses = []
    def add_clause(self, clause):
        row = list(clause)
        self.clauses.append(row)
        self.inner.add_clause(row)
    def solve(self):
        return self.inner.solve()
    def get_model(self):
        return self.inner.get_model()
    def get_proof(self):
        return self.inner.get_proof()
    def delete(self):
        self.inner.delete()

def write_dimacs(path, nv, clauses):
    with open(path, "w", encoding="ascii") as f:
        f.write(f"p cnf {nv} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(map(str, cl)) + " 0\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bits", type=int, required=True)
    ap.add_argument("--lower", type=int, required=True)
    ap.add_argument("--upper", type=int, required=True)
    ap.add_argument("--horizon", type=int, required=True)
    ap.add_argument("--replay-limit", type=int, default=10000)
    ap.add_argument("--out-dir", required=True)
    A = ap.parse_args()

    K, H = A.bits, A.horizon
    assert 0 <= A.lower <= A.upper < (1 << K)
    out = Path(A.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    req = req_odds(H)
    widths = worst_widths(A.upper, H)
    qwidth = (H + 1).bit_length() + 1
    start = time.time()

    s = RecordingSolver()
    try:
        c = C(s)
        seed = [c.var() for _ in range(K)]
        c.add([c.uge_const(seed, A.lower)])
        c.add([c.ule_const(seed, A.upper)])
        x = seed + [c.F] * max(0, widths[0] - K)
        qbits = [c.F] * qwidth

        for t in range(1, H + 1):
            x, odd = step_conditional(c, x, widths[t])
            qbits = c.inc_if(qbits, odd)
            c.add([c.uge_const(qbits, req[t])])

        build_seconds = time.time() - start
        solve_start = time.time()
        sat = s.solve()
        solve_seconds = time.time() - solve_start

        summary = {
            "kind": "exact_coefficient_persistence_drup",
            "bits": K,
            "lower": str(A.lower),
            "upper": str(A.upper),
            "horizon": H,
            "vars": c.nv,
            "clauses": len(s.clauses),
            "build_seconds": build_seconds,
            "solve_seconds": solve_seconds,
            "status": "SAT" if sat else "UNSAT",
        }

        if sat:
            model = {v for v in s.get_model() if v > 0}
            n = sum((1 << i) for i, v in enumerate(seed) if v in model)
            rep = replay(n, A.replay_limit)
            assert A.lower <= n <= A.upper
            assert rep["first_contract"] is None or rep["first_contract"] > H, (n, H, rep)
            summary["witness"] = str(n)
            summary["replay"] = rep
        else:
            cnf = out / "problem.cnf"
            proof = out / "proof.drup"
            write_dimacs(cnf, c.nv, s.clauses)
            lines = s.get_proof()
            assert lines is not None and len(lines) > 0
            proof.write_text("\n".join(lines) + "\n", encoding="ascii")
            summary["cnf"] = cnf.name
            summary["proof"] = proof.name
            summary["proof_lines"] = len(lines)

        summary["wall_seconds"] = time.time() - start
        (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print("RESULT_JSON", json.dumps(summary, separators=(",", ":")), flush=True)
    finally:
        s.delete()

if __name__ == "__main__":
    main()
