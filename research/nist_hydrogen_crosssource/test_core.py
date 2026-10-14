import unittest
from fractions import Fraction as F
from consequence_core import (q,canonical,robust_consistency,joint_covariance_diagnostic,
    Ledger,UnknownEvidence,independent_pooled_mean,contrast_measured_predicted,C)

def nature_radius():
    return q("proton_radius","0.8406","0.0015","fm","nature2026","2026qed",("nature-2s6p","1s2s","qed2026","alpha2022"))

def bullis_radius(theory="new"):
    return q("proton_radius","0.8433" if theory=="new" else "0.8422",
        "0.0031","fm","bullis2026",theory,("bullis-2sns","1s2s","qed-"+theory,"alpha2022"))

def nature_rydberg():
    return q("rydberg_constant","10973731.568152","0.000014","m^-1",
             "nature2026","2026qed",("nature-2s6p","1s2s","qed2026","alpha2022"))

def bullis_rydberg():
    return q("rydberg_frequency","3289841960252.9","9.7","kHz",
             "bullis2026","new",("bullis-2sns","1s2s","qed-new","alpha2022"))

def nist_rydberg():
    return q("rydberg_constant","10973731.568157","0.000012","m^-1",
             "nist2022","codata2022",("nist-input-corpus","nist-lsa"))

class Algebra(unittest.TestCase):
    def test_exact_conversion(self):
        x=canonical(nature_rydberg())
        self.assertEqual(x.value,F("10973731.568152")*C/1000)
        self.assertEqual(x.sigma,F("0.000014")*C/1000)
    def test_malformed_unit(self):
        with self.assertRaisesRegex(UnknownEvidence,"UNSUPPORTED_DIMENSION"):
            canonical(q("rydberg_constant","100","1","Hz","a","a",("x",)))
    def test_zero_sigma(self):
        with self.assertRaisesRegex(UnknownEvidence,"INVALID"):
            q("proton_radius","1","0","fm","a","a",("x",))
    def test_duplicate_supports(self):
        with self.assertRaisesRegex(UnknownEvidence,"DUPLICATED"):
            q("proton_radius","1","0.1","fm","a","a",("x","x"))
    def test_rp_cross_papers_all_correlations(self):
        r=robust_consistency(nature_radius(),bullis_radius())
        self.assertEqual(r["verdict"],"WARRANTED_BOUNDED_ROBUST_CONSISTENCY")
        self.assertEqual(F(r["maximum_possible_z"]),F(27,16))
        # Independently brute force over 1001 allowed rational correlations.
        a,b=nature_radius(),bullis_radius()
        for n in range(-500,501):
            rho=F(n,500)
            variance=a.sigma**2+b.sigma**2-2*rho*a.sigma*b.sigma
            self.assertGreater(4*variance,(a.value-b.value)**2)
    def test_rydberg_cross_papers_all_correlations(self):
        r=robust_consistency(nature_rydberg(),bullis_rydberg())
        self.assertEqual(r["verdict"],"WARRANTED_BOUNDED_ROBUST_CONSISTENCY")
        self.assertLess(F(r["maximum_possible_z"]),F(1))
    def test_unknown_historic_cross_covariance(self):
        r=robust_consistency(nature_rydberg(),nist_rydberg())
        self.assertEqual(r["verdict"],"UNKNOWN_CORRELATION_COULD_CHANGE_THRESHOLD_DECISION")
    def test_compatible_rp_old_theory(self):
        self.assertEqual(robust_consistency(nature_radius(),bullis_radius("old"))["verdict"],
                         "WARRANTED_BOUNDED_ROBUST_CONSISTENCY")
    def test_same_event_not_2_independent_theories(self):
        with self.assertRaisesRegex(UnknownEvidence,"SAME_EVIDENCE_EVENT"):
            robust_consistency(bullis_radius(),bullis_radius("old"))
    def test_cross_measurand_rejection(self):
        with self.assertRaisesRegex(UnknownEvidence,"INCOMPATIBLE"):
            robust_consistency(nature_radius(),bullis_rydberg())
    def test_covariance_exact_psd(self):
        r=joint_covariance_diagnostic(F("0.94"))
        self.assertEqual(F(r["correlated_sum_variance"]),F("3.88"))
        self.assertEqual(F(r["covariance_matrix_determinant"]),F("0.1164"))
    def test_missing_rho(self):
        with self.assertRaisesRegex(UnknownEvidence,"UNKNOWN_WITHIN"):
            joint_covariance_diagnostic(None)
    def test_invalid_rho(self):
        with self.assertRaisesRegex(UnknownEvidence,"NON_POSITIVE"):
            joint_covariance_diagnostic(F("1.01"))
    def test_cross_study_fusion_blocked(self):
        with self.assertRaisesRegex(UnknownEvidence,"NO_POOLED_MEAN"):
            independent_pooled_mean(nature_radius(),bullis_radius())
    def test_measured_predicted(self):
        x=q("hydrogen_transition_frequency","730690248610.79","0.48","kHz","nature2026","exp",("nature-2s6p",))
        pred=q("hydrogen_transition_frequency","730690248610.79","0.23","kHz","nature2026","SM",("muonic-radius","1s2s","qed"))
        r=contrast_measured_predicted(x,pred)
        self.assertEqual(F(r["difference_kHz"]),0)
        self.assertEqual(F(r["variance_kHz_sq"]),F("0.2833"))
        self.assertFalse(r["independent_QED_validation"])

