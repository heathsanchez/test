"""V140 adversarial checks for proof-scoped FIXED-CLOCK residual decisions.

The decider may classify a local positive source-relative chart. It
cannot amend the active V134 LowerMerge ledger, invent a Collatz
counterexample, or promote a generic conditional formal theorem to
an unconditional source-specific proof.
"""
import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from research.collatz_ros_fixed_clock_v140 import (
    PAIRS,PARENT_PATH,PARENT_EXPECTED_SHA,PARENT_GIT_BLOB_SHA,PINS,SCHEMA,
    bootstrap,audit,classify,write,digest,
)

class FixedClockROSDecisionTests(unittest.TestCase):
    def setUp(self):
        self.raw=PARENT_PATH.read_bytes()
        self.state=bootstrap()

    def test_read_only_parent_exact_sha_and_full_warrant_ledger(self):
        self.assertEqual(digest(json.loads(self.raw)),PARENT_EXPECTED_SHA)
        header=("blob "+str(len(self.raw))).encode()+bytes([0])
        self.assertEqual(hashlib.sha1(header+self.raw).hexdigest(),PARENT_GIT_BLOB_SHA)
        self.assertEqual(len(json.loads(self.raw)["joins"]),17)
        self.assertEqual(json.loads(self.raw)["negative_controls"][2]["changing_source"],2**80-1)
        self.assertEqual(self.state["parent"]["mutated"],False)
        self.assertEqual(self.state["parent"]["parent_claim_count"],17)
        self.assertEqual(self.state["schema"],SCHEMA)
        self.assertFalse(self.state["qed"])
        self.assertFalse(self.state["universal_event_producer_proved"])
        self.assertEqual(self.state["global_collatz"],"UNKNOWN")
        self.assertEqual(self.raw,PARENT_PATH.read_bytes())

    def test_formal_sources_must_match_declared_scopes(self):
        self.assertEqual(self.state["proof_authorities"],PINS)
        self.assertEqual(PINS["V137_MULTIPLIER_IFF"]["run"],37995061222)
        self.assertEqual(PINS["V139_SUFFIX_INVARIANCE"]["run"],37995933736)
        self.assertEqual(PINS["V136_REDUCED_COEFFICIENTS"]["run"],37994631045)
        self.assertEqual(PINS["V131_GENERIC_SOUNDNESS"]["run"],37986167263)

    def test_complete_bad_fixed_clock_without_fake_collatz_counterexample(self):
        x=classify(5,3,3,8)
        self.assertEqual(x["status"],"FIXED_CLOCK_MATCHED_COEFFICIENT_GRAMMAR_IMPOSSIBLE")
        self.assertEqual(x["source_endpoint"],x["earlier_endpoint"])
        self.assertEqual((x["source_odd_count"],x["earlier_odd_count"]),(1,4))
        self.assertEqual((x["primitive_source_multiplier"],x["primitive_earlier_multiplier"]),(27,1))
        self.assertEqual((x["original_source_slope"],x["earlier_source_slope"]),(216,256))
        self.assertFalse(x["candidate_multiplier_exists"])
        self.assertTrue(x["not_a_Collatz_counterexample"])
        self.assertIn("V139_SUFFIX_INVARIANCE",x["proof_authority"])
        self.assertEqual(x["global_collatz"],"UNKNOWN")

    def test_good_asynchronous_phase_from_same_pair_is_admitted(self):
        x=classify(5,3,1,2)
        self.assertEqual(x["status"],"ADMISSIBLE_PRIMITIVE_FULL_OFFSET_CHART")
        self.assertEqual((x["primitive_source_multiplier"],x["primitive_earlier_multiplier"]),(3,1))
        self.assertEqual((x["original_source_slope"],x["earlier_source_slope"]),(6,4))
        self.assertEqual(x["common_endpoint_intercept"],8)
        self.assertTrue(x["candidate_multiplier_exists"])
        self.assertFalse(x["individual_chart_formally_reified"])
        self.assertEqual(x["global_collatz"],"UNKNOWN")

    def test_neither_integer_multiplier_search_nor_common_waiting_rescues_bad_pair(self):
        for k in range(81):
            negative=classify(5,3,3+k,8+k)
            positive=classify(5,3,1+k,2+k)
            self.assertEqual(negative["status"],"FIXED_CLOCK_MATCHED_COEFFICIENT_GRAMMAR_IMPOSSIBLE")
            self.assertEqual(positive["status"],"ADMISSIBLE_PRIMITIVE_FULL_OFFSET_CHART")
            self.assertTrue(negative["synchronous_guard_invariance_applicable"])

    def test_27_late_root3_join_has_exact_primitive_multiplier_scope(self):
        x=classify(27,3,66,1)
        self.assertEqual(x["status"],"ADMISSIBLE_PRIMITIVE_FULL_OFFSET_CHART")
        self.assertEqual(x["source_endpoint"],x["earlier_endpoint"])
        self.assertEqual(x["source_endpoint"],5)
        self.assertEqual((x["source_odd_count"],x["earlier_odd_count"]),(40,1))
        self.assertEqual((x["primitive_source_multiplier"],x["primitive_earlier_multiplier"]),(1,3**39))
        self.assertEqual(x["original_source_slope"],2**66)
        self.assertEqual(x["earlier_source_slope"],2*3**39)
        self.assertLess(x["earlier_source_slope"],x["original_source_slope"])
        self.assertFalse(x["individual_chart_formally_reified"])

    def test_21_odd_three_root_preserved_but_earlier7_not_root(self):
        x=classify(21,3,3,2)
        self.assertEqual((x["original_source_slope"],x["earlier_source_slope"]),(24,4))
        self.assertEqual((21+24)%6,3)
        self.assertEqual((3+4)%3,1)
        y=classify(45,7,3,2)
        self.assertEqual(y["status"],"ADMISSIBLE_PRIMITIVE_FULL_OFFSET_CHART")
        self.assertEqual(y["common_endpoint_intercept"],17)

    def test_real_base_mismatch_is_not_infinite_negative_theorem(self):
        for x in (classify(5,3,1,0),classify(27,3,0,0)):
            self.assertEqual(x["status"],"BASE_ENDPOINT_MISMATCH_AT_SUPPLIED_CLOCKS")
            self.assertIsNone(x["candidate_multiplier_exists"])
            self.assertIs(x["synchronous_guard_invariance_applicable"],False)
            self.assertEqual(x["proof_authority"],"BOUNDED_EXACT_ONLY")
            self.assertTrue(x["not_a_Collatz_counterexample"])

    def test_invalid_source_and_clock_coordinates_are_rejected(self):
        for args in ((5,5,1,2),(3,5,1,2),(0,3,1,2),
                     (5,3,-1,2),(5,3,1,-2),(5,3,1.0,2),
                     (True,3,1,2)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):classify(*args)

    def test_tampering_with_evidence_scopes_or_case_fails_restart(self):
        for key in ("proof_pin","classification","parent","qed","weighted","extra_case"):
            s=deepcopy(self.state)
            if key=="proof_pin":
                s["proof_authorities"]["V137_MULTIPLIER_IFF"]["commit"]="0"*40
            elif key=="classification":
                s["tracked_cases"][1]["status"]="COLLATZ_COUNTEREXAMPLE"
            elif key=="parent":
                s["parent"]["canonical_state_sha256"]="0"*64
            elif key=="qed":
                s["qed"]=True
            elif key=="weighted":
                s["tracked_cases"][1]["weighted_left"]=0
            else:
                s["tracked_cases"].append({"source":5,"status":"QED"})
            with self.subTest(key=key):
                with self.assertRaises(ValueError):audit(s)

    def test_byte_identical_state_restart_and_original_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"decision.json"
            q=Path(td)/"decision-restart.json"
            h1=write(self.state,p)
            h2=write(json.loads(p.read_text()),q)
            self.assertEqual(h1,h2)
            self.assertEqual(p.read_bytes(),q.read_bytes())
            self.assertEqual(PARENT_PATH.read_bytes(),self.raw)

    def test_minimum_present_only_pinned_cases_and_no_false_success(self):
        self.assertEqual(len(self.state["tracked_cases"]),len(PAIRS))
        bystat={}
        for c in self.state["tracked_cases"]:
            bystat[c["status"]]=bystat.get(c["status"],0)+1
        self.assertEqual(bystat,{
            "ADMISSIBLE_PRIMITIVE_FULL_OFFSET_CHART":8,
            "FIXED_CLOCK_MATCHED_COEFFICIENT_GRAMMAR_IMPOSSIBLE":1,
            "BASE_ENDPOINT_MISMATCH_AT_SUPPLIED_CLOCKS":2,
        })
        self.assertIn("identical_additional_shortcut_wait_on_both_meeting_clocks",
                      self.state["retired_redundant_search"])
        self.assertIn("new_asymmetric_clock_or_meeting_endpoint",
                      self.state["not_retired_search"])
        self.assertEqual(self.state["global_collatz"],"UNKNOWN")

if __name__=="__main__":
    unittest.main()
