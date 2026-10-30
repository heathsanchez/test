"""Exact-form two-state falsifier for an overbroad Doob-transform statement.

The fixture is analytic; floats only evaluate formulas containing sqrt(5).
No stochastic simulation, fitting, external data, or model-specific tuning.
"""

import argparse
import json
from math import sqrt


def matvec(m, x):
    return [sum(a * b for a, b in zip(row, x)) for row in m]


def stationary2(generator):
    forward, backward = generator[0][1], generator[1][0]
    return [backward / (forward + backward), forward / (forward + backward)]


def witness():
    # Q is an irreducible conservative CTMC generator, V a killing potential.
    q = [[-1.0, 1.0], [1.0, -1.0]]
    v = [0.0, 1.0]
    killed = [[q[i][j] - (v[i] if i == j else 0.0)
               for j in range(2)] for i in range(2)]
    h = [1.0, (sqrt(5.0) - 1.0) / 2.0]
    lam = (3.0 - sqrt(5.0)) / 2.0

    # The paper's bare transform uses the un-killed generator Q.
    bare = [[q[i][j] * h[j] / h[i] for j in range(2)] for i in range(2)]
    # Correct Q-process generator: H^-1 (Q - V + lambda I) H.
    conditioned = [[(killed[i][j] + (lam if i == j else 0.0)) * h[j] / h[i]
                    for j in range(2)] for i in range(2)]

    baseline_stationary = [0.5, 0.5]
    claimed_survivor = [baseline_stationary[i] * h[i] for i in range(2)]
    claimed_survivor = [x / sum(claimed_survivor) for x in claimed_survivor]
    actual_stationary = stationary2(conditioned)
    # Here killed is symmetric, so its left principal eigenvector equals h.
    left_right_stationary = [x * x for x in h]
    left_right_stationary = [x / sum(left_right_stationary) for x in left_right_stationary]
    return {
        "q": q, "killed": killed, "v": v, "h": h, "lambda": lam,
        "eigen_residual": [matvec(killed, h)[i] + lam * h[i] for i in range(2)],
        "bare": bare, "bare_mass_derivative": matvec(bare, [1.0, 1.0]),
        "conditioned": conditioned,
        "conditioned_mass_derivative": matvec(conditioned, [1.0, 1.0]),
        "baseline_stationary": baseline_stationary,
        "claimed_p_times_h": claimed_survivor,
        "actual_conditioned_stationary": actual_stationary,
        "left_times_right_stationary": left_right_stationary,
        "E1_baseline_positive_f_qf": matvec(q, [1.0, 0.0]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assert-original-generator-is-markov", action="store_true")
    args = ap.parse_args()
    w = witness()
    print(json.dumps(w, sort_keys=True, indent=2))
    if args.assert_original_generator_is_markov:
        if any(abs(x) > 1e-10 for x in w["bare_mass_derivative"]):
            raise SystemExit("EXPECTED_COUNTEREXAMPLE: h^-1 Q(h f) is not conservative")


if __name__ == "__main__":
    main()
