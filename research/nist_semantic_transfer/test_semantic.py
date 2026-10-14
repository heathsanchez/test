import unittest
from fractions import Fraction as F
from semantic_core import (source_ratio,source_transition_pair,source_hfs,
    source_ratio_compiled_centroid,published_centroid_for_validation_only,RelationUnknown)

# These synthetic source snippets test grammar and target isolation.
# Actual CI must also use both frozen original primary manuscript PDF hashes.
SAMPLE=("The line strengths of the 2S–6P1/2 and 2S–6P3/2 transitions have a 1:2 ratio. "
        "Spectroscopy laser powers have a 2:1 ratio. "
        "By averaging all available data we find "
        "ν1/2 = 730,690,111,486.30(49)stat (49)sys kHz; "
        "= 730,690,111,486.30(69) kHz. "
        "ν3/2 = 730,690,516,650.91(60)stat (28)sys kHz; "
        "= 730,690,516,650.91(66) kHz. "
        "with the hyperfine-structure (HFS) correction ΔνHFS(ν) = "
        "−132,985.25(1) kHz. "
        "Finally, we combine the two transition frequencies into the centroid. "
        "νcentroid = 730,690,248,610.79(48) kHz.")

class SourceGrammar(unittest.TestCase):
    def test_ratio_source_derived(self):
        a,b,w=source_ratio(SAMPLE)
        self.assertEqual((a,b),(F(1,3),F(2,3)))
        self.assertIn("line-strength",w.kind)
    def test_unrelated_laser_2to1_not_selected(self):
        t="Spectroscopy laser powers have a 2:1 ratio. "+SAMPLE
        self.assertEqual(source_ratio(t)[:2],(F(1,3),F(2,3)))
    def test_ratio_swap_changes_executable_consequence(self):
        swapped=SAMPLE.replace("have a 1:2 ratio","have a 2:1 ratio")
        new=source_ratio_compiled_centroid(swapped)["value"]
        old=source_ratio_compiled_centroid(SAMPLE)["value"]
        self.assertNotEqual(new,old)
    def test_measured_values_source_derived(self):
        m=source_transition_pair(SAMPLE)
        self.assertEqual(m["1/2"][0].value,F("730690111486.30"))
        self.assertEqual(m["1/2"][0].sigma,F("0.69"))
        self.assertEqual(m["3/2"][0].value,F("730690516650.91"))
        self.assertEqual(m["3/2"][0].sigma,F("0.66"))
    def test_invalid_missing_measurement_rejected(self):
        s=SAMPLE.replace("ν3/2 = ","νx = ")
        with self.assertRaisesRegex(RelationUnknown,"MEASUREMENT_LABELS"):
            source_transition_pair(s)
    def test_duplicate_measurement_rejected(self):
        source=SAMPLE.replace("ν3/2 = ","ν1/2 = ")
        with self.assertRaises(RelationUnknown):
            source_transition_pair(source)
    def test_missing_combined_sigma_rejected(self):
        s=SAMPLE.replace("= 730,690,516,650.91(66) kHz", "")
        with self.assertRaisesRegex(RelationUnknown,"COMBINED_UNCERTAINTY"):
            source_transition_pair(s)
    def test_hfs_signed_original(self):
        h,w=source_hfs(SAMPLE)
        self.assertEqual(h.value,F("-132985.25"))
        self.assertEqual(h.sigma,F(".01"))
        self.assertIn("signed-hyperfine",w.kind)
    def test_missing_hfs_sign_rejects(self):
        s=SAMPLE.replace("−132,985.25","132,985.25")
        with self.assertRaisesRegex(RelationUnknown,"SIGNED_HFS"):
            source_hfs(s)
    def test_reverse_hfs_sign_changes_result(self):
        s=SAMPLE.replace("−132,985.25","+132,985.25")
        self.assertNotEqual(source_ratio_compiled_centroid(s)["value"],
                            source_ratio_compiled_centroid(SAMPLE)["value"])
    def test_missing_role_rejects(self):
        s=SAMPLE.replace("The line strengths","The mass ratios")
        with self.assertRaisesRegex(RelationUnknown,"SOURCE_RATIO"):
            source_ratio(s)
    def test_zero_ratio_denominator_rejects(self):
        s=SAMPLE.replace("have a 1:2 ratio","have a 0:0 ratio")
        with self.assertRaisesRegex(RelationUnknown,"INVALID_SOURCE_WEIGHT"):
            source_ratio(s)
    def test_source_derived_centroid(self):
        r=source_ratio_compiled_centroid(SAMPLE)
        self.assertEqual(r["value"],F("730690248610.79"))
        self.assertEqual(r["physical_uncertainty"],
                         "UNKNOWN_FULL_COVARIANCE_NOT_INFERRED")
    def test_target_is_not_an_input(self):
        changed=SAMPLE.replace("730,690,248,610.79(48)","730,690,248,610.70(48)")
        self.assertEqual(source_ratio_compiled_centroid(changed)["value"],
                         source_ratio_compiled_centroid(SAMPLE)["value"])
        self.assertNotEqual(published_centroid_for_validation_only(changed)[0],
                            source_ratio_compiled_centroid(changed)["value"])
    def test_target_extraction_for_comparison_only(self):
        value,sigma=published_centroid_for_validation_only(SAMPLE)
        self.assertEqual(value,F("730690248610.79"))
        self.assertEqual(sigma,"48")
    def test_ambiguous_target_rejected(self):
        s=SAMPLE.replace(
            "νcentroid = 730,690,248,610.79(48) kHz.",
            "νcentroid = 730,690,248,610.79(48) kHz. νtwo = 730,690,248,610.79(48) kHz.")
        with self.assertRaisesRegex(RelationUnknown,"AMBIGUOUS_PUBLISHED"):
            published_centroid_for_validation_only(s)

if __name__=="__main__":
    unittest.main()
