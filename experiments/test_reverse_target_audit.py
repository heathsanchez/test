import unittest
from collatz_reverse_predecessor_tree import reverse_apply
from collatz_reverse_target_audit import enumerate_target

class TargetTests(unittest.TestCase):
    def test_continue_past_first_contraction(self):
        # At endpoint 13 and original source 11, EOO reaches 11 (not <11).
        # EOOO reaches 7 (<11). First-contraction pruning loses this exit.
        self.assertEqual(reverse_apply(13, 'EOO'),11)
        self.assertEqual(reverse_apply(13, 'EOOO'),7)
        certs=enumerate_target(3)
        self.assertIn('EOOO', {c.word for c in certs})

class CompletenessTests(unittest.TestCase):
    def test_small_budget_exhaustive_word_sets(self):
        from itertools import product
        for Q in range(1,7):
            limit=(3*3**Q//4).bit_length()-1
            brute=set()
            for depth in range(1,limit+1):
                for chars in product('EO',repeat=depth):
                    odds=0; first=None
                    for k,ch in enumerate(chars,1):
                        odds+=ch=='O'
                        if first is None and 4*2**k <= 3*3**odds:
                            first=k
                    if odds<=Q and first==depth: brute.add(''.join(chars))
            self.assertEqual({c.word for c in enumerate_target(Q)},brute)

    def test_one_residue_is_not_covered(self):
        for Q in range(1,11):
            self.assertTrue(all(c.residue != 1 % c.d for c in enumerate_target(Q)))

    def test_legacy_q7_retained(self):
        from collatz_reverse_predecessor_tree import enumerate_first_contractions
        cs=enumerate_first_contractions(7)
        killed={r for c in cs for r in range(c.residue,3**7,c.d)}
        self.assertEqual(len(cs),41)
        self.assertEqual(len(killed),1013)

    def test_target_checks_original_source(self):
        from collatz_reverse_predecessor_tree import T
        for c in enumerate_target(5):
            first=c.residue or c.d
            for lift in range(5):
                y=first+lift*c.d
                p=reverse_apply(y,c.word)
                n=3*y//4+1
                self.assertGreater(p,0)
                self.assertLess(p,n)
                z=p
                for _ in c.word:z=T(z)
                self.assertEqual(z,y)

    def test_mod24_overcompression_separator(self):
        from collatz_reverse_predecessor_tree import T
        y=19
        self.assertEqual((y%3,y%2,T(y)%2),(1,1,1))
        self.assertEqual(y%12,7)
        self.assertNotEqual(y%24,7)

    def test_invalid_budget(self):
        for Q in (0,15,-1,True):
            with self.assertRaises(ValueError):enumerate_target(Q)

    def test_invalid_target(self):
        for num,den in ((0,4),(4,4),(5,4)):
            with self.assertRaises(ValueError):enumerate_target(4,num,den)

if __name__=='__main__': unittest.main()
