import unittest
import os
SALT = os.urandom(10)
def random_names(left, right):
    return (hash(SALT + left.encode()) > hash(SALT + right.encode())) - (hash(SALT + left.encode()) < hash(SALT + right.encode()))
unittest.TestLoader.sortTestMethodsUsing = staticmethod(random_names)
class NativeCase(unittest.TestCase):
    def test_a(self):
        assert 42 == 41
    def test_b(self):
        assert True
