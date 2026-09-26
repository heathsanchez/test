"""Independent replay and deliberately adversarial normalization contracts."""
import importlib.util
import random
import unittest
from pathlib import Path

FILE = Path(__file__).with_name('source_product.py')
SPEC = importlib.util.spec_from_file_location('source_product', FILE) if FILE.exists() else None
if SPEC:
    import sys
    product = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = product
    SPEC.loader.exec_module(product)
else:
    product = None


def direct(x):
    return x // 2 if x % 2 == 0 else (3 * x + 1) // 2


class ProductTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(product, 'exact source-product implementation is absent')

    def assert_trace(self, n, depth):
        s = product.initial(n)
        x, A, B, q = n, 1, 0, 0
        for k in range(depth + 1):
            self.assertEqual(s.source, n)
            self.assertEqual(s.depth, k)
            self.assertEqual(s.odd_steps, q)
            self.assertEqual(s.endpoint, x)
            self.assertEqual(s.source_scale, 2**k)
            self.assertEqual(s.endpoint_scale, A)
            self.assertEqual(s.intercept, B)
            self.assertEqual(s.tail, n // 2**k)
            self.assertEqual(s.tail, x // A)
            self.assertEqual(s.source_residue, n % 2**k)
            self.assertEqual(s.endpoint_residue, x % A)
            self.assertTrue(s.valid())
            self.assertEqual((2**k)*x, A*n+B)
            if k != depth:
                if x % 2:
                    A *= 3
                    B = 3*B + 2**k
                    q += 1
                x = direct(x)
                s = product.advance(s)
        return s

    def test_all_small_sources(self):
        for n in range(1, 1025):
            self.assert_trace(n, 40)

    def test_all_binary_cylinders_through_depth_10(self):
        for k in range(11):
            for r in range(2**k):
                for u in (1, 3):
                    s = self.assert_trace(r + 2**k*u, k)
                    self.assertEqual(s.source_residue, r)
                    self.assertEqual(s.tail, u)

    def test_large_sources_and_long_continuations(self):
        rng = random.Random(26092026)
        for bits in (72, 128, 256, 512):
            for _ in range(8):
                n = rng.getrandbits(bits) | (1 << (bits-1))
                self.assert_trace(n, 600)

    def test_positive_source_domain(self):
        for n in (0, -1, -27):
            with self.assertRaises(ValueError):
                product.initial(n)

    def test_tail_zero_is_not_terminal_or_strict_rank(self):
        s = self.assert_trace(27, 5)
        t = product.advance(s)
        self.assertEqual((s.endpoint, t.endpoint), (71, 107))
        self.assertEqual((s.tail, t.tail), (0, 0))
        self.assertGreater(s.endpoint, s.source)
        self.assertGreater(t.endpoint, t.source)
        self.assertNotIn(s.endpoint, (1, 2))
        self.assertNotIn(t.endpoint, (1, 2))

    def test_identical_tail_can_have_different_consequences(self):
        a = self.assert_trace(27, 5)
        b = self.assert_trace(31, 5)
        self.assertEqual(a.tail, b.tail)
        self.assertNotEqual(a.endpoint, b.endpoint)
        self.assertNotEqual(product.advance(a).endpoint, product.advance(b).endpoint)

    def test_no_fixed_near_return_gap_is_assumed(self):
        s = self.assert_trace(2**100-1, 50)
        self.assertGreater(s.endpoint-s.source, 30_243_148_343)
        self.assertTrue(s.valid())

    def test_all_odd_prefix_preserved(self):
        for k in range(1, 80):
            s = self.assert_trace(2**k-1, k)
            self.assertEqual(s.odd_steps, k)
            self.assertEqual(s.endpoint, 3**k-1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
