"""Exact binary-tilt counterexample to the maximal-variance clause of Theorem 12.1.

The March 2026 Recursive Distillation Manual §12.2 equates a fixed point of
beta' = kappa*(Var_beta(h)-lambda*beta) with maximal discriminative capacity.
We test the mathematical implication; this does not address physics.
"""

import math
import sys
import unittest


def variance(beta: float) -> float:
    """Variance of h=(0,1) under p_beta=(1,e^beta)/(1+e^beta)."""
    return 1.0 / (4.0 * math.cosh(beta / 2.0) ** 2)


def variance_derivative(beta: float) -> float:
    return -variance(beta) * math.tanh(beta / 2.0)


def equilibrium(lam: float = 1.0) -> float:
    """Unique positive root of Var_beta(h) = lambda*beta for lambda>0."""
    assert lam > 0.0
    lo, hi = 0.0, max(1.0, 1.0 / lam)
    for _ in range(90):
        middle = (lo + hi) / 2.0
        if variance(middle) > lam * middle:
            lo = middle
        else:
            hi = middle
    return (lo + hi) / 2.0


class BinaryTiltCriticality(unittest.TestCase):
    def test_variance_matches_direct_binary_distribution(self):
        for beta in [0.0, 0.1, 0.2462480927475339, 0.5, 1.0, 3.0]:
            p = math.exp(beta) / (1.0 + math.exp(beta))
            self.assertAlmostEqual(variance(beta), p * (1.0 - p), places=14)

    def test_variance_strictly_decreases_for_positive_beta(self):
        self.assertAlmostEqual(variance(0.0), 0.25, places=15)
        for beta in [0.01, 0.1, 0.2, 0.5, 1.0, 3.0]:
            self.assertLess(variance_derivative(beta), 0.0)
            self.assertLess(variance(beta), variance(0.0))

    def test_stable_positive_balance_point_does_exist(self):
        beta = equilibrium(lam=1.0)
        self.assertAlmostEqual(beta, 0.2462480927475339, places=12)
        self.assertAlmostEqual(variance(beta), beta, places=13)
        # This *retains* the correct fixed-point claim in Theorem 12.1.
        self.assertLess(variance_derivative(beta) - 1.0, 0.0)

    def test_balance_does_not_maximize_variance_or_variance_per_beta(self):
        beta = equilibrium(lam=1.0)
        self.assertGreater(variance(beta / 2.0), variance(beta))
        self.assertGreater(variance(0.0), variance(beta))
        self.assertGreater(variance(beta / 2.0) / (beta / 2.0), variance(beta) / beta)


if __name__ == "__main__":
    if "--assert-balance-maximizes-variance" in sys.argv:
        beta = equilibrium(lam=1.0)
        assert variance(beta) >= variance(0.0), "EXPECTED_CRITICALITY_COUNTEREXAMPLE"
    else:
        unittest.main()
