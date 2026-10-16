"""Precommitted V6 typed-source native authority contracts.

These contracts are authored before V6 implementation. V5 inventory and all
original native verifiers must remain byte-identical. No prospective G2, no
unrestricted hostile-Python containment, and no retrospective V5 promotion.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from . import decisive_native_verify as original
from . import typed_source_inventory_v5 as typed
from . import typed_native_authority_v6 as candidate


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], stderr=subprocess.PIPE,
    ).decode().strip()


class FrozenTypedNativeV6(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="v6-typed-native-")
        self.addCleanup(tmp.cleanup)
        self.source=Path(tmp.name).resolve()/"source"
        self.stage_dir=Path(tmp.name).resolve()/"stage"
        self.source.mkdir()
        git(self.source,"init","-q")
        git(self.source,"config","user.name","V6 Frozen Contracts")
        git(self.source,"config","user.email","v6@example.invalid")

    def write(self,path,body):
        f=self.source/path
        f.parent.mkdir(parents=True,exist_ok=True)
        f.write_bytes(body if isinstance(body,bytes) else body.encode())

    def link(self,path,target):
        f=self.source/path
        f.parent.mkdir(parents=True,exist_ok=True)
        os.symlink(target,f)

    def commit(self,gitlink=None):
        git(self.source,"add","-A")
        if gitlink is not None:
            git(self.source,"update-index","--add","--cacheinfo",
                "160000,"+gitlink+",vendor/external")
        git(self.source,"commit","-qm","precommitted typed native source")
        return git(self.source,"rev-parse","HEAD")

    def normal(self, link=True, gitlink=True):
        self.write("pkg/__init__.py","def answer(): return 42\n")
        self.write("docs/intro.rst","Original documentation\n")
        self.write("tests/test_native.py",
                   "from pkg import answer\n"
                   "def test_protected(): assert answer() == 42\n"
                   "def test_other(): assert 1 + 1 == 2\n")
        if link:self.link("README.rst","docs/intro.rst")
        return self.commit("b"*40 if gitlink else None)

    def stage(self,commit):
        return candidate.stage(self.source,commit,self.stage_dir)

    def run_protected(self,commit,required=("tests/test_native.py::test_protected",)):
        return candidate.run_protected(self.source,commit,self.stage_dir,
                                      required=required,interpreter=sys.executable,
                                      timeout=55)

    def test_A01_authentic_regular_link_and_opaque_gitlink_staged_without_flattening(self):
        sha=self.normal()
        old=typed.snapshot(self.source,sha)
        with self.assertRaisesRegex(ValueError,"only regular tracked files"):
            original._snapshot(self.source,sha)
        record=self.stage(sha)
        self.assertEqual(record["status"],"STAGED_TYPED_SOURCE_NO_NATIVE_WARRANT")
        self.assertEqual(record["typed_manifest_sha256"],old["manifest_sha256"])
        self.assertEqual(record["counts"],{"regular":3,"symlink":1,"gitlink":1})
        self.assertTrue((self.stage_dir/"README.rst").is_symlink())
        self.assertEqual(os.readlink(self.stage_dir/"README.rst"),"docs/intro.rst")
        self.assertFalse((self.stage_dir/"vendor/external").exists())
        self.assertEqual((self.stage_dir/"pkg/__init__.py").read_text(),
                         "def answer(): return 42\n")
        self.assertEqual(candidate.verify_stage(self.source,sha,self.stage_dir)["status"],
                         "PASS_TYPED_STAGE_IDENTITY")

    def test_A02_executable_regular_mode_is_preserved(self):
        self.write("bin/exec.py","print('hello')\n")
        os.chmod(self.source/"bin/exec.py",0o755)
        sha=self.commit()
        self.stage(sha)
        self.assertTrue((self.stage_dir/"bin/exec.py").stat().st_mode & 0o100)
        self.assertEqual(candidate.verify_stage(self.source,sha,self.stage_dir)["status"],
                         "PASS_TYPED_STAGE_IDENTITY")

    def test_A03_refuse_absolute_relative_escape_cycles_and_dangling_links(self):
        for name, links in [
            ("absolute",[("README.rst","/etc/passwd")]),
            ("escape",[("README.rst","../outside.txt")]),
            ("cycle",[("link_a","link_b"),("link_b","link_a")]),
            ("dangling",[("README.rst","missing.txt")]),
            ("directory",[("README.rst","docs")]),
            ("gitlink",[("README.rst","vendor/external/executable.py")]),
        ]:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory(prefix="v6-link-neg-") as folder:
                    root=Path(folder).resolve()/"repo"
                    root.mkdir()
                    git(root,"init","-q")
                    git(root,"config","user.name","V6")
                    git(root,"config","user.email","v6@example.invalid")
                    (root/"docs").mkdir()
                    (root/"docs/inside.txt").write_text("data")
                    for name_,target in links:
                        os.symlink(target,root/name_)
                    git(root,"add","-A")
                    if name=="gitlink":
                        git(root,"update-index","--add","--cacheinfo",
                            "160000,"+"c"*40+",vendor/external")
                    git(root,"commit","-qm","untrusted link")
                    sha=git(root,"rev-parse","HEAD")
                    dest=Path(folder).resolve()/"dest"
                    with self.assertRaises(ValueError):
                        candidate.stage(root,sha,dest)
                    self.assertFalse(dest.exists(),"Unsafe link must fail before staging")

    def test_A04_reread_detects_changed_tracked_bytes_and_modes(self):
        sha=self.normal()
        self.stage(sha)
        (self.stage_dir/"pkg/__init__.py").write_text("def answer(): return 0\n")
        with self.assertRaises(ValueError):
            candidate.verify_stage(self.source,sha,self.stage_dir)

    def test_A05_reread_detects_symlink_target_replacement(self):
        sha=self.normal()
        self.stage(sha)
        (self.stage_dir/"README.rst").unlink()
        (self.stage_dir/"README.rst").symlink_to("pkg/__init__.py")
        with self.assertRaises(ValueError):
            candidate.verify_stage(self.source,sha,self.stage_dir)

    def test_A06_unexpected_file_or_opaque_gitlink_materialization_is_refused(self):
        sha=self.normal()
        self.stage(sha)
        (self.stage_dir/"rogue.py").write_text("pass\n")
        with self.assertRaises(ValueError):
            candidate.verify_stage(self.source,sha,self.stage_dir)
        (self.stage_dir/"rogue.py").unlink()
        (self.stage_dir/"vendor/external").mkdir(parents=True)
        with self.assertRaises(ValueError):
            candidate.verify_stage(self.source,sha,self.stage_dir)

    def test_A07_protected_full_native_run_executes_and_checks_import_manifest(self):
        sha=self.normal()
        self.stage(sha)
        receipt=self.run_protected(sha)
        self.assertEqual(receipt["status"],"PASS_SCOPED_NATIVE")
        self.assertEqual(receipt["junit"]["passed"],2)
        self.assertEqual(receipt["junit"]["failed"],0)
        self.assertIn("tests/test_native.py::test_protected",receipt["executed"])
        self.assertIn("pkg/__init__.py",receipt["imported_project_files"])
        self.assertEqual(candidate.verify_stage(self.source,sha,self.stage_dir)["status"],
                         "PASS_TYPED_STAGE_IDENTITY")

    def test_A08_protected_assertion_failure_is_native_failure_not_silent_pass(self):
        self.write("pkg/__init__.py","def answer(): return 41\n")
        self.write("tests/test_native.py",
                   "from pkg import answer\ndef test_protected(): assert answer()==42\n")
        sha=self.commit()
        self.stage(sha)
        receipt=self.run_protected(sha)
        self.assertEqual(receipt["status"],"FAIL_NATIVE_PROTECTED")
        self.assertEqual(receipt["junit"]["failed"],1)
        self.assertNotEqual(receipt["native_exit"],0)

    def test_A09_pytest_skip_never_promotes(self):
        self.write("tests/test_native.py",
                   "import pytest\ndef test_protected(): pytest.skip('not executed')\n")
        sha=self.commit();self.stage(sha)
        receipt=self.run_protected(sha)
        self.assertNotEqual(receipt["status"],"PASS_SCOPED_NATIVE")
        self.assertTrue(receipt["junit"]["skipped"]>0)

    def test_A10_missing_protected_obligation_refuses(self):
        self.write("tests/test_other.py","def test_other(): assert True\n")
        sha=self.commit();self.stage(sha)
        receipt=self.run_protected(sha)
        self.assertEqual(receipt["status"],"UNKNOWN_PROTECTED_NOT_EXECUTED")

    def test_A11_config_deselection_cannot_hide_protected(self):
        self.write("pytest.ini","[pytest]\naddopts = -k other\n")
        self.write("tests/test_native.py",
                   "def test_protected(): assert False\n"
                   "def test_other(): assert True\n")
        sha=self.commit();self.stage(sha)
        receipt=self.run_protected(sha)
        self.assertEqual(receipt["status"],"UNKNOWN_PROTECTED_NOT_EXECUTED")
        self.assertTrue(receipt["deselected"])

    def test_A12_malformed_collected_python_is_not_warranted(self):
        self.write("tests/test_native.py","def test_protected():\n  pass\n    pass\n")
        sha=self.commit();self.stage(sha)
        receipt=self.run_protected(sha)
        self.assertEqual(receipt["status"],"UNKNOWN_NATIVE_COLLECTION")

    def test_A13_native_source_mutation_revokes_post_execution_warrant(self):
        self.write("pkg/__init__.py","def answer(): return 42\n")
        self.write("tests/test_native.py",
                   "from pathlib import Path\n"
                   "def test_protected():\n"
                   "    p=Path(__file__).parent.parent/'pkg'/'__init__.py'\n"
                   "    p.write_text('def answer(): return 42\\n')\n"
                   "    assert True\n")
        sha=self.commit();self.stage(sha)
        receipt=self.run_protected(sha)
        self.assertEqual(receipt["status"],"UNKNOWN_SOURCE_MUTATED")

    def test_A14_symlink_to_imported_python_is_content_bound(self):
        self.write("pkg/__init__.py","")
        self.write("pkg/real.py","VALUE=99\n")
        self.link("pkg/alias.py","real.py")
        self.write("tests/test_native.py",
                   "from pkg.alias import VALUE\n"
                   "def test_protected(): assert VALUE==99\n")
        sha=self.commit();self.stage(sha)
        receipt=self.run_protected(sha)
        self.assertEqual(receipt["status"],"PASS_SCOPED_NATIVE")
        self.assertIn("pkg/real.py",receipt["imported_project_files"])

    def test_A15_no_free_protected_authority_from_gitlink_oid(self):
        sha=self.normal()
        self.stage(sha)
        receipt=self.run_protected(sha,required=("vendor/external/test_special.py::test_missing",))
        self.assertEqual(receipt["status"],"UNKNOWN_PROTECTED_NOT_EXECUTED")


if __name__=="__main__":
    unittest.main()
