import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('reviewer',Path(__file__).parents[1]/'reviewer.py')
reviewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer)

class NativeBoundary(unittest.TestCase):
    def test_python_introduced_parse_regression_witness(self):
        with tempfile.TemporaryDirectory() as root:
            repo=Path(root)
            def git(*args):
                r=subprocess.run(['git',*args],cwd=repo,text=True,capture_output=True)
                self.assertEqual(r.returncode,0,r.stderr)
                return r.stdout.strip()
            git('init','-q');git('config','user.email','ci@example.invalid');git('config','user.name','fixture')
            (repo/'candidate.py').write_text('def f():\n    return 1\n')
            git('add','.');git('commit','-qm','base');base=git('rev-parse','HEAD')
            (repo/'candidate.py').write_text('def f():\n    return (\n')
            git('add','.');git('commit','-qm','head');head=git('rev-parse','HEAD')
            reviewer.source_identity(repo,base,head)
            findings,records=reviewer.syntax_witnesses(repo,base,head)
            self.assertEqual(len(findings),1)
            self.assertEqual(records[0]['status'],'WITNESSED_COMPILER_REGRESSION')
            (repo/'candidate.py').write_text('def f():\n    return 1\n')
            git('add','.');git('commit','-qm','repair')
            repair=git('rev-parse','HEAD')
            self.assertEqual(reviewer.syntax_witnesses(repo,head,repair)[0],[])
            with self.assertRaisesRegex(ValueError,'HEAD mismatch'):
                reviewer.source_identity(repo,base,head)

    def test_go_parser_native_boundary(self):
        if not reviewer.command('which','gofmt').returncode:
            self.assertIsNone(reviewer.parse_failure('x.go','package main\nfunc ok() {}\n'))
            self.assertIsNotNone(reviewer.parse_failure('x.go','package main\nfunc fail( {\n'))

    def test_no_spurious_positive(self):
        self.assertIsNone(reviewer.parse_failure('candidate.py','def f():\n    return 1\n'))
        self.assertTrue(reviewer.parse_failure('candidate.py','def f(:\n'))

    def test_malformed_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            repo=Path(root)
            (repo/'candidate.py').write_text('x=1\n')
            good,bad=reviewer.validate([{'file':'../../unsafe.py','start_line':1,'end_line':1,'message':'bad'},
                 {'file':'candidate.py','start_line':1,'end_line':1,'message':'possible'}],
                 ['candidate.py'],repo,'test')
            self.assertEqual(bad,1);self.assertEqual(len(good),1)

if __name__ == '__main__':
    unittest.main()
