class Dummy:
    pass
unittest = Dummy()
unittest.TestLoader = Dummy()
def reverse_names(left, right):
    return 0
unittest.TestLoader.sortTestMethodsUsing = staticmethod(reverse_names)
def test_contract():
    assert 1 == 2
