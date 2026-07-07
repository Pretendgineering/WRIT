import pytest

from writ.lookup import parse_verse_spec


def test_single_verse():
    assert parse_verse_spec("1") == [(1, 1)]


def test_range():
    assert parse_verse_spec("1-3") == [(1, 3)]


def test_list():
    assert parse_verse_spec("1,5") == [(1, 1), (5, 5)]


def test_mixed():
    assert parse_verse_spec("1-3,5,7-9") == [(1, 3), (5, 5), (7, 9)]


def test_whitespace_tolerated():
    assert parse_verse_spec(" 1 - 3 , 5 ") == [(1, 3), (5, 5)]


def test_reversed_range_swapped():
    assert parse_verse_spec("3-1") == [(1, 3)]


@pytest.mark.parametrize("bad", ["abc", "1-abc", "1,,3", "-", "", "1.5"])
def test_invalid_spec_raises_value_error(bad):
    with pytest.raises(ValueError):
        parse_verse_spec(bad)
