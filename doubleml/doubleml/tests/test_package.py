"""Test the dml package."""


def test_version_is_string():
    import doubleml
    assert isinstance(doubleml.__version__, str)

