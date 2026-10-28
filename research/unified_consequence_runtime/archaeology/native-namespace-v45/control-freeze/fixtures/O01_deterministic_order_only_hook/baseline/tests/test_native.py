import unittest
def reverse_names(left, right):
    return (left < right) - (left > right)
unittest.TestLoader.sortTestMethodsUsing = staticmethod(reverse_names)
class NativeCase(unittest.TestCase):
    def test_a(self):
        assert 42 == 41
    def test_b(self):
        assert True
