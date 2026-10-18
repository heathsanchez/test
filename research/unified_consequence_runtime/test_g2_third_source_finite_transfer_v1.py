"""Preregistered apparatus and adversarial contracts for source-distinct V1.

All sources are synthetic or previously exposed methods; no third-source bodies.
"""
from __future__ import annotations
from pathlib import Path
import tempfile
import unittest

from . import g2_third_source_finite_transfer_v1 as m


class SourceUnopenedThirdTransferV1(unittest.TestCase):
    def test_01_frozen_source_roles_preserve_original_metadata(self):
        p=m.protocol()
        self.assertEqual([x["repo"] for x in p["candidate_order"]],
                         ["psf/requests","urllib3/urllib3","pydantic/pydantic"])
        self.assertEqual(p["science"]["G2"],"UNKNOWN")

    def test_02_frozen_source_method_code_not_rewritten(self):
        pins=m.source_pins()
        self.assertEqual(set(pins),{"source neutral strict terminal anchor","finite composition","original native admission"})

    def test_03_safe_source_path_refuses_traversal_links_and_untracked(self):
        for x in ("src/../evil.py","/src/f.py","src/x//y.py","src/f.txt","tests/test.py",""):
            with self.subTest(path=x),self.assertRaises(ValueError):
                m.safe_module_path(x)
        self.assertTrue(m.safe_module_path("src/requests/utils.py"))

    def test_04_test_ast_import_scope_has_no_target_specific_paths(self):
        source=b"import requests.utils\nfrom requests.sessions import Session\nfrom os.path import join\n"
        tracked=["src/requests/utils.py","src/requests/sessions.py",
                 "src/requests/api.py","src/os/path.py"]
        found=m.scope_from_imports(source,tracked,"src/requests/utils.py",8)
        self.assertEqual(found,["src/requests/sessions.py","src/requests/utils.py"])

    def test_05_ambiguous_module_mapping_refused(self):
        with self.assertRaises(ValueError):
            m.scope_from_imports(b"from request_lib.a import A\n",
              ["src/request_lib/a.py","libs/request_lib/a.py","src/request_lib/driver.py"],
              "src/request_lib/driver.py",8)

    def test_06_literal_edit_schedule_two_files_four_masks(self):
        original={
          "src/a/core.py":b"import re\nPAT_A = re.compile(r'^x$')\n",
          "src/b/core.py":b"import re\nPAT_B = re.compile(r'^y$')\n"}
        cat=m.catalog(original,max_edits=4)
        self.assertEqual(len(cat),2)
        masks=m.mask_schedule(original,cat)
        self.assertEqual(set(masks),set(range(4)))
        self.assertEqual(len({m.source_fingerprint(v) for v in masks.values()}),4)
        self.assertEqual(masks[0],original)
        self.assertNotEqual(masks[3],original)

    def test_07_parametrized_junit_cases_distinct_and_declared(self):
        selectors=["tests/test_utils.py::test_p"]
        raw=(b'<testsuite tests="2"><testcase classname="tests.test_utils" name="test_p[a]"/>'
             b'<testcase classname="tests.test_utils" name="test_p[b]"><failure/></testcase></testsuite>')
        x=m.native_cases(raw,selectors)
        self.assertEqual(list(x.values()).count("FAIL"),1)
        self.assertEqual(len(x),2)

    def test_08_unexpected_native_case_rejected(self):
        with self.assertRaises(ValueError):
            m.native_cases(b'<testsuite><testcase classname="t" name="unexpected"/></testsuite>',
                           ["tests/test_utils.py::test_p"])

    def test_09_skip_and_collection_error_rejected(self):
        for child in (b"<skipped/>",b"<error/>"):
            raw=(b'<testsuite><testcase classname="tests.test_utils" name="test_p">'
                 +child+b'</testcase></testsuite>')
            with self.subTest(child=child),self.assertRaises(ValueError):
                m.native_cases(raw,["tests/test_utils.py::test_p"])

    def test_10_finite_join_true_on_original_qualified_exposed_masks(self):
        self.assertEqual(m.finite_law([0,4,2,6,8,12,10,14,1,5,3,7,9,13,11,15],4,4)["pairs"],256)
        self.assertEqual(m.finite_law([5,7,13,15],2,4)["pairs"],16)

    def test_11_finite_join_counterexample_rejected_even_if_full_pass(self):
        with self.assertRaises(ValueError):
            m.finite_law([0,3,2,3],2,2)

    def test_12_true_equal_info_ledger_cannot_be_reported_as_loss(self):
        original={"a":"PASS","b":"FAIL"}
        rows={
         0:original,
         1:{"a":"PASS","b":"PASS"},
         2:{"a":"PASS","b":"FAIL"},
         3:{"a":"PASS","b":"PASS"}}
        outcome=m.replay_choices(rows,2)
        self.assertEqual(outcome["ledger"]["winner"],1)
        self.assertEqual(outcome["composed"]["winner"],1)
        self.assertEqual(outcome["prior_single"]["winner"],1)
        self.assertEqual(outcome["relative_to_fully_informed_ledger"],"TIE_MINIMAL_MASK")

    def test_13_composition_succeeds_where_single_does_not_but_informed_ledger_ties(self):
        rows={
          0:{"x":"FAIL","y":"FAIL"},
          1:{"x":"PASS","y":"FAIL"},
          2:{"x":"FAIL","y":"PASS"},
          3:{"x":"PASS","y":"PASS"}}
        r=m.replay_choices(rows,2)
        self.assertIsNone(r["prior_single"]["winner"])
        self.assertEqual(r["composed"]["winner"],3)
        self.assertEqual(r["ledger"]["winner"],3)
        self.assertEqual(r["relative_to_fully_informed_ledger"],"TIE_MINIMAL_MASK")


if __name__=="__main__":
    unittest.main()
