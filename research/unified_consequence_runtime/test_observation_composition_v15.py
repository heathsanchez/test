"""Frozen V15 generic observation-conditioned Python predicate-construction contracts.

Authored before the V15 constructor; exposed Tenacity is NOT prospective G2.
No correct edit, original repaired HEAD, or task-specific known answer supplied.
"""
from __future__ import annotations
import ast
import hashlib
import unittest
from . import observation_composition_v15 as v15

SOURCE = ("class Widget:\n"
          "    def f(self):\n"
          "        if not self.action:\n"
          "            return 'skipped'\n"
          "        if not self.other:\n"
          "            return 'other'\n"
          "        return self.action()\n")
EVENT={"path":"pkg/module.py","line":3,"then_line":4,
       "attribute":"action","branch":"THEN","callable":True,
       "kind":"IF_NOT_SELF_ATTRIBUTE"}

def observed_test(tree,index=0):
    return tree.body[0].body[0].body[index].test

class FrozenV15CompositionalGrammar(unittest.TestCase):
    def emit(self,source=SOURCE,event=None,cap=24,path="pkg/module.py"):
        return v15.emit(source,path,EVENT if event is None else event,cap=cap)

    def test_A01_bounded_task_agnostic_candidates_deterministic(self):
        x=self.emit();y=self.emit()
        self.assertEqual(x,y)
        self.assertLessEqual(len(x),24)
        self.assertGreater(len(x),8)
        self.assertEqual(len({item["sha256"] for item in x}),len(x))
        self.assertTrue(all(item["status"]=="CANDIDATE_NOT_NATIVE_WARRANT"
                            for item in x))
        self.assertTrue(all(item["source_line"]==3 and item["path"]=="pkg/module.py"
                            for item in x))

    def test_A02_only_exact_observed_AST_slot_changes(self):
        before=ast.parse(SOURCE)
        for row in self.emit():
            candidate=ast.parse(row["source"])
            self.assertNotEqual(ast.dump(observed_test(candidate)),ast.dump(observed_test(before)))
            self.assertEqual(ast.dump(observed_test(candidate,1)),ast.dump(observed_test(before,1)))
            self.assertEqual(ast.dump(candidate.body[0].body[0].body[-1]),
                             ast.dump(before.body[0].body[0].body[-1]))

    def test_A03_every_generated_predicate_references_original_observed_attribute(self):
        for row in self.emit():
            tree=ast.parse(row["source"])
            test=observed_test(tree)
            references=[n for n in ast.walk(test) if isinstance(n,ast.Attribute)
                        and isinstance(n.value,ast.Name) and n.value.id=="self"
                        and n.attr=="action"]
            self.assertTrue(references)

    def test_A04_compositions_extend_original_v104_expression_types(self):
        emitted=[observed_test(ast.parse(row["source"])) for row in self.emit()]
        self.assertTrue(any(isinstance(x,ast.Compare) for x in emitted))
        self.assertTrue(any(isinstance(x,ast.BoolOp) for x in emitted))
        self.assertTrue(any(isinstance(x,ast.Call) and getattr(x.func,"id",None)=="callable"
                            for x in emitted))
        self.assertTrue(any(isinstance(x,ast.BoolOp) and any(
               isinstance(n,ast.Call) and getattr(n.func,"id",None)=="callable"
               for n in ast.walk(x)) for x in emitted))

    def test_A05_no_executable_names_outside_pinned_compositional_vocabulary(self):
        for row in self.emit():
            tree=ast.parse(row["source"])
            test=observed_test(tree)
            for n in ast.walk(test):
                if isinstance(n,ast.Call):
                    self.assertIsInstance(n.func,ast.Name)
                    self.assertIn(n.func.id,{"bool","callable"})
                if isinstance(n,ast.Compare):
                    self.assertEqual(len(n.ops),1)
                    self.assertIsInstance(n.ops[0],(ast.Is,ast.Eq))
                if isinstance(n,ast.BoolOp):
                    self.assertIsInstance(n.op,(ast.And,ast.Or))

    def test_A06_cold_original_expression_is_not_promoted_as_developmental(self):
        orig=ast.dump(observed_test(ast.parse(SOURCE)))
        self.assertTrue(all(ast.dump(observed_test(ast.parse(row["source"])))!=orig
                            for row in self.emit()))
        self.assertEqual(v15.G2,"UNKNOWN")
        self.assertEqual(v15.G3,"UNKNOWN")

    def test_A07_wrong_observation_and_nonunique_AST_source_refused(self):
        for change in ({"path":"other.py"},{"line":999},{"then_line":999},
                       {"attribute":"other"},{"callable":False},{"branch":"ELSE"},
                       {"kind":"CALL"}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.emit(event={**EVENT,**change})
        with self.assertRaises(ValueError):
            self.emit(source=SOURCE.replace("if not self.action:","if self.action:"))

    def test_A08_source_independent_renaming_and_relocation(self):
        changed=SOURCE.replace("action","handler")
        event={**EVENT,"path":"other/nothing.py","attribute":"handler"}
        candidates=self.emit(changed,event,path="other/nothing.py")
        self.assertTrue(candidates)
        self.assertTrue(all(row["path"]=="other/nothing.py" for row in candidates))
        for c in candidates:
            test=observed_test(ast.parse(c["source"]))
            self.assertTrue(any(isinstance(n,ast.Attribute) and n.attr=="handler"
                                for n in ast.walk(test)))

    def test_A09_candidate_source_identity_independent_of_path_spelling(self):
        first=self.emit()
        second=self.emit(source=SOURCE.replace("action","handler"),
                         event={**EVENT,"attribute":"handler"})
        self.assertNotEqual(first[0]["sha256"],second[0]["sha256"])
        self.assertEqual(len(first),len(second))

    def test_A10_cap_refuses_nonfinite_or_oversized_search(self):
        for cap in (0,-1,25,1.0,True):
            with self.subTest(cap=cap),self.assertRaises(ValueError):
                self.emit(cap=cap)
        self.assertEqual(len(self.emit(cap=5)),5)

    def test_A11_single_input_bytes_preserved(self):
        prior=hashlib.sha256(SOURCE.encode()).hexdigest()
        self.emit()
        self.assertEqual(prior,hashlib.sha256(SOURCE.encode()).hexdigest())

    def test_A12_generic_source_contains_no_original_task_specific_repair(self):
        import inspect
        source=inspect.getsource(v15)
        self.assertNotIn("tenacity",source.lower())
        self.assertNotIn("if not self.wait",source)
        self.assertNotIn("line 425",source)

if __name__=="__main__":unittest.main()
