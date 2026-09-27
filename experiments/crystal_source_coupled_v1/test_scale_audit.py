"""Independent regression contracts for scale and semantic qualification."""
import unittest
import crystal_source_coupled as c


def direct(x):
    return (x // 2) if (x & 1) == 0 else (3*x+1)//2


def oracle(n,h):
    result={}
    for p in range(1,n):
        x=p
        for r in range(h+1):
            result.setdefault(x,(p,r))
            x=direct(x)
    return result


class ScaleAuditTests(unittest.TestCase):
    def index_type(self):
        self.assertTrue(hasattr(c,'SharedBasin'), 'shared bounded-basin implementation absent')
        return c.SharedBasin

    def test_exact_index_matches_independent_oracle(self):
        cls=self.index_type()
        for h in (0,1,2,4,16,64):
            index=cls(128,h)
            for n in range(2,129):
                expected=oracle(n,h)
                actual={y:w for y,w in index.witnesses.items() if w[0]<n}
                self.assertEqual(actual,expected,(n,h))

    def test_every_index_witness_replays(self):
        index=self.index_type()(1000,64)
        for y,(p,r) in index.witnesses.items():
            x=p
            for _ in range(r): x=direct(x)
            self.assertEqual(x,y)
            self.assertLessEqual(r,64)

    def test_index_never_uses_original_or_larger_source(self):
        index=self.index_type()(128,64)
        self.assertIsNone(index.witness(27,71))
        self.assertIsNone(index.witness(27,107))
        self.assertEqual(index.witness(28,71),(27,5))

    def test_reuse_avoids_replaying_all_suffixes(self):
        index=self.index_type()(1000,64)
        self.assertLess(index.stats['expanded_states'],1000*65//2)
        self.assertGreater(index.stats['dominated_suffixes'],0)

    def test_exit_before_zero_tail_is_not_forgotten(self):
        self.assertEqual(c.build_records([6],post=8,future=8,reverse=0),[])

    def test_constant_label_control_refuses_quotient_promotion(self):
        self.assertTrue(hasattr(c,'classification_audit'), 'constant-label control absent')
        rows=c.actual_trace(27,6)
        rec=[(27,rows[k],('EXIT',)) for k in (5,6)]
        result=c.classification_audit(rec)
        self.assertEqual(result['constant_classes'],1)
        self.assertEqual(result['constant_impure_classes'],0)
        self.assertFalse(result['informative_for_quotient'])
        self.assertFalse(result['rank_certified'])

    def test_source27_exact_rank_separator(self):
        self.assertTrue(hasattr(c,'rank_separator'), 'exact finite-invariant audit absent')
        result=c.rank_separator()
        self.assertEqual(result['endpoints'],[71,107])
        self.assertEqual(result['coarse_keys'],[[1,2],[1,2]])
        self.assertTrue(result['both_no_exit_certified'])
        self.assertTrue(result['strict_coarse_rank_rejected'])
        self.assertEqual(len(result['invariant']),34)

    def test_corrupted_finite_invariant_is_rejected(self):
        self.assertTrue(hasattr(c,'verify_finite_exclusion'), 'finite-invariant verifier absent')
        inv=set(range(1,27))|{29,32,35,38,40,44,53,80}
        self.assertTrue(c.verify_finite_exclusion(27,[71,107],inv))
        self.assertFalse(c.verify_finite_exclusion(27,[71,107],inv-{80}))
        self.assertFalse(c.verify_finite_exclusion(27,[71,107],inv|{71}))

if __name__=='__main__': unittest.main(verbosity=2)
