"""Strict C64 n7 evidence classifier. No ACCEPT authority is ever issued."""
import copy
import hashlib
import json
import pathlib
import unittest

RECEIPT = pathlib.Path(__file__).resolve().parents[1] / "nucleus-logos-support-20261108" / "c64-source-instance.json"
SOURCE = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
STANDARD, HIGH = 262144, 14155776

def classify(data):
    if data.get("source_sha256") != SOURCE or data.get("standard_budget") != STANDARD:
        raise ValueError("source hash or budget mismatch")
    if data.get("proof_rules_changed") is not False or data.get("selected_checker_changed") is not False:
        raise ValueError("checker rules changed")
    if data.get("protected_403_not_run") is not True:
        raise ValueError("protected qualification claim changed")
    records = data.get("records")
    if not isinstance(records, list) or len(records) != 4:
        raise ValueError("C64 evidence truncated")
    arms = {(x.get("budget"), x.get("observe")): x for x in records}
    if len(arms) != 4 or set(arms) != {
        (STANDARD, False), (STANDARD, True), (8388608, True), (HIGH, True)
    }:
        raise ValueError("comparison arms changed")
    for arm in [(STANDARD, False), (STANDARD, True), (8388608, True)]:
        if arms[arm].get("verdict") != "UNKNOWN":
            raise ValueError("unsound early ACCEPT/REJECT claim")
    high = arms[(HIGH, True)]
    if high.get("verdict") != "ACCEPT":
        raise ValueError("high-budget diagnostic positive missing")
    standard_lines = arms[(STANDARD, True)].get("source_instance_observations", [])
    high_lines = high.get("source_instance_observations", [])
    if len(standard_lines) != 12 or len(high_lines) != 12:
        raise ValueError("observer sample missing")
    if any("bool_constructor=true" in x for x in standard_lines):
        raise ValueError("standard trace drift")
    if not any("role=instance:expr=ExprId(8796):grant=14155776" in x and "NameId(146)" in x
               for x in high_lines):
        raise ValueError("instance constructor-shaped observation missing")
    if not any("role=decide:expr=ExprId(8799):grant=128" in x and "NameId(169)" in x
               and "bool_constructor=true" in x for x in high_lines):
        raise ValueError("warmed Bool observation missing")
    if "certificate_steps" in data or "kernel_verified_constructor" in data:
        raise ValueError("unqualified certificate authority")
    return {"source_sha256": SOURCE, "standard_verdict": "UNKNOWN",
            "high_budget_diagnostic_verdict": "ACCEPT",
            "independent_n7_certificate_replay": "NOT_RUN",
            "verified_source_constructor_certificate": "UNKNOWN",
            "nucleus_accept_authority": "NONE"}

class C64Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads(RECEIPT.read_text())
    def test_original_stays_unknown(self):
        self.assertEqual(classify(self.original)["nucleus_accept_authority"], "NONE")
    def test_source_swap_refused(self):
        bad = copy.deepcopy(self.original)
        bad["source_sha256"] = hashlib.sha256(b"forged").hexdigest()
        with self.assertRaises(ValueError): classify(bad)
    def test_false_standard_accept_refused(self):
        bad = copy.deepcopy(self.original)
        bad["records"][1]["verdict"] = "ACCEPT"
        with self.assertRaises(ValueError): classify(bad)
    def test_forged_authority_field_refused(self):
        bad = copy.deepcopy(self.original)
        bad["kernel_verified_constructor"] = True
        with self.assertRaises(ValueError): classify(bad)
    def test_missing_constructor_observation_refused(self):
        bad = copy.deepcopy(self.original)
        bad["records"][-1]["source_instance_observations"] = bad["records"][-1]["source_instance_observations"][6:]
        with self.assertRaises(ValueError): classify(bad)

if __name__ == "__main__":
    unittest.main()
