"""Frozen V13 exposed-source branch observation qualification.

Test the OBSERVATION only. No patch or method selector may be supplied with
the guard location, candidate answer, or HEAD repaired source. This does not
qualify native scientific G2, verified repair acquisition or a generic sandbox.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from . import typed_native_authority_v10 as native
from . import observed_branch_v13 as detect


def git(path,*args):
    return subprocess.check_output(["git","-C",str(path),*args],text=True,
                                   stderr=subprocess.PIPE).strip()


def source(callable_action=True):
    behavior=(
        "class Action:\n"
        "    def __bool__(self): return False\n"
        "    def __call__(self): return 'called'\n"
        if callable_action else "")
    action="Action()" if callable_action else "0"
    return (behavior+
        "class Widget:\n"
        "    def __init__(self): self.action="+action+"\n"
        "    def evaluate(self):\n"
        "        if not self.action:\n"
        "            return 'skipped'\n"
        "        return self.action()\n").encode()


class FrozenV13BranchObservation(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="udm-v13-")
        self.addCleanup(temp.cleanup)
        self.home=Path(temp.name).resolve()
        self.root=self.home/"original"
        self.root.mkdir()
        git(self.root,"init","-q")
        git(self.root,"config","user.name","V13 frozen observations")
        git(self.root,"config","user.email","v13@example.invalid")
        (self.root/"pkg").mkdir()
        (self.root/"pkg/__init__.py").write_text("")
        (self.root/"tests").mkdir()
        (self.root/"tests/__init__.py").write_text("")

    def seal(self,src,test="from pkg.core import Widget\ndef test_protected(): assert Widget().evaluate() == 'called'\n"):
        (self.root/"pkg/core.py").write_bytes(src)
        (self.root/"tests/test_protected.py").write_text(test)
        git(self.root,"add","-A")
        git(self.root,"commit","-qm","immutable original test source")
        return git(self.root,"rev-parse","HEAD")

    def observe(self,commit,index=0,required="tests/test_protected.py::test_protected"):
        stage=self.home/("stage-"+str(index))
        native.stage(self.root,commit,stage)
        result=detect.run_observer(
           self.root,commit,stage,
           production_paths=("pkg/core.py",),
           required=(required,),
           testpaths=("tests/test_protected.py",),
           interpreter=sys.executable,timeout=45)
        self.assertEqual(native.verify_stage(self.root,commit,stage)["status"],
                         "PASS_TYPED_STAGE_IDENTITY")
        return result

    def test_A01_source_agnostic_static_AST_guard_inventory(self):
        found=detect.guard_nodes("pkg/core.py",source())
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]["path"],"pkg/core.py")
        self.assertEqual(found[0]["attribute"],"action")
        self.assertEqual(found[0]["kind"],"IF_NOT_SELF_ATTRIBUTE")
        self.assertGreater(found[0]["line"],0)
        self.assertTrue(found[0]["then_lines"])

    def test_A02_actually_failing_callable_branch_is_observed(self):
        commit=self.seal(source())
        result=self.observe(commit)
        self.assertEqual(result["status"],"OBSERVED_PROTECTED_FAILURE_BRANCH_EDGE")
        self.assertEqual(result["native_exit"],1)
        self.assertIn("tests/test_protected.py::test_protected",result["failed_protected"])
        events=result["events"]
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["path"],"pkg/core.py")
        self.assertEqual(events[0]["attribute"],"action")
        self.assertEqual(events[0]["branch"],"THEN")
        self.assertTrue(events[0]["callable"])
        self.assertEqual(result["source_commit"],commit)

    def test_A03_callability_is_not_derived_from_text_alone(self):
        commit=self.seal(source(callable_action=False))
        result=self.observe(commit)
        self.assertEqual(result["status"],"UNKNOWN_NO_WARRANTED_BRANCH_EDGE")
        self.assertEqual(result["events"],[])
        self.assertEqual(result["native_exit"],1)

    def test_A04_branch_observation_is_not_a_warrant_when_test_passed(self):
        commit=self.seal(source(),test=(
            "from pkg.core import Widget\n"
            "def test_protected(): assert Widget().evaluate() == 'skipped'\n"))
        result=self.observe(commit)
        self.assertEqual(result["native_exit"],0)
        self.assertEqual(result["status"],"UNKNOWN_PROTECTED_NOT_FAILED")
        self.assertEqual(result["events"],[])

    def test_A05_unexecuted_source_pattern_has_no_event(self):
        code=source()+(
            b"def unused(self):\n"
            b"    if not self.missing:\n"
            b"        return 'never'\n")
        commit=self.seal(code)
        result=self.observe(commit)
        self.assertEqual(result["status"],"OBSERVED_PROTECTED_FAILURE_BRANCH_EDGE")
        self.assertEqual({x["attribute"] for x in result["events"]},{"action"})

    def test_A06_two_independent_observers_agree_on_exact_edges(self):
        commit=self.seal(source())
        first=self.observe(commit,0)
        second=self.observe(commit,1)
        self.assertEqual(first["status"],second["status"])
        self.assertEqual(first["events"],second["events"])
        self.assertNotEqual(first["native_stdout_sha256"],"")

    def test_A07_mutated_staged_source_must_refuse_before_observation(self):
        commit=self.seal(source())
        stage=self.home/"altered"
        native.stage(self.root,commit,stage)
        (stage/"pkg/core.py").write_text("class Unrelated: pass\n")
        with self.assertRaises(ValueError):
            detect.run_observer(self.root,commit,stage,
                production_paths=("pkg/core.py",),
                required=("tests/test_protected.py::test_protected",),
                testpaths=("tests/test_protected.py",),
                interpreter=sys.executable,timeout=45)

    def test_A08_nonexistent_protected_test_is_not_a_source_observation(self):
        commit=self.seal(source())
        result=self.observe(commit,0,"tests/test_protected.py::test_missing")
        self.assertEqual(result["status"],"UNKNOWN_PROTECTED_NOT_FAILED")
        self.assertEqual(result["events"],[])

    def test_A09_malformed_or_out_of_scope_source_is_rejected(self):
        with self.assertRaises(ValueError):
            detect.guard_nodes("../host.py",b"if not self.x: pass\n")
        with self.assertRaises(ValueError):
            detect.guard_nodes("pkg/core.py",b"if True:\n  pass\n    pass\n")

    def test_A10_warrant_remains_separate_from_observation(self):
        self.assertEqual(detect.G2,"UNKNOWN")
        self.assertEqual(detect.G3,"UNKNOWN")
        self.assertEqual(detect.SOURCE_OBSERVATION_AUTHORITY,"DIAGNOSTIC_NOT_NATIVE_WARRANT")
        self.assertNotIn("repair",str(detect.guard_nodes("pkg/core.py",source())).lower())


if __name__=="__main__":
    unittest.main()
