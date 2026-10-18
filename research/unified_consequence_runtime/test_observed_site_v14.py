"""Frozen V14 tests: original V104 source-slot activation, no new builders.

Everything here is EXPOSED Tenacity or synthetic; no prospective G2 claim.
The slot is passed as an authenticated *observation candidate*, not as a
manually selected replacement expression or method.
"""
from __future__ import annotations
import ast
import hashlib
import os
from pathlib import Path
import unittest

from . import observed_site_v14 as v14

SOURCE=("def f(self):\n"
        "    if not self.action:\n"
        "        return 0\n"
        "    if not self.other:\n"
        "        return 1\n"
        "    return 2\n")
EVENT={"kind":"IF_NOT_SELF_ATTRIBUTE","path":"pkg.py",
       "line":2,"attribute":"action","branch":"THEN",
       "callable":True,"then_line":3}


class FrozenV14OriginalSlotRules(unittest.TestCase):
    def setUp(self):
        self.original=Path(os.environ["UDM_V7_TRISKELION"]).resolve()

    def emit(self, source=SOURCE, event=None, cap=32):
        return v14.targeted_original_candidates(source,"pkg.py",
                                                 EVENT if event is None else event,
                                                 self.original,cap=cap)

    def test_A01_original_V104_source_is_authenticated(self):
        ns,pin=v14.original_programs(self.original)
        self.assertEqual(len(ns["SELECTORS"]),5)
        self.assertEqual(len(ns["BUILDERS"]),15)
        self.assertIn(("If","test"),ns["SELECTORS"])
        self.assertEqual(pin["commit"],"426c54f7c774560e0fabe7213c5ef333b1327c71")

    def test_A02_candidate_generation_is_source_slot_conditional(self):
        c=self.emit(cap=64)
        self.assertGreater(len(c),5)
        self.assertLessEqual(len(c),64)
        self.assertTrue(all(x["path"]=="pkg.py" and x["observed_line"]==2 for x in c))
        self.assertTrue(all(x["selector"]==("If","test") for x in c))
        second=ast.parse(SOURCE).body[0].body[1].test
        for x in c:
            altered=ast.parse(x["source"])
            self.assertEqual(ast.dump(altered.body[0].body[1].test),
                             ast.dump(second))
            self.assertNotEqual(ast.dump(altered.body[0].body[0].test),
                                ast.dump(ast.parse(SOURCE).body[0].body[0].test))

    def test_A03_known_original_builder_language_has_no_Compare_or_BoolOp(self):
        c=self.emit(cap=64)
        for x in c:
            tree=ast.parse(x["source"])
            test=tree.body[0].body[0].test
            self.assertNotIsInstance(test,(ast.Compare,ast.BoolOp))
            self.assertEqual(x["grammar"],"PINNED_ORIGINAL_V104_BUILDERS_ONLY")

    def test_A04_frozen_program_order_deterministic_and_capped_before_native(self):
        a=self.emit(cap=8)
        b=self.emit(cap=8)
        self.assertEqual(a,b)
        self.assertEqual(len(a),8)
        self.assertEqual(len({x["source_sha256"] for x in a}),8)

    def test_A05_incorrect_observation_location_or_attribute_refused(self):
        for change in ({"line":999},{"attribute":"other"},
                       {"branch":"ELSE"},{"callable":False},{"path":"other.py"}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.emit(event={**EVENT,**change},cap=8)

    def test_A06_not_only_a_text_replacement_of_a_familiar_broken_guard(self):
        src=SOURCE.replace("action","handler")
        e={**EVENT,"attribute":"handler"}
        rows=self.emit(src,e,cap=8)
        self.assertEqual(len(rows),8)
        self.assertTrue(all(ast.parse(x["source"]) for x in rows))

    def test_A07_original_guard_and_other_Source_AST_bytes_are_preserved(self):
        before=SOURCE.encode()
        self.emit(cap=16)
        self.assertEqual(SOURCE.encode(),before)
        self.assertEqual(hashlib.sha256(before).hexdigest(),
                         hashlib.sha256(SOURCE.encode()).hexdigest())

    def test_A08_candidates_are_not_verified_repair_receipts(self):
        rows=self.emit(cap=8)
        self.assertEqual(v14.G2,"UNKNOWN")
        self.assertTrue(all(x["status"]=="CANDIDATE_NO_NATIVE_WARRANT" for x in rows))
        self.assertTrue(all(x["source_sha256"] for x in rows))


if __name__=="__main__":
    unittest.main()
