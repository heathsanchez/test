"""Qualification of *candidate* verifier V2; original pinned V1 is retained elsewhere."""
import unittest
from .decisive_native_verify import _declared_addopts, _test_nodes
class V2PolicyTests(unittest.TestCase):
    def test_known_options(self):
        for s in ('--import-mode=importlib','-l','--import-mode=append -q','--import-mode=prepend --tb=short'):
            with self.subTest(s=s):_declared_addopts(s)
    def test_unknown_options(self):
        for s in ('--import-mode=evil','--override-ini=pythonpath=/tmp','-p evil','--confcutdir=/tmp','--ignore=tests','-k','--import-mode','--import-mode=importlib;rm'):
            with self.subTest(s=s):
                with self.assertRaises(ValueError):_declared_addopts(s)
    def test_static_data_not_disguised_test(self):
        tree,nodes=_test_nodes('tests/test_sample.py',b'test_inputs = (1,2,3)\ndef test_actual():\n assert True\n')
        self.assertEqual(nodes,['tests/test_sample.py::test_actual'])
    def test_dynamic_alias_refusal(self):
        for source in (b'test_inputs = get_data()\n',b'test_alias = real_test\n',
                       b'test_alias = lambda: None\n',b'globals()["test_x"] = lambda: None\n'):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):_test_nodes('tests/test_sample.py',source)
if __name__=='__main__':unittest.main()
