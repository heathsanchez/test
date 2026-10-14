import unittest
from fractions import Fraction as F
from decimal import Decimal
from rounding_envelope import (
  e,Unknown,UncertainComponent,ReportedEstimate,rounded_covariance_envelope,
  nature,qattan_first,qattan_second,qattan_magnetic,
  unsafe_midpoint_only,independent_decimal_check)

class RoundingAndUnknownCovariance(unittest.TestCase):
    def test_first_fit_naive_looks_over_two(self):
        self.assertGreater(unsafe_midpoint_only(nature(),qattan_first()),2)
    def test_first_fit_correctly_stays_unknown(self):
        r=rounded_covariance_envelope(nature(),qattan_first())
        self.assertEqual(r["verdict"],"UNKNOWN_UNDER_ROUNDING_OR_COVARIANCE")
        self.assertEqual(F(r["guaranteed_z_lower"]),F(257,151))
        self.assertEqual(F(r["gap_lower_fm_exact"]),F("0.01285"))
        self.assertEqual(F(r["difference_sigma_upper_fm_exact"]),F("0.00755"))
    def test_second_fit_robust_even_to_rounding_and_every_covariance(self):
        r=rounded_covariance_envelope(nature(),qattan_second())
        self.assertEqual(r["verdict"],"WARRANTED_BOUNDED_ROUNDING_COVARIANCE_ROBUST_2SIGMA_TENSION")
        self.assertEqual(F(r["guaranteed_z_lower"]),F(197,91))
        self.assertGreater(F(r["gap_lower_fm_exact"]),2*F(r["difference_sigma_upper_fm_exact"]))
    def test_decimal_reference_matches_rational(self):
        for candidate in (qattan_first(),qattan_second()):
            got=rounded_covariance_envelope(nature(),candidate)
            baseline=independent_decimal_check(nature(),candidate)
            diff=abs(baseline-Decimal(F(got["guaranteed_z_lower"]).numerator)/Decimal(F(got["guaranteed_z_lower"]).denominator))
            self.assertLess(diff,Decimal("1e-45"))
    def test_comparison_order_invariant(self):
        for f in [qattan_first,qattan_second]:
            a=rounded_covariance_envelope(nature(),f())
            b=rounded_covariance_envelope(f(),nature())
            self.assertEqual(a["guaranteed_z_lower"],b["guaranteed_z_lower"])
    def test_magnetic_is_not_electric(self):
        with self.assertRaisesRegex(Unknown,"MEASURAND_MISMATCH"):
            rounded_covariance_envelope(nature(),qattan_magnetic())
    def test_same_2012_2015_data_cannot_be_independent(self):
        with self.assertRaisesRegex(Unknown,"SAME_UNDERLYING_DATA"):
            rounded_covariance_envelope(qattan_first(),qattan_second())
    def test_absent_rounding_metadata_fails_closed(self):
        with self.assertRaisesRegex(Unknown,"MISSING_PRECISION_METADATA"):
            e("bad","proton_electric_charge_radius",".854","0",[("stat",".002",".001")],["s"],"s","m")
    def test_missing_uncertainties_fails_closed(self):
        with self.assertRaisesRegex(Unknown,"MISSING_UNCERTAINTY"):
            e("bad","proton_electric_charge_radius",".854",".001",[],["s"],"s","m")
    def test_unit_mismatch(self):
        wrong=e("bad","proton_electric_charge_radius",".854",".001",[("stat",".002",".001")],["s"],"s","m","pm")
        with self.assertRaisesRegex(Unknown,"UNIT_MISMATCH"):
            rounded_covariance_envelope(nature(),wrong)
    def test_duplicate_raw_dataset_ids(self):
        with self.assertRaisesRegex(Unknown,"DUPLICATE_ORIGINAL_ROOTS"):
            e("bad","proton_electric_charge_radius",".854",".001",[("stat",".002",".001")],["s","s"],"s","m")
    def test_invalid_component_uncertainty_or_quantum(self):
        for s,q in (("-0.1",".001"),(".002","0")):
            with self.assertRaisesRegex(Unknown,"INVALID_UNCERTAINTY"):
                UncertainComponent("x",F(s),F(q))
    def test_negative_control_larger_uncertainty_requires_unknown(self):
        q=qattan_second()
        wide=e(q.claim_id,q.kind,str(q.center),str(q.center_displayed_quantum),
              [("stat",".001",".010"),("sys",".001",".010")],
              q.original_data_roots,q.source_id,q.method_id)
        self.assertEqual(rounded_covariance_envelope(nature(),wide)["verdict"],
                         "UNKNOWN_UNDER_ROUNDING_OR_COVARIANCE")
    def test_malformed_claim_is_not_an_experiment(self):
        # Qattan's two method products carry same raw data roots.
        self.assertEqual(qattan_first().original_data_roots,qattan_second().original_data_roots)
        self.assertEqual(qattan_first().source_id,qattan_second().source_id)

if __name__=="__main__":
    unittest.main()
