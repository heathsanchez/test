import copy
import unittest
from fractions import Fraction as F
from affine_core import (Datum, SourceParseFailure, table_rows, linear_map,
                         independent_variance, reproduce_table, holdout_centroid,
                         parse_explicit_entries)
# Synthetic surrogate for signed numeric structure of original published Table I.
# Qualifier must separately parse original SHA-locked publisher-derived PDF.
SYNTHETIC_TABLE="""TABLE I. Systematic corrections to the 2S-nS transitions
All values are given in kHz.
ac Stark shift corrected     770 649 350 002.60(1.90)     781 432 010 264.30(1.89)     789 144 778 098.87(2.05)
dc Stark shift              -1.30(0.17)                   -2.90(0.40)                    -5.89(0.83)
Second-order Doppler shift   0.74(0.10)                    0.75(0.10)                     0.76(0.10)
Blackbody radiation         -0.39(0.02)                   -0.76(0.03)                    -1.07(0.04)
Extrapolation nonlinearity   0.00(0.10)                    0.00(0.10)                     0.00(0.10)
Photodiode imperfections     0.00(0.28)                    0.00(0.28)                     0.00(0.28)
Frequency calibration        0.00(0.08)                    0.00(0.08)                     0.00(0.08)
ac Stark canceling laser stability 0.00(0.03)              0.00(0.03)                     0.00(0.03)
Final measured value         770 649 350 001.65(1.94)     781 432 010 261.39(1.96)     789 144 778 092.67(2.24)
"""
NATURE_EQ_SAMPLES="730,690,111,486.30 730,690,516,650.91 730,690,248,610.79 132,985.25"

class NumericCore(unittest.TestCase):
    def test_signed_three_column_parser(self):
        self.assertEqual(parse_explicit_entries("-2.90(0.40) 0.74(0.10) −1.07(0.04)"),
                         [Datum(F("-2.90"),F("0.40")),
                          Datum(F("0.74"),F("0.10")),
                          Datum(F("-1.07"),F("0.04"))])
    def test_table_has_all_nine_rows(self):
        self.assertEqual(len(table_rows(SYNTHETIC_TABLE)),9)
    def test_table_three_columns_per_row(self):
        self.assertTrue(all(len(values)==3 for _,values in table_rows(SYNTHETIC_TABLE)))
    def test_three_bullis_exact_values(self):
        r=reproduce_table(table_rows(SYNTHETIC_TABLE))
        self.assertTrue(all(x["exact_value_match"] for x in r))
    def test_bullis_uncertainties_display_precision(self):
        r=reproduce_table(table_rows(SYNTHETIC_TABLE))
        self.assertTrue(all(x["rss_rounded_sigma_match"] for x in r))
    def test_rounded_error_rejects_forgery(self):
        text=SYNTHETIC_TABLE.replace("770 649 350 001.65(1.94)","770 649 350 001.65(1.64)")
        self.assertFalse(reproduce_table(table_rows(text))[0]["rss_rounded_sigma_match"])
    def test_missing_one_correction(self):
        text="\n".join(t for t in SYNTHETIC_TABLE.splitlines()
                       if not t.startswith("Second-order Doppler shift"))
        with self.assertRaisesRegex(SourceParseFailure,"MISSING_OR_DUPLICATE"):
            table_rows(text)
    def test_double_correction_not_two_observations(self):
        lines=SYNTHETIC_TABLE.splitlines()
        target=next(i for i,line in enumerate(lines) if line.startswith("Blackbody radiation"))
        lines.insert(target,lines[target])
        with self.assertRaisesRegex(SourceParseFailure,"MISSING_OR_DUPLICATE"):
            table_rows("\n".join(lines))
    def test_wrong_sign_breaks_reproduction(self):
        t=SYNTHETIC_TABLE.replace("dc Stark shift              -1.30", "dc Stark shift              +1.30")
        self.assertFalse(reproduce_table(table_rows(t))[0]["exact_value_match"])
    def test_scramble_one_column_breaks_reproduction(self):
        t=SYNTHETIC_TABLE.replace(
              "0.74(0.10)                    0.75(0.10)",
              "0.75(0.10)                    0.74(0.10)")
        self.assertFalse(all(r["exact_value_match"] for r in reproduce_table(table_rows(t))))
    def test_hacked_target_detected(self):
        t=SYNTHETIC_TABLE.replace("789 144 778 092.67","789 144 778 092.66")
        self.assertFalse(reproduce_table(table_rows(t))[2]["exact_value_match"])
    def test_missing_final_row_unknown(self):
        t=SYNTHETIC_TABLE.replace("Final measured value", "No declared final line")
        with self.assertRaisesRegex(SourceParseFailure,"FINAL_ROW_IDENTITY_MISMATCH"):
            table_rows(t)
    def test_missing_heading_unknown(self):
        with self.assertRaisesRegex(SourceParseFailure,"HEADING"):
            table_rows(SYNTHETIC_TABLE.replace("TABLE I. Systematic corrections","Removed headline"))
    def test_malformed_two_column_row_unknown(self):
        t=SYNTHETIC_TABLE.replace("Photodiode imperfections     0.00(0.28)                    0.00(0.28)                     0.00(0.28)",
                                  "Photodiode imperfections     0.00(0.28)                    0.00(0.28)")
        with self.assertRaisesRegex(SourceParseFailure,"MALFORMED"):
            table_rows(t)
    def test_affine_general_three_factors(self):
        vals=[Datum(F(1),F(1)),Datum(F(6),F(2)),Datum(F(3),F(1))]
        self.assertEqual(linear_map(vals,[F(1,3),F(2,3),-1]),F(4,3))
    def test_affine_arity_guard(self):
        with self.assertRaisesRegex(SourceParseFailure,"ARITY"):
            linear_map([Datum(F(1),F(1))],[F(1),F(2)])
    def test_uncertainty_fail_closed(self):
        with self.assertRaisesRegex(SourceParseFailure,"UNKNOWN_COVARIANCE"):
            independent_variance([Datum(F(1),F(1))],[1])
    def test_reported_nature_centroid(self):
        self.assertEqual(holdout_centroid(NATURE_EQ_SAMPLES)["exact_centroid"],
                         str(F("730690248610.79")))
    def test_nature_sigma_remains_unknown(self):
        self.assertEqual(holdout_centroid(NATURE_EQ_SAMPLES)["reconstruct_reported_sigma"],
                         "UNKNOWN_CORRELATION_BETWEEN_TERMS")
    def test_nature_missing_observation_fail(self):
        with self.assertRaisesRegex(SourceParseFailure,"ANCHOR"):
            holdout_centroid(NATURE_EQ_SAMPLES.replace("730,690,111,486.30","0"))
    def test_nature_corrupted_target_fail(self):
        with self.assertRaisesRegex(SourceParseFailure,"ANCHOR"):
            holdout_centroid(NATURE_EQ_SAMPLES.replace("730,690,248,610.79","730,690,248,610.78"))

if __name__=="__main__":
    unittest.main()
