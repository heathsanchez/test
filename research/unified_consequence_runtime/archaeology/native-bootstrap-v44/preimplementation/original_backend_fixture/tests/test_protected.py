from native_bootstrap_alpha import protected_value


def test_original_pass():
    assert protected_value() == 41


def test_protected_failure():
    assert protected_value() == 42
