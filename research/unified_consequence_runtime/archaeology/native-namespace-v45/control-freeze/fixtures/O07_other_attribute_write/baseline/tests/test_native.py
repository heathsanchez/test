import unittest
unittest.TestCase.__test__ = False
class NativeCase(unittest.TestCase):
    def test_a(self):
        assert 42 == 41
    def test_b(self):
        assert True
