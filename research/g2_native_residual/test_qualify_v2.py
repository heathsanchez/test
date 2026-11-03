"""Source-neutral regression test for newly introduced author Go tests.

This controlled local fixture is not a new external G2 result.
"""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from qualify_v2 import qualify,decode_go_events


def call(cwd, *args):
    p=subprocess.run(args,cwd=cwd,capture_output=True,text=True,timeout=20)
    if p.returncode:raise AssertionError(f'{args}: {p.stderr}')
    return p.stdout.strip()


class NativeAuthorAdmissionV2Tests(unittest.TestCase):
    def test_zero_work_is_unknown(self):
        self.assertEqual(decode_go_events('{"Action":"pass","Package":"x"}',0)['status'], 'UNKNOWN_ZERO_RECOGNIZED_TESTS')

    def test_compiler_error_is_not_native_assertion(self):
        self.assertEqual(decode_go_events('{"Action":"output","Output":"compile failure"}',1)['status'],'UNKNOWN_ZERO_RECOGNIZED_TESTS')

    def test_empty_new_test_file_is_not_eligible(self):
        self.assertEqual(decode_go_events('',1)['status'],'UNKNOWN_ZERO_RECOGNIZED_TESTS')

    def test_new_file_native_assertion_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'source';root.mkdir()
            call(root,'git','init','-q');call(root,'git','config','user.email','fixture@example.invalid');call(root,'git','config','user.name','Fixture')
            (root/'go.mod').write_text('module example.com/mathgraph-fixture\n\ngo 1.20\n')
            (root/'source.go').write_text('package fixture\nfunc Probe(i int) int { return i+1 }\n')
            (root/'baseline_test.go').write_text('package fixture\nimport "testing"\nfunc TestBaseline(t *testing.T){ if Probe(0)<0 { t.Fatal("invalid") } }\n')
            call(root,'git','add','.');call(root,'git','commit','-qm','base')
            base=call(root,'git','rev-parse','HEAD')
            (root/'source.go').write_text('package fixture\nfunc Probe(i int) int { return i+2 }\n')
            (root/'new_protected_test.go').write_text('package fixture\nimport "testing"\nfunc TestAuthorNew(t *testing.T){ if Probe(1)!=3 { t.Fatalf("expected 3, got %d",Probe(1)) } }\n')
            call(root,'git','add','.');call(root,'git','commit','-qm','head')
            head=call(root,'git','rev-parse','HEAD')
            receipt=qualify(root,base,head,'new_protected_test.go',Path(d)/'qualification')
            self.assertEqual(receipt['status'],'WARRANTED_BOUNDED_AUTHENTIC_AUTHOR_NATIVE_RED_GREEN',receipt)
            self.assertEqual(receipt['original_base']['status'],'PASS_NONEMPTY')
            self.assertEqual(receipt['base_transplant']['status'],'FAIL_NATIVE_ASSERTIONS')
            self.assertEqual(receipt['head_contributor']['status'],'PASS_NONEMPTY')
            self.assertIn('TestAuthorNew',receipt['matched_failed_tests'])
            self.assertEqual(receipt['base_test_exists'],False)


if __name__=='__main__':unittest.main()