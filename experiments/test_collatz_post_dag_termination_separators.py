"""Regression gates for the post-DAG Collatz termination audit.

These are exact finite separators. They deliberately prevent future work from
re-promoting refuted local ranking claims into a global theorem.
"""
import unittest
from fractions import Fraction

import collatz_q0_coalescence_component_audit as base


def cert(word):
    A,B,D=1,0,0
    for r,s,rp in word:
        A,B,D=3**r*A,3**r*B+((1<<s)-1)*(1<<D),D+s+rp
    C=(1<<D)-A
    return A,B,D,C,Fraction(B,C)


class PostDagTerminationSeparators(unittest.TestCase):
    def test_rigid_recharge_discharge_can_expand(self):
        # Source 26863 has a RIGID recharge->drop block at anchor r=1:
        #   m: 38773 -> 73609 -> 55207.
        # Target return words are Q then P.
        Q=((1,1,4),(4,1,1))
        P=((1,1,1),)
        A1,B1,D1,_,_=cert(Q)
        A2,B2,D2,_,_=cert(P)
        A=A2*A1
        B=A2*B1+B2*(1<<D1)
        D=D1+D2
        self.assertEqual((A,D,B),(729,9,467))
        self.assertGreaterEqual(A,1<<D)
        self.assertEqual((A*38773+B)//(1<<D),55207)
        self.assertGreater(55207,38773)
        # The fixed ordinary source still has no direct descent at the
        # endpoints covering this macro.
        self.assertEqual(base.cylinder_status(27,26863)[0],"RIGID")
        self.assertEqual(base.cylinder_status(36,26863)[0],"RIGID")

    def test_concrete_rigid_pattern_cycle_can_expand(self):
        # Source 16937 returns to the same return-pattern node after:
        # flat -> drop -> drop, while m grows 20629 -> 79399.
        W1=((1,1,5),(5,2,1))
        W2=((1,1,2),(2,1,5),(5,1,2),(2,1,1))
        W3=((1,1,1),)
        A,B,D=1,0,0
        for W in (W1,W2,W3):
            a,b,d,_,_=cert(W)
            B=a*B+b*(1<<D)
            A=a*A
            D+=d
        self.assertEqual((A,D,B),(129140163,25,155923841))
        self.assertGreater(A,1<<D)
        self.assertEqual((A*20629+B)//(1<<D),79399)

        # Nevertheless the exact composite return word cannot immediately
        # repeat indefinitely. Its rational fixed point is negative and its
        # exact 2-adic repeat budget at this entry is one.
        C=(1<<D)-A
        q=Fraction(B,C)
        self.assertEqual(q,Fraction(-155923841,95585731))
        p,u=q.numerator,q.denominator
        delta=u*20629-p
        v=(delta & -delta).bit_length()-1
        self.assertEqual(v,26)
        self.assertEqual((v-1)//D,1)

    def test_26863_eventually_direct_descends_but_not_at_macro(self):
        # The expanding macro is real but not divergent: source 26863 first
        # crosses below itself later. This is a separator, not a counterexample
        # to Collatz.
        y=26863
        first=None
        for t in range(1,100):
            y=base.T(y)
            if y<26863:
                first=(t,y);break
        self.assertEqual(first,(42,15527))


if __name__=="__main__":
    unittest.main()
