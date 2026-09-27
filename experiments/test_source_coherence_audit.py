"""Independent exact regressions. These fixtures are not Collatz counterexamples."""
import unittest


def step(n: int) -> int:
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


def trace(n: int, depth: int):
    values, odd, bias = [n], 0, 0
    for k in range(depth):
        if values[-1] % 2:
            odd += 1
            bias = 3 * bias + (1 << k)
        values.append(step(values[-1]))
    return values, odd, bias


class CoherenceTests(unittest.TestCase):
    def test_all_depth_closed_set_certificate(self):
        safe = {1, 2, 3, 4, 5, 6, 8}
        self.assertTrue(set(range(1, 7)) <= safe)
        self.assertTrue(all(step(x) in safe for x in safe))
        self.assertNotIn(7, safe)

    def test_numeric_envelope_is_consistent(self):
        n, y, depth, q, b = 7, 7, 8, 5, 91
        A, Q = 1 << depth, 3 ** q
        self.assertTrue(1 < n <= y and q < n and 3 * (y - n) < q)
        self.assertTrue((1 << (depth - 1)) <= Q < A <= 3 ** (q + 1))
        self.assertEqual(A * y, Q * n + b)
        self.assertLessEqual(3 * b, q * Q)
        self.assertEqual(y % 12, 7)
        self.assertEqual(trace(n, depth)[1], q)

    def test_actual_source_coupling_rejects_fixture(self):
        path, q, b = trace(7, 8)
        self.assertEqual(path, [7, 11, 17, 26, 13, 20, 10, 5, 8])
        self.assertEqual((q, b), (5, 347))
        self.assertNotEqual(path[-1], 7)
        self.assertNotEqual(b, 91)

    def test_actual_first_crossing_is_seven_not_eight(self):
        values, q, _ = trace(7, 8)
        count = 0
        first = None
        for d, x in enumerate(values[:-1], 1):
            count += x % 2
            if first is None and 3 ** count < 2 ** d:
                first = d
        self.assertEqual(first, 7)
        self.assertLess(values[first], 7)

    def test_no_exit_is_not_forward_invariant(self):
        self.assertEqual(trace(7, 7)[0][-1], 5)
        self.assertTrue(0 < 5 < 7)

    def test_a_later_real_exit_is_valid(self):
        self.assertEqual(trace(5, 1)[0][-1], trace(7, 8)[0][-1])
        self.assertLess(5, 7)


if __name__ == '__main__':
    unittest.main()
