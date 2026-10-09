"""Adversarial qualification for Collatz ROS V123 persistent research controller."""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from research.collatz_ros_future_controller_v123 import (
    BASE_RUNS, Controller, bootstrap, compose, digest, dump,
    fixed_F27_no_smaller_preimage, from_file, ghost_prefix, initial_state,
    iterate, make_join, verify_earliest_source27, verify_join,
)


class StatefulWarrantTests(unittest.TestCase):
    def setUp(self):
        self.c = bootstrap()

    def test_only_qualified_class_merger_changes_protected_status(self):
        self.assertEqual(self.c.state["objective"],
            "exclude_second_positive_future_coalescence_class")
        self.assertEqual(self.c.state["global_collatz"], "UNKNOWN")
        self.assertIs(self.c.state["qed"], False)
        self.assertIs(self.c.state["universal_event_producer_proved"], False)
        self.assertEqual(self.c.status(27)["status"], "WARRANTED_BOUNDED_LOWER_MERGE")
        self.assertEqual(self.c.status(27)["source_clock"], 59)
        self.assertEqual(self.c.status(27)["earlier"], 23)
        self.assertEqual(self.c.status(3)["earlier"], 2)
        self.assertEqual(self.c.status(11)["earlier"], 3)

    def test_grammar_unknown_is_not_a_mathematical_counterexample(self):
        old = Controller(initial_state())
        self.assertEqual(old.state["grammar"]["active"], "FIXED_F_SOURCE")
        self.assertEqual(old.status(27)["status"], "UNKNOWN_UNDER_CURRENT_WARRANTS")
        negative = fixed_F27_no_smaller_preimage()
        self.assertEqual(negative["target"], 83)
        self.assertEqual(negative["max_reachable_from_any_smaller_source"], 80)
        self.assertEqual(negative["verdict"], "EXCLUDED_ONLY_FOR_THIS_FIXED_ENDPOINT")
        self.assertTrue(old.refine())
        self.assertFalse(old.refine())
        self.assertEqual(old.status(27)["status"], "UNKNOWN_UNDER_CURRENT_WARRANTS")
        self.assertIn("FIXED_F_SOURCE", old.state["grammar"]["rejected_as_complete"])

    def test_source27_exact_earliest_join_is_stricter_than_F_target_failure(self):
        verify_earliest_source27()
        for w in self.c.state["joins"]:
            if w["source"] == 27:
                self.assertEqual((w["earlier"], w["source_clock"],
                                  w["earlier_clock"], w["common"]), (23, 59, 0, 23))
        self.assertEqual(iterate(27, 59), 23)
        self.assertNotEqual(iterate(27, 58), 23)

    def test_real_asynchronous_phase_and_compiled_consequence(self):
        self.assertEqual(iterate(11, 6), iterate(3, 1))
        self.assertEqual(iterate(11, 6), 5)
        self.assertNotEqual(iterate(3, 6), iterate(11, 6))
        for k in range(64):
            self.assertNotEqual(iterate(3, k), iterate(11, k))
        one = next(j for j in self.c.state["joins"]
                   if (j["source"], j["earlier"]) == (11, 3))
        two = next(j for j in self.c.state["joins"]
                   if (j["source"], j["earlier"]) == (3, 2))
        z = compose(one, two)
        self.assertEqual((z["source"], z["earlier"], z["source_clock"],
                          z["earlier_clock"], z["common"]), (11, 2, 10, 1, 1))
        self.assertEqual(z["parents"], [one["id"], two["id"]])
        self.assertEqual(self.c.reclose(), 0)  # never pay twice

    def test_persistence_restart_integrity_and_idempotence(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "state.json"
            hash1 = dump(self.c, path)
            restored = from_file(path)
            hash2 = dump(restored, path)
            self.assertEqual(hash1, hash2)
            self.assertEqual(json.loads(path.read_text()), self.c.state)
            self.assertFalse(restored.refine())
            self.assertEqual(restored.reclose(), 0)
            self.assertEqual(hash1, digest(restored.state))

    def test_corrupted_cached_result_is_not_warrant(self):
        s = deepcopy(self.c.state)
        w = next(z for z in s["joins"] if z["source"] == 27)
        w["source_clock"] = 58
        with self.assertRaises(ValueError):
            Controller(s)
        s = deepcopy(self.c.state)
        s["joins"][0]["common"] = 1234567
        with self.assertRaises(ValueError):
            Controller(s)
        s = deepcopy(self.c.state)
        s["global_collatz"] = "TRUE"
        with self.assertRaises(ValueError):
            Controller(s)

    def test_source_guard_and_lineage_cannot_be_fabricated(self):
        with self.assertRaises(ValueError):
            make_join(27, 27, 59, 59, "v122_exact_first_join_27",
                      "CIRCULAR_IDENTITY")
        with self.assertRaises(ValueError):
            make_join(11, 0, 6, 1, "v123_bounded_arithmetic", "NONPOSITIVE")
        with self.assertRaises(ValueError):
            make_join(11, 3, 6, 0, "v123_bounded_arithmetic", "WRONG_CLOCK")
        fake = make_join(11, 3, 6, 1, "fictional_run", "FAKE_SUPPORT")
        with self.assertRaises(ValueError):
            self.c.add(fake)

    def test_revocation_reopens_only_proof_dependent_claims(self):
        removed = self.c.revoke("v122_exact_first_join_27")
        self.assertEqual(removed, 1)
        self.assertEqual(self.c.status(27)["status"],
                         "UNKNOWN_UNDER_CURRENT_WARRANTS")
        self.assertEqual(self.c.status(11)["earlier"], 3)
        self.assertEqual(self.c.revoke("v122_exact_first_join_27"), 0)
        self.assertEqual(len([w for w in self.c.state["archived_joins"]
                              if w["source"] == 27]), 1)
        self.c.audit()

    def test_dependency_revocation_propagates_through_composed_warrant(self):
        removed = self.c.revoke("v123_bounded_arithmetic")
        self.assertEqual(removed, 3)
        self.assertEqual(self.c.status(27)["earlier"], 23)
        self.assertEqual(self.c.status(11)["status"],
                         "UNKNOWN_UNDER_CURRENT_WARRANTS")
        self.c.audit()

    def test_no_false_infinite_natural_from_adic_ghosts(self):
        for k in (4, 20, 80, 128):
            x = ghost_prefix(k)
            self.assertTrue(x["cannot_infer_positive_infinite_survivor"])
            self.assertEqual(x["changing_source"], (1 << k) - 1)
            self.assertEqual(x["type"],
                "FINITE_POSITIVE_SHADOW_OF_NEGATIVE_2ADIC_FIXED_POINT")
        self.assertNotIn("COUNTEREXAMPLE",
                         json.dumps(self.c.state["negative_controls"]).upper())

    def test_all_external_sources_are_explicitly_scoped(self):
        self.assertEqual(self.c.state["support"]["v66_future_quotient"]["run"], 36840670599)
        self.assertEqual(self.c.state["support"]["v121_no_fixed_F27"]["run"], 37975109424)
        self.assertEqual(self.c.state["support"]["v122_exact_first_join_27"]["run"], 37975443683)
        self.assertEqual(self.c.state["support"]["v123_bounded_arithmetic"]["status"],
                         "BOUNDED_EXACT")
        for w in self.c.state["joins"]:
            self.assertIn(w["support"], BASE_RUNS)


if __name__ == "__main__":
    unittest.main()
