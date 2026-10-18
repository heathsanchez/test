"""V5 frozen native/family-choice contracts without reading new task source bodies."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import g2_v5_native_admission as gate
from . import g2_v5_choose_observation as choice


class V5NativeAndMethodBoundary(unittest.TestCase):
    def test_01_four_roles_locked_before_any_task_source(self):
        m=gate.frozen_roles()
        self.assertEqual([r["role"] for r in m["roles"]],[
            "TRAINING_0","TRAINING_1","TRAINING_2","SEALED_FUTURE"])
        self.assertEqual(len({r["repo"] for r in m["roles"]}),4)
        self.assertTrue(all(r["source_body"]=="UNOPENED" for r in m["roles"]))

    def test_02_three_original_method_source_pins_match(self):
        self.assertEqual(set(choice.pinned_method_bytes()),
                         {"mutable","projection","projection_support"})
        self.assertTrue(all(len(x)==64 for x in choice.pinned_method_bytes().values()))

    def test_03_no_method_applicable_returns_unknown(self):
        self.assertEqual(choice.choose_family(False,False),
                         "UNKNOWN_NO_APPLICABLE_FROZEN_METHOD")

    def test_04_two_applicable_methods_preserve_choice(self):
        self.assertEqual(choice.choose_family(True,True),
                         "UNKNOWN_CHOICE_TWO_APPLICABLE_METHODS")

    def test_05_each_unique_family_selects_only_itself(self):
        self.assertEqual(choice.choose_family(True,False),
                         "APPLICABLE_MUTABLE_METHOD")
        self.assertEqual(choice.choose_family(False,True),
                         "APPLICABLE_PROJECTION_METHOD")

    def test_06_original_protected_failure_is_not_zero_skip(self):
        row={"status":"ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE",
             "native":{"returncode":1,"counts":{"tests":3,"failures":1,
                      "errors":0,"skipped":1}}}
        self.assertEqual(gate.clean_selected(row)[0],False)

    def test_07_source_faithful_real_assertion_shape_allowed_for_admission(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/"src").mkdir();(p/"tests").mkdir()
            a=b"def calculate(): return 1\n";b=b"def test_failure(): assert False\n"
            (p/"src/x.py").write_bytes(a);(p/"tests/test_x.py").write_bytes(b)
            row={"status":"ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE",
                 "repo":"fake/new","pr":88,"work_dir":str(p),"production":"src/x.py",
                 "author_test":"tests/test_x.py",
                 "source_sha256":hashlib.sha256(a).hexdigest(),
                 "head_test_sha256":hashlib.sha256(b).hexdigest(),
                 "protected_nodes":["tests/test_x.py::test_failure"],
                 "native":{"returncode":1,"counts":{"tests":1,"failures":1,
                           "errors":0,"skipped":0}}}
            self.assertEqual(gate.clean_selected(row),
                             (True,"AUTHENTIC_PROTECTED_FAIL"))
            (p/"src/x.py").write_bytes(b"tampered")
            self.assertEqual(gate.clean_selected(row)[0],False)

    def test_08_only_training_roles_ever_enter_native_runner(self):
        invoked=[]
        def fake(task,index,dest):
            invoked.append((task["repo"],index))
            return {"status":"NOT_ELIGIBLE_NO_PROTECTED_FAILURE"}
        with tempfile.TemporaryDirectory() as td:
            with patch.object(gate.native,"one",side_effect=fake):
                output=gate.execute(Path(td)/"native")
            self.assertEqual(output["status"],
                             "UNKNOWN_NO_ADMITTED_TRAINING_FAILURE")
            self.assertEqual(len(invoked),3)
            future=gate.frozen_roles()["roles"][3]["repo"]
            self.assertNotIn(future,[x[0] for x in invoked])
            self.assertEqual(output["future"],"SEALED_UNOPENED")
            self.assertEqual(output["G2"],"UNKNOWN")

    def test_09_no_admission_never_opens_method_or_future(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td);result=target/"ADMISSION.json"
            result.write_text(json.dumps({
                "status":"UNKNOWN_NO_ADMITTED_TRAINING_FAILURE",
                "future":"SEALED_UNOPENED","selected":None}))
            report=choice.main(result,target/"method")
            self.assertEqual(report["status"],"UNKNOWN_NO_EARNED_NATIVE_TRAINING")
            self.assertEqual(report["future"],"SEALED_UNOPENED")
            self.assertEqual(report["candidate_results"],[])
            self.assertEqual(report["G2"],"UNKNOWN")


if __name__=="__main__":
    unittest.main()
