import unittest
from pytest_admission import admit
class AdmissionTests(unittest.TestCase):
    def test_scope(self):
        for c in ('python -m pytest --import-mode=importlib tests','pytest -l tests','python3 -m pytest -q tests'):
            self.assertEqual(admit(c,authorized_roots=('tests',),authorized=True).status,'ADMIT_SCOPED')
    def test_unknown(self):
        self.assertEqual(admit('pytest tests',authorized_roots=('tests',),authorized=False).status,'UNKNOWN_SOURCE_AUTHORITY')
    def test_reject(self):
        for c in ('pytest -k exploit tests','pytest --override-ini=pythonpath=/tmp tests','pytest ../tests',
          'pytest /tmp/evil','pytest tests/../../etc','pytest tests; echo pwn','python -c print',
          'bash -c pytest','pytest','pytest other_tests','pytest --import-mode=unknown tests',
          'pytest -p bad tests','pytest \'bad'):
            with self.subTest(c=c):
                self.assertEqual(admit(c,authorized_roots=('tests',),authorized=True).status,'REJECT')
if __name__=='__main__':unittest.main()
