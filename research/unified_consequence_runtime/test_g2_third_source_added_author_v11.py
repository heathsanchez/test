"""Frozen V1.1 apparatus regression: exact contributor NEW test absent at BASE.

No external target source appears in any fixture. Method, source roles and oracle
are unchanged; tests only admit an *author-supplied* newly added original test.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

from . import g2_third_source_added_author_v11 as v11
from . import g2_pool_first_native_failure_v1 as old


class SourceOwnedAddedTestV11(unittest.TestCase):
    def setUp(self):
        self.context=tempfile.TemporaryDirectory()
        self.addCleanup(self.context.cleanup)
        self.root=Path(self.context.name)
        subprocess.run(["git","init","-q",str(self.root)],check=True)
        self.git("config","user.email","test@example.invalid")
        self.git("config","user.name","Native Author")
        (self.root/"src").mkdir()
        (self.root/"src/core.py").write_text("def f(): return 1\n")
        self.git("add",".")
        self.git("commit","-qm","source")
        self.base=self.git("rev-parse","HEAD")

    def git(self,*args):
        x=subprocess.check_output(["git","-C",str(self.root),*args],text=True)
        return x.strip()

    def new_head(self):
        (self.root/"test").mkdir(exist_ok=True)
        path=self.root/"test/test_genuine.py"
        path.write_text("def test_original_author():\n    assert 1 == 2\n")
        self.git("add","test/test_genuine.py")
        self.git("commit","-qm","author test")
        return self.git("rev-parse","HEAD")

    def test_01_protected_first_new_author_test_absent_at_base(self):
        head=self.new_head()
        b,h,kind=v11.author_blobs(self.root,self.base,head,"test/test_genuine.py")
        self.assertEqual(b,b"")
        self.assertIn(b"assert",h)
        self.assertEqual(kind,"AUTHOR_HEAD_ADDED_TEST")
        self.assertEqual(old.select_protected(b,h,"test/test_genuine.py"),
                         ["test/test_genuine.py::test_original_author"])

    def test_02_original_existing_author_test_stays_byte_exact(self):
        head=self.new_head()
        b,h,kind=v11.author_blobs(self.root,head,head,"test/test_genuine.py")
        self.assertEqual(kind,"AUTHOR_BASE_EXISTS")
        self.assertEqual(b,h)

    def test_03_missing_head_author_test_fails_closed(self):
        with self.assertRaises(ValueError):
            v11.author_blobs(self.root,self.base,self.base,"test/test_missing.py")

    def test_04_forged_symlink_author_test_fails_closed(self):
        (self.root/"test").mkdir(exist_ok=True)
        (self.root/"test/test_genuine.py").symlink_to("../src/core.py")
        self.git("add",".")
        self.git("commit","-qm","symlink")
        head=self.git("rev-parse","HEAD")
        with self.assertRaises(ValueError):
            v11.author_blobs(self.root,self.base,head,"test/test_genuine.py")

    def test_05_intent_to_add_exact_head_file_remains_only_author_diff(self):
        head=self.new_head()
        self.git("checkout","-q","--detach",self.base)
        b,h,kind=v11.author_blobs(self.root,self.base,head,"test/test_genuine.py")
        v11.stage_author_overlay(self.root,"test/test_genuine.py",h,kind)
        self.assertEqual(self.git("diff","--name-only"),"test/test_genuine.py")
        self.assertEqual((self.root/"src/core.py").read_text(),"def f(): return 1\n")
        self.assertEqual((self.root/"test/test_genuine.py").read_bytes(),h)

    def test_06_wrong_source_commit_refused(self):
        head=self.new_head()
        with self.assertRaises(ValueError):
            v11.author_blobs(self.root,"b"*40,head,"test/test_genuine.py")


if __name__=="__main__":
    unittest.main()
