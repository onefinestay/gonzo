import pytest

from gonzo.utils import last_index


def test_last_index():
    assert last_index([1, 1], 1) == 1
    assert last_index([1, 1, 2], 1) == 1


def test_last_index_missing():
    with pytest.raises(ValueError):
        last_index([1], 2)


def test_last_index_empty():
    with pytest.raises(ValueError):
        last_index([], 1)