class Support(unittest.TestCase):
    def setUp(self):
        self.l=Ledger()
        self.sha_a="a"*64
        self.sha_b="b"*64
    def test_unique_root(self):
        self.assertTrue(self.l.add_event("nature2026",self.sha_a,"https://nature.com/foo"))
        self.assertEqual(self.l.count_events(),1)
        self.assertFalse(self.l.add_event("nature2026",self.sha_a,"https://nature.com/foo"))
        self.assertEqual(self.l.count_events(),1)
    def test_forged_source_alias(self):
        self.l.add_event("nature2026",self.sha_a,"https://nature.com/foo")
        with self.assertRaisesRegex(UnknownEvidence,"SOURCE_ALIAS"):
            self.l.add_event("forged2026",self.sha_a,"https://different.example/")
    def test_changed_source_same_id(self):
        self.l.add_event("nature2026",self.sha_a,"https://nature.com/foo")
        with self.assertRaisesRegex(UnknownEvidence,"CONFLICTING_SOURCE_ID"):
            self.l.add_event("nature2026",self.sha_b,"https://nature.com/foo")
    def test_invalid_source_digest(self):
        with self.assertRaisesRegex(UnknownEvidence,"INVALID_SOURCE"):
            self.l.add_event("a","garbage","https://example.com")
    def test_unqualified_output_source(self):
        with self.assertRaisesRegex(UnknownEvidence,"UNQUALIFIED_SOURCE"):
            self.l.add_product("rp",nature_radius())
    def test_same_event_two_products_are_not_two_events(self):
        self.l.add_event("bullis2026",self.sha_b,"https://arxiv.org/foo")
        self.assertTrue(self.l.add_product("rp_new",bullis_radius()))
        self.assertTrue(self.l.add_product("rp_old",bullis_radius("old")))
        self.assertEqual(self.l.count_events(),1)
        self.assertNotEqual(self.l.products["rp_new"].value,self.l.products["rp_old"].value)
    def test_theory_withdrawal_scope(self):
        self.l.add_event("bullis2026",self.sha_b,"https://arxiv.org/foo")
        self.l.add_product("rp_new",bullis_radius())
        self.l.add_product("rp_old",bullis_radius("old"))
        self.assertTrue(self.l.resolve("rp_new").startswith("WARRANTED"))
        self.l.revoke("qed-new")
        self.assertEqual(self.l.resolve("rp_new"),"UNKNOWN_REVOKED_SUPPORT")
        self.assertTrue(self.l.resolve("rp_old").startswith("WARRANTED"))
        self.l.restore("qed-new")
        self.assertTrue(self.l.resolve("rp_new").startswith("WARRANTED"))
    def test_role_guard(self):
        self.l.add_event("nature2026",self.sha_a,"https://nature.com/foo")
        with self.assertRaisesRegex(UnknownEvidence,"INPUT_NOT_INDEPENDENT"):
            self.l.insert_claim("nature2026","inverse_alpha","FIXED_INPUT")
    def test_duplicate_product_collision(self):
        self.l.add_event("bullis2026",self.sha_b,"https://arxiv.org/foo")
        self.l.add_product("rp",bullis_radius())
        with self.assertRaisesRegex(UnknownEvidence,"CONFLICTING_PRODUCT"):
            self.l.add_product("rp",bullis_radius("old"))

if __name__=="__main__":
    unittest.main()
