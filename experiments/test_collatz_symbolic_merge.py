import unittest
from collatz_symbolic_merge import compile_portfolio, verify_merge, verify_partition


class MergeTests(unittest.TestCase):
    def test_cone_certificates_really_merge(self):
        bank, residual, exceptions = compile_portfolio(12)
        cones = [s for s in bank if s['kind']=='inverse_odd']
        self.assertTrue(cones)
        for s in cones:
            for q in range(s['Q'],s['Q']+4):
                n=2**s['k']*q+s['b']
                if n<=1: continue
                y=3**s['c']*q+s['d'];p=(2*y-1)//3
                self.assertTrue(0<p<n)
                self.assertEqual((3*p+1)//2,y)
        verify_partition(bank,residual)

    def test_forged_threshold_rejected(self):
        bank,_,_=compile_portfolio(12)
        s=next(s for s in bank if s['kind']=='inverse_odd')
        with self.assertRaises(ValueError): verify_merge(dict(s,Q=s['Q']+1))

    def test_forged_residue_rejected(self):
        bank,_,_=compile_portfolio(12)
        s=next(s for s in bank if s['kind']=='inverse_odd')
        with self.assertRaises(ValueError): verify_merge(dict(s,d=s['d']+1))


if __name__=='__main__': unittest.main()
