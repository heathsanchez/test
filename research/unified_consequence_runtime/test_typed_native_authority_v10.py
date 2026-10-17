"""V10 test-first class-qualified protected native execution contracts.

The V9 Tenacity source outcome is *already exposed* and cannot become fresh G2.
These contracts are synthetic, source-bound and independent of that result.
They protect the exact V6 source pin, never permit class/parameter deselection,
and leave the old verifier unchanged. No production or external authority.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

from . import typed_native_authority_v6 as v6
from . import typed_native_authority_v10 as v10


def git(root,*args):
    return subprocess.check_output(["git","-C",str(root),*args],text=True,
                                   stderr=subprocess.PIPE).strip()


class FrozenV10ClassQualifiedNative(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="udm-v10-class-native-")
        self.addCleanup(tmp.cleanup)
        self.repo=Path(tmp.name).resolve()/"source"
        self.dest=Path(tmp.name).resolve()/"staged"
        self.repo.mkdir()
        git(self.repo,"init","-q")
        git(self.repo,"config","user.name","V10 Frozen")
        git(self.repo,"config","user.email","v10@invalid.example")

    def add(self,name,text):
        f=self.repo/name
        f.parent.mkdir(parents=True,exist_ok=True)
        f.write_text(text)

    def commit(self,gitlink=False):
        git(self.repo,"add","-A")
        if gitlink:
            git(self.repo,"update-index","--add","--cacheinfo",
                "160000,"+"b"*40+",vendor/opaque")
        git(self.repo,"commit","-qm","freeze exact class-qualified native source")
        return git(self.repo,"rev-parse","HEAD")

    def run_native(self,required,*,scope=("tests/test_classes.py",),ordinary_v6=False):
        runner=v6 if ordinary_v6 else v10
        return runner.run_protected(self.repo,self.sha,self.dest,required=required,
                                    paths=scope,interpreter=sys.executable,timeout=40)

    def test_A01_only_exact_old_v6_source_can_be_extended(self):
        self.assertEqual(v10.ORIGINAL_V6_GIT_BLOB,
                         "7a813db84ef34a2dd16713b29fd3aced162a4955")
        self.assertEqual(v10.SCHEMA,"UDM_V10_CLASS_QUALIFIED_PROTECTED_AUTHORITY")
        self.assertTrue(v10.verified_v6_source())

    def test_A02_original_v6_class_path_refusal_remains_unchanged(self):
        self.add("tests/test_classes.py",
                 "class TestWitness:\n    def test_case(self): assert True\n")
        self.sha=self.commit();v6.stage(self.repo,self.sha,self.dest)
        with self.assertRaisesRegex(ValueError,"protected obligation"):
            self.run_native(("tests/test_classes.py::TestWitness::test_case",),ordinary_v6=True)

    def test_A03_new_class_method_genuine_native_success(self):
        self.add("pkg/__init__.py","VALUE=42\n")
        self.add("tests/test_classes.py",
                 "from pkg import VALUE\n"
                 "class TestWitness:\n    def test_case(self): assert VALUE==42\n")
        self.sha=self.commit(gitlink=True);v10.stage(self.repo,self.sha,self.dest)
        r=self.run_native(("tests/test_classes.py::TestWitness::test_case",))
        self.assertEqual(r["status"],"PASS_SCOPED_NATIVE")
        self.assertEqual(r["junit"]["passed"],1)
        self.assertIn("pkg/__init__.py",r["imported_project_files"])
        self.assertEqual(v10.verify_stage(self.repo,self.sha,self.dest)["status"],
                         "PASS_TYPED_STAGE_IDENTITY")

    def test_A04_original_class_assertion_failure_is_not_warranted(self):
        self.add("tests/test_classes.py",
                 "class TestWitness:\n    def test_case(self): assert False\n")
        self.sha=self.commit();v10.stage(self.repo,self.sha,self.dest)
        r=self.run_native(("tests/test_classes.py::TestWitness::test_case",))
        self.assertEqual(r["status"],"FAIL_NATIVE_PROTECTED")
        self.assertEqual(r["junit"]["failed"],1)

    def test_A05_nonexistent_class_prefix_is_never_authorized(self):
        self.add("tests/test_classes.py",
                 "class TestWitness:\n    def test_case(self): assert True\n")
        self.sha=self.commit();v10.stage(self.repo,self.sha,self.dest)
        r=self.run_native(("tests/test_classes.py::TestOther::test_case",))
        self.assertEqual(r["status"],"UNKNOWN_PROTECTED_NOT_EXECUTED")

    def test_A06_missing_protected_method_is_not_authorized(self):
        self.add("tests/test_classes.py",
                 "class TestWitness:\n    def test_case(self): assert True\n")
        self.sha=self.commit();v10.stage(self.repo,self.sha,self.dest)
        r=self.run_native(("tests/test_classes.py::TestWitness::test_nonexistent",))
        self.assertEqual(r["status"],"UNKNOWN_PROTECTED_NOT_EXECUTED")

    def test_A07_original_skip_inside_class_is_unknown(self):
        self.add("tests/test_classes.py",
                 "import pytest\nclass TestWitness:\n"
                 "    @pytest.mark.skip(reason='original')\n"
                 "    def test_case(self): assert False\n")
        self.sha=self.commit();v10.stage(self.repo,self.sha,self.dest)
        r=self.run_native(("tests/test_classes.py::TestWitness::test_case",))
        self.assertEqual(r["status"],"UNKNOWN_SKIPPED")

    def test_A08_original_pytest_collection_error_is_unknown(self):
        self.add("tests/test_classes.py",
                 "class TestWitness:\n    def test_case(self):\n"
                 "      return False\n       pass\n")
        self.sha=self.commit();v10.stage(self.repo,self.sha,self.dest)
        r=self.run_native(("tests/test_classes.py::TestWitness::test_case",))
        self.assertEqual(r["status"],"UNKNOWN_NATIVE_COLLECTION")

    def test_A09_injected_unqualified_path_or_invalid_node_is_refused(self):
        self.add("tests/test_classes.py",
                 "class TestWitness:\n    def test_case(self): assert True\n")
        self.sha=self.commit();v10.stage(self.repo,self.sha,self.dest)
        for required in (
             ("tests/../evil.py::TestWitness::test_case",),
             ("tests/test_classes.py::TestWitness::",),
             ("tests/test_classes.py::TestWitness::not_test",),
             ("tests/test_classes.py::TestWitness::test_case::anything",)
        ):
            with self.subTest(required=required),self.assertRaises(ValueError):
                self.run_native(required)

    def test_A10_parameterized_class_method_requires_actual_native_execution(self):
        self.add("tests/test_classes.py",
                 "import pytest\n"
                 "class TestWitness:\n"
                 "    @pytest.mark.parametrize('value',[1,2])\n"
                 "    def test_case(self,value): assert value>0\n")
        self.sha=self.commit();v10.stage(self.repo,self.sha,self.dest)
        r=self.run_native(("tests/test_classes.py::TestWitness::test_case",))
        self.assertEqual(r["status"],"PASS_SCOPED_NATIVE")
        self.assertEqual(r["junit"]["passed"],2)
        self.assertEqual(len(r["executed"]),2)


if __name__=="__main__":
    unittest.main()
