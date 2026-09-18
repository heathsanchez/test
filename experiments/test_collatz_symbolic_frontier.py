import unittest
from collatz_symbolic_frontier import compile_frontier, verify, classify, scalar, verify_cover


class SymbolicTests(unittest.TestCase):
    def test_threshold_equality_is_not_descent(self):
        bank, residual, exceptions = compile_frontier(2)
        odd = next(c for c in bank if c['b'] == 1)
        self.assertEqual(odd['Q'], 1)
        self.assertIsNone(classify(1, bank))
        self.assertIsNotNone(classify(5, bank))

    def test_corrupt_endpoint_rejected(self):
        bank, _, _ = compile_frontier(3)
        with self.assertRaises(ValueError): verify(dict(bank[0], d=99))

    def test_exact_disjoint_partition(self):
        bank, residual, exceptions = compile_frontier(8)
        for n in range(2, 2048):
            terminal = classify(n, bank)
            pending = sum(n % 2**s['k'] == s['b'] for s in residual)
            self.assertEqual(int(terminal is not None) + pending + int(n in exceptions), 1)
            if terminal:
                x = n
                for _ in range(terminal['k']): x = x//2 if x%2==0 else (3*x+1)//2
                self.assertLess(x, n)

    def test_budget_exhaustion_stays_unknown(self):
        self.assertIsNone(scalar(27, 1))

    def test_missing_region_rejected(self):
        bank, residual, _ = compile_frontier(8)
        with self.assertRaises(ValueError): verify_cover(bank, residual[:-1])

    def test_overlapping_region_rejected(self):
        bank, residual, _ = compile_frontier(8)
        with self.assertRaises(ValueError): verify_cover(bank+[bank[0]], residual)


if __name__ == '__main__': unittest.main()
