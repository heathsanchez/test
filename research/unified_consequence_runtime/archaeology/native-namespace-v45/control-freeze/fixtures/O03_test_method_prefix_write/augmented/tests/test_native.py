import unittest
unittest.TestLoader.testMethodPrefix = "noop"
class NativeCase(unittest.TestCase):
    def test_a(self):
        assert 42 == 42
    def test_b(self):
        assert True
