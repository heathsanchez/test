import unittest
from research.collatz_F_swap_grammar import (
    compile_certificate, verify_certificate, T, iterate, affine_check)


class GrammarTests(unittest.TestCase):
    def test_new_swap_184(self):
        self.assertIsNone(compile_certificate(184, allow_swap=False))
        c = compile_certificate(184)
        self.assertIsNotNone(c)
        self.assertEqual(verify_certificate(c), 8)
        self.assertEqual(iterate(184, 8), 20)

    def test_source_attached_nondescending_witness(self):
        n, p = 22652991, 15909919
        self.assertIsNone(compile_certificate(n, allow_swap=False))
        c = compile_certificate(n)
        self.assertIsNotNone(c)
        self.assertEqual(verify_certificate(c), 15)
        self.assertEqual(iterate(n, 15), iterate(p, 24))
        self.assertLess(p, n)
        x = n
        for _ in range(15):
            x = T(x)
            self.assertGreaterEqual(x, n)
            self.assertFalse(x % 3 == 2 and 2*x-1 < 3*n)

    def test_two_swaps_compose(self):
        c = compile_certificate(2085)
        self.assertIsNotNone(c)
        self.assertEqual(sum(row['rule'] == 'swap' for row in c['steps']), 2)
        self.assertEqual(verify_certificate(c), 15)

    def test_adversarial_source_edit(self):
        c = compile_certificate(184)
        self.assertIsNotNone(c)
        c['source'] = 185
        with self.assertRaises(ValueError):
            verify_certificate(c)

    def test_adversarial_clock_edit(self):
        c = compile_certificate(184)
        self.assertIsNotNone(c)
        c['clock'] += 1
        with self.assertRaises(ValueError):
            verify_certificate(c)

    def test_opposite_terminal_phase_is_unknown(self):
        self.assertIsNone(compile_certificate(3))
        self.assertEqual((iterate(3, 10), iterate(11, 10)), (2, 1))
        for j in range(100):
            self.assertNotEqual(iterate(3, j), iterate(11, j))

    def test_two_run_coordinates(self):
        for k in (0, 1, 2, 6, 12, 31):
            for s in (0, 1, 2, 7, 20, 31):
                with self.subTest(k=k, s=s):
                    affine_check(k, s)


if __name__ == '__main__':
    unittest.main()
