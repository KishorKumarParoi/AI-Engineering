"""
Dummy test file for testing purposes.
"""

import pytest


def dummy_function(x):
    """A simple dummy function that returns x + 1."""
    return x + 1


def test_dummy_function():
    """Test the dummy function."""
    assert dummy_function(1) == 2
    assert dummy_function(0) == 1
    assert dummy_function(-1) == 0


def test_dummy_function_with_strings():
    """Test dummy function with invalid input."""
    with pytest.raises(TypeError):
        dummy_function("string")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
