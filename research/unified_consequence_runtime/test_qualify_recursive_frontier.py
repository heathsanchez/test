"""Protocol guards, not a synthetic developmental qualification."""
import unittest
import os
from pathlib import Path
from research.unified_consequence_runtime import qualify_recursive_frontier as q

class RecursiveProtocolTests(unittest.TestCase):
    def test_timeout_does_not_license_development(self):
        self.assertEqual(q.development_route({'status':'UNKNOWN_TIMEOUT'}),'UNKNOWN_NATIVE_OBLIGATION')
    def test_passing_native_suite_does_not_invent_a_residual(self):
        self.assertEqual(q.development_route({'status':'PASS_NATIVE'}),'SATISFIED_NO_DEVELOPMENTAL_RESIDUAL')
    def test_genuine_native_assertion_failure_licenses_search_only(self):
        self.assertEqual(q.development_route({'status':'FAIL_NATIVE'}),'SEARCH_EXISTING_LANGUAGE')
    def test_original_generator_semantics_and_budget_preserved(self):
        source=Path(os.environ.get('UDM_CONSTRUCTOR_SOURCE','/workspace/repos/triskelion'))
        programs=q.original_candidates(source,'def f(x):\n return abs(x)\n',cap=8)
        self.assertEqual(len(programs),8)
        self.assertEqual(programs,q.original_candidates(source,'def f(x):\n return abs(x)\n',cap=8))
        self.assertTrue(all(isinstance(item[2],str) for item in programs))
        with self.assertRaises(ValueError):q.original_candidates(source,'x=1',cap=0)

if __name__=='__main__':unittest.main()
