"""V12 pre-execution deterministic source-role and guard constraints.

All candidates are HUMAN-SUPPLIED EXPOSED alternatives. Passing the original
native tests is not an autonomous G2 or unrestricted source-repair result.
"""
import unittest
from pathlib import Path
from . import qualify_exposed_guard_v12 as v12

class FrozenV12GuardContracts(unittest.TestCase):
    def test_A01_original_source_and_protocol_are_bound(self):
        p=v12.frozen()
        self.assertEqual(p["original_head_test_blob"],"577720ec7cf0a48b9b2909e45ddde29235f460ac")
        self.assertEqual(p["prior_V11_red"],38986306451)
        self.assertEqual(p["claims"]["G2"],"UNKNOWN")
        self.assertEqual(p["budgets"]["native_calls_ceiling"],12)

    def test_A02_exactly_six_predeclared_typed_arms(self):
        self.assertEqual(v12.ARMS,("BASE","NONE_ONLY","NONE_OR_ZERO","CALLABILITY","SHAM","REMOVAL"))

    def test_A03_only_original_production_guard_is_changed(self):
        before="def fn(self):\n    if not self.wait:  # type: ignore[truthy-bool]\n        pass\n"
        for arm in ("NONE_ONLY","NONE_OR_ZERO","CALLABILITY"):
            changed=v12.transform(arm,before)
            self.assertNotEqual(before,changed)
            self.assertEqual(before.count("if not self.wait:"),1)
            self.assertNotIn("if not self.wait:",changed)
        self.assertEqual(v12.transform("BASE",before),before)

    def test_A04_nonmatching_or_ambiguous_original_guards_refuse(self):
        for before in ("if self.wait:\n pass\n",
                       "if not self.wait:  # type: ignore[truthy-bool]\n"*2):
            with self.assertRaises(ValueError):
                v12.transform("NONE_OR_ZERO",before)

    def test_A05_original_sham_guard_is_unmodified(self):
        source="def f():\n    return tornado is not None\n"
        altered=v12.transform("SHAM",source)
        self.assertIn("return tornado is None",altered)
        self.assertEqual(v12.transform("REMOVAL",source),source)

    def test_A06_alternatives_use_valid_python_ast(self):
        source="def f(self):\n    if not self.wait:  # type: ignore[truthy-bool]\n        pass\n"
        import ast
        for arm in ("NONE_ONLY","NONE_OR_ZERO","CALLABILITY"):
            ast.parse(v12.transform(arm,source))

    def test_A07_no_outcome_promoted_from_simulated_or_missing_native_receipts(self):
        self.assertEqual(v12.native_status({"status":"PASS_SCOPED_NATIVE",
                                           "native_calls":1},
                                          {"status":"UNKNOWN_NATIVE_COLLECTION","native_calls":1}),"UNKNOWN")
        self.assertEqual(v12.native_status({"status":"PASS_SCOPED_NATIVE","native_calls":0},
                                          {"status":"PASS_SCOPED_NATIVE","native_calls":0}),"UNKNOWN")

if __name__=="__main__":unittest.main()
