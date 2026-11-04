"""Check the reported decision boundary, not the serialization implementation."""

import copy
import unittest

from postflight_qualification import validate_pair


def packet(status, sha, last, admitted):
    return {
        "status": status, "source_sha256": sha,
        "global_barrier": "whole-export-sha256",
        "read_coverage": "PARTIAL",
        "semantic_dependency_completeness": "UNKNOWN",
        "verification_reuse_authority": "NONE", "proof_skips": 0,
        "global": {
            "guards": [
                {"stage": "quotient-source-ownership", "result": "PASS"},
                {"stage": "capability-bank", "result": "PASS"},
                {"stage": "postflight-string-literal-qualification", "result": last},
            ],
            "source_resolution_reads": [{"table": "expression", "access": "bulk", "id": None, "present": None}],
            "preflight_reads": [{"table": "expression", "access": "bulk", "id": None, "present": None}],
        },
        "declarations": [{"index": 0}] if admitted else [],
    }


class PostflightPairTests(unittest.TestCase):
    def setUp(self):
        self.good = packet("Accept", "a" * 64, "PASS", admitted=True)
        self.deferred = packet("Unknown", "b" * 64, "DEFER", admitted=False)

    def test_real_downgrade_has_explicit_postflight_boundary(self):
        actual = validate_pair(self.good, self.deferred)
        self.assertEqual(actual["verdict_pair"], ["Accept", "Unknown"])
        self.assertEqual(actual["postflight_pair"], ["PASS", "DEFER"])
        self.assertEqual(actual["nonaccept_admissions"], 0)
        self.assertEqual(actual["proof_skips"], 0)

    def test_forged_or_omitted_postflight_cannot_be_qualified(self):
        for change in (
            lambda x: x["global"]["guards"].pop(),
            lambda x: x["global"]["guards"][-1].update(result="PASS"),
            lambda x: x["declarations"].append({"index": 1}),
            lambda x: x.update(proof_skips=1),
            lambda x: x.update(source_sha256="a" * 64),
            lambda x: x["global"]["preflight_reads"].clear(),
        ):
            bad = copy.deepcopy(self.deferred)
            change(bad)
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_pair(self.good, bad)

    def test_original_accept_must_not_carry_terminal_defer(self):
        good = copy.deepcopy(self.good)
        good["global"]["guards"][-1]["result"] = "DEFER"
        with self.assertRaises(ValueError):
            validate_pair(good, self.deferred)


if __name__ == "__main__":
    unittest.main()
