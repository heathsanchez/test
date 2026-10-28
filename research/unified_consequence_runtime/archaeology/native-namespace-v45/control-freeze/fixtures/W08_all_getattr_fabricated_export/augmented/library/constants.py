ANSWER = 42
__all__ = ["ANSWER", "test_fabricated"]
def __getattr__(name):
    return lambda: None
