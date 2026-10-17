"""V9 acceptance contracts frozen before implementing the next source-native trial.

No target source or protected tests accessed here; original V7 source and
historical negative evidence remain unchanged. A metadata-only role change is
disclosed; withheld Packaging cannot be read before independently selected
training policy. All UNKNOWN outcomes fail closed.
"""
import copy
from pathlib import Path
import unittest

from . import qualify_source_bound_g2_v9 as v9

class FrozenProspectiveV9(unittest.TestCase):
    def test_A01_frozen_two_roles_and_authored_blob_pointers(self):
        p=v9.frozen()
        self.assertEqual([x["role"] for x in p["task_roles"]],["TRAINING","HELDOUT_FUTURE"])
        self.assertEqual([x["repository"] for x in p["task_roles"]],["jd/tenacity","pypa/packaging"])
        self.assertEqual(p["budget"]["search_horizon_per_policy"],8)
        self.assertEqual(p["source_pins"]["original_v104"],
                         "426c54f7c774560e0fabe7213c5ef333b1327c71")
        self.assertEqual(p["frozen_author_test_git_blob_refs"][1]["git_oid"],
                         "e8d51790856a17c4c722692f760ff7b3d30c4762")

    def test_A02_original_pareto_and_v104_pins_not_new_operators(self):
        self.assertEqual(v9.PROTOCOL_SCHEMA,"UDM_V9_SOURCE_BOUND_G2_PROSPECTIVE_FREEZE")
        self.assertEqual(v9.V104_SOURCE,"ORIGINAL_PINNED_V104")
        self.assertEqual(v9.MSI_SOURCE,"ORIGINAL_PINNED_MSI_V10")

    def test_A03_schedule_round_robin_deduplicates_without_outcomes(self):
        orders={"COLD_V104_ORDER":["a","b","c","d"],"MSI_V10:x":["b","e","a","f"],
                "MSI_V10:y":["c","f","e","a"]}
        self.assertEqual(v9.schedule(orders,2),["a","b","c","e","f"])
        self.assertEqual(v9.schedule(orders,2),v9.schedule(dict(reversed(list(orders.items()))),2))

    def test_A04_native_replay_binds_names_and_source_imports(self):
        def native(status):
            return {"status":status,"native_calls":1,"native_exit":0 if status=="PASS_SCOPED_NATIVE" else 1,
                    "required":["tests/test_x.py::test_p"],"executed":["tests/test_x.py::test_p"],
                    "deselected":[],"imported_project_files":["pkg.py"],
                    "typed_manifest_sha256":"f"*64}
        self.assertEqual(v9.replayed(native("FAIL_NATIVE_PROTECTED"),
                                    native("FAIL_NATIVE_PROTECTED")),
                         "VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED")
        self.assertEqual(v9.replayed(native("PASS_SCOPED_NATIVE"),
                                    native("PASS_SCOPED_NATIVE")),
                         "VERIFIED_REPEATED_PASS_SCOPED_NATIVE")

    def test_A05_native_mismatch_never_qualified(self):
        good={"status":"PASS_SCOPED_NATIVE","native_calls":1,"native_exit":0,
              "required":["tests/test_x.py::test_p"],"executed":["tests/test_x.py::test_p"],
              "deselected":[],"imported_project_files":["pkg.py"],
              "typed_manifest_sha256":"f"*64}
        for change in ({"imported_project_files":["other.py"]},{"executed":[]},
                       {"deselected":["tests/test_x.py::test_p"]},
                       {"typed_manifest_sha256":"0"*64},{"native_calls":0},
                       {"native_exit":1},{"status":"UNKNOWN_NATIVE_COLLECTION"}):
            with self.subTest(change=change):
                self.assertEqual(v9.replayed(good,{**good,**change}),"UNKNOWN_NATIVE_EVIDENCE")

    def test_A06_incomplete_profile_remains_unknown(self):
        actual={"a":"VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED",
                "b":"UNKNOWN_NATIVE_EVIDENCE"}
        self.assertIsNone(v9.profile(["a","b"],actual,2))
        self.assertIsNone(v9.profile(["a"],actual,2))
        self.assertEqual(v9.profile(["a","a"],actual,2),[1,4])

    def test_A07_success_and_predecessor_fail_are_needed(self):
        v={"a":"VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED",
           "b":"VERIFIED_REPEATED_PASS_SCOPED_NATIVE"}
        self.assertEqual(v9.profile(["a","b"],v,2),[0,4])
        self.assertEqual(v9.profile(["b","a"],v,2),[0,2])

    def test_A08_training_unknown_must_keep_future_unopened(self):
        self.assertFalse(v9.authorize_future({"status":"UNKNOWN_CHOICE"},"COLD_V104_ORDER"))
        self.assertFalse(v9.authorize_future({"status":"AUTHORIZED_REPAIR",
                                               "selected":"COLD_V104_ORDER"},"COLD_V104_ORDER"))
        self.assertTrue(v9.authorize_future({"status":"AUTHORIZED_REPAIR",
                                              "selected":"MSI_V10:x"},"COLD_V104_ORDER"))

    def test_A09_future_cannot_claim_G2_by_executable_detection_alone(self):
        receipt={"cold_profile":[1,16],"selected_profile":[0,2],
                 "removal_replayed":False,"restoration_replayed":False}
        self.assertEqual(v9.g2_verdict(receipt),"UNKNOWN")
        receipt.update(removal_replayed=True,restoration_replayed=True,
                       physical_program_removed=True, independent_future_native=True)
        self.assertEqual(v9.g2_verdict(receipt),"WARRANTED_BOUNDED_PROSPECTIVE_G2")

    def test_A10_all_other_claims_remain_unqualified(self):
        self.assertEqual(v9.G3,"UNKNOWN")
        self.assertEqual(v9.G4,"UNKNOWN")
        self.assertEqual(v9.G5,"UNKNOWN")
        self.assertEqual(v9.G6,"UNKNOWN")


if __name__=="__main__":
    unittest.main()
