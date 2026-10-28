ANSWER = 42
VALUES = (41, 42)
class Node:
    pass
def describe():
    return ANSWER
_hidden = 99
class TestForeign:
    def test_injected(self):
        assert True
