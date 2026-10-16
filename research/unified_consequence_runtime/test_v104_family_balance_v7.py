"""Precommitted frozen V7 exposed V104 family scheduling contracts.

No new AST repair generator is allowed: exact original V104 selector/builder
program_candidates is the *only* emission authority. This can diagnose
starvation on exposed source but cannot promote developmental G2.
"""
import json
import os
from pathlib import Path
import unittest

from . import v104_family_balance_v7 as balance
from . import decisive_constructor as qualified

SOURCE="""def choose(items, threshold):
    count = 0
    while count < len(items):
        if items[count] >= threshold:
            return len(items)
        count += 1
    return max(items)
"""


class FrozenV104FamilySchedule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pin=Path(os.environ["UDM_V7_TRISKELION"])

    def test_A01_original_source_pin_and_only_original_generator_used(self):
        report=balance.emit(self.pin,SOURCE,cap=64)
        self.assertEqual(report["source_pin"],qualified.SOURCE_PIN)
        self.assertEqual(report["scope"],"EXPOSED_DIAGNOSTIC_ORIGINAL_GRAMMAR_ONLY")
        self.assertLessEqual(len(report["rows"]),64)
        self.assertTrue(report["rows"])
        self.assertEqual(len({row["id"] for row in report["rows"]}),len(report["rows"]))
        native,_=qualified._original(self.pin)
        accepted={(tuple(s),tuple(b)) for s in native["SELECTORS"] for b in native["BUILDERS"]}
        for row in report["rows"]:
            signature=(tuple(row["selector"]),tuple(row["builder"]))
            self.assertIn(signature,accepted)
            original=native["program_candidates"](SOURCE,allowed={signature},cap=row["slot_rank"])
            self.assertEqual(original[row["slot_rank"]-1][2],row["replacement"])

    def test_A02_finite_family_coverage_increases_diversity_without_new_operation(self):
        old=qualified.generate_candidates(self.pin,SOURCE,cap=64)
        new=balance.emit(self.pin,SOURCE,cap=64)
        old_families={(tuple(s),tuple(b)) for s,b,_ in old}
        new_families={(tuple(x["selector"]),tuple(x["builder"])) for x in new["rows"]}
        self.assertGreater(len(new_families),len(old_families))
        self.assertGreaterEqual(len(new_families),4)
        self.assertEqual(new["native_calls"],0)
        self.assertEqual(new["G2"],"UNKNOWN")

    def test_A03_exact_source_change_affects_candidate_identity(self):
        first=balance.emit(self.pin,SOURCE,cap=64)
        second=balance.emit(self.pin,SOURCE.replace("return len(items)","return count"),cap=64)
        self.assertNotEqual(first["source_sha256"],second["source_sha256"])

    def test_A04_unmodified_source_pin_rejects_unknown_family(self):
        native,_=qualified._original(self.pin)
        bad=(("Invented","field"),("CONST",99))
        self.assertNotIn(bad,{(tuple(s),tuple(b)) for s in native["SELECTORS"] for b in native["BUILDERS"]})
        with self.assertRaises(ValueError):
            qualified.generate_candidates(self.pin,SOURCE,allowed=[bad],cap=1)

    def test_A05_nonstr_source_and_budget_fail_closed(self):
        for content,cap in ((12,64),(SOURCE,0),(SOURCE,321)):
            with self.subTest(content=content if isinstance(content,int) else "string",cap=cap),self.assertRaises(ValueError):
                balance.emit(self.pin,content,cap=cap)

    def test_A06_no_repair_promotion_from_source_enumeration(self):
        result=balance.emit(self.pin,SOURCE,cap=64)
        self.assertEqual(result["verification"],"NONE_NO_NATIVE_SOURCE_TEST")
        self.assertEqual(result["G2"],"UNKNOWN")
        self.assertEqual(result["G3"],"UNKNOWN")
        self.assertEqual(result["G4"],"UNKNOWN")


if __name__=="__main__":unittest.main()
