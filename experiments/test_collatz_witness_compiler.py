import importlib.util
import pathlib
import unittest

class WitnessTests(unittest.TestCase):
    def test_compiler_exists(self):
        self.assertTrue(pathlib.Path(__file__).with_name('collatz_witness_compiler.py').exists(),
                        'Exact witness compiler has not been implemented')

    def test_sound_transfer_and_reject_forgery(self):
        p = pathlib.Path(__file__).with_name('collatz_witness_compiler.py')
        if not p.exists(): self.skipTest('compiler absent')
        spec = importlib.util.spec_from_file_location('compiler',p)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        # T^6(3)=2. Same parity cylinder is 3 modulo 64.
        rule = m.compile_rule(3,6)
        self.assertEqual(rule, (6,3,27,47,2))
        for q in (0,1,2,100,10**30):
            n = 3+64*q
            self.assertTrue(m.applies(rule,n))
            x=n
            for _ in range(6): x=m.step(x)
            self.assertEqual(x,(27*n+47)//64)
            self.assertLess(x,n)
        self.assertFalse(m.applies(rule,7))
        self.assertFalse(m.applies(rule,1))
        self.assertEqual(m.first_descent(3,100),[3,5,8,4,2])
        self.assertIsNone(m.first_descent(27,10))
        with self.assertRaises(ValueError): m.compile_rule(1,2)
        self.assertTrue(m.validate_rule(rule))
        self.assertFalse(m.validate_rule((6,3,27,23,2)))
        self.assertFalse(m.validate_rule((6,3,27,47,1)))

if __name__=='__main__': unittest.main()
