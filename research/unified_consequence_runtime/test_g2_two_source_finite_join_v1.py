"""Frozen adversarial contracts for source-native two-project finite join certificate.

Finitary unit controls only: no theorem about arbitrary original source.
"""
import unittest

from . import g2_two_source_finite_join_v1 as model

MISTRAL=(0,4,2,6,8,12,10,14,1,5,3,7,9,13,11,15)
DEER=(5,7,13,15)


class FrozenTwoSourceFiniteJoin(unittest.TestCase):
    def test_01_mistral_all_ordered_pairs_are_union(self):
        r=model.validate_masks(MISTRAL,4,4)
        self.assertEqual(r["pairwise_join_pairs"],256)
        self.assertEqual(r["necessary_edits"],4)
        self.assertEqual(r["all_pass_mask"],15)

    def test_02_deer_all_ordered_pairs_are_union(self):
        r=model.validate_masks(DEER,2,4)
        self.assertEqual(r["pairwise_join_pairs"],16)
        self.assertEqual(r["necessary_edits"],2)
        self.assertEqual(r["original_pass_mask"],5)

    def test_03_missing_subset_refused(self):
        with self.assertRaises(ValueError):
            model.validate_masks(MISTRAL[:-1],4,4)

    def test_04_non_join_homomorphic_mask_refused(self):
        wrong=list(MISTRAL)
        wrong[3]=wrong[3]|8
        with self.assertRaises(ValueError):
            model.validate_masks(wrong,4,4)

    def test_05_superfluous_edit_refused(self):
        with self.assertRaises(ValueError):
            model.validate_masks((0,1,0,1),2,1)

    def test_06_incomplete_repaired_future_refused(self):
        wrong=list(MISTRAL);wrong[-1]=14
        with self.assertRaises(ValueError):
            model.validate_masks(wrong,4,4)

    def test_07_no_original_failing_obligation_refused(self):
        with self.assertRaises(ValueError):
            model.validate_masks((1,1),1,1)

    def test_08_noninteger_and_out_of_domain_masks_refused(self):
        for rows in [(5.0,7,13,15),(5,7,13,16),("5",7,13,15)]:
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                model.validate_masks(rows,2,4)

    def test_09_new_law_not_the_same_as_preserving_only_final(self):
        # A bogus improvement/regression profile can end all PASS but is not a join law.
        with self.assertRaises(ValueError):
            model.validate_masks((0,3,2,3),2,2)

    def test_10_proof_source_declares_all_obligations_and_no_sorry(self):
        lean=model.render_lean({"MISTRAL":{"pass_masks":list(MISTRAL),"edits":4,"cases":4},
                                "DEERFLOW":{"pass_masks":list(DEER),"edits":2,"cases":4}})
        self.assertIn("MISTRALJoinAllOrderedPairs",lean)
        self.assertIn("DEERFLOWJoinAllOrderedPairs",lean)
        self.assertIn("EveryEditNecessary",lean)
        self.assertNotIn("sorry",lean)
        self.assertNotIn("axiom",lean.lower())


    def test_11_deer_source_nested_native_receipt_counts_are_authoritative(self):
        import hashlib
        import tempfile
        from pathlib import Path
        raw=(b'<?xml version="1.0"?><testsuite>'
             b'<testcase classname="mod.Tests" name="case[a]"/>'
             b'<testcase classname="mod.Tests" name="case[b]"><failure/></testcase>'
             b'</testsuite>')
        receipt={"junit_sha256":hashlib.sha256(raw).hexdigest(),
                 "counts":{"tests":2,"failures":1,"errors":0,"skipped":0},
                 "returncode":1}
        expected={"mod.Tests::case[a]":"PASS","mod.Tests::case[b]":"FAIL"}
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            (folder/"mask.xml").write_bytes(raw)
            result=model.receipt_vector(folder,"mask.xml",receipt,expected,
                                        "deer_protected",is_mistral=False)
            self.assertEqual(result,expected)


if __name__=="__main__":
    unittest.main()
