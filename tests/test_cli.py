"""End-to-end CLI tests against a tiny throwaway translation."""

import pytest


def test_default_lookup(cli):
    result = cli("ge", "1", "1")
    assert result.exit_code == 0
    assert "In the beginning" in result.output


def test_options_before_book(cli):
    result = cli("-t", "kjv", "jn", "3", "16")
    assert result.exit_code == 0
    assert "so loved the world" in result.output


@pytest.mark.parametrize("args, fragment", [
    (("xyz", "1"), "unknown book"),
    (("ge", "abc"), "invalid chapter"),
    (("ge", "0"), "no chapter 0"),
    (("ge", "51"), "no chapter 51"),
    (("set", "kjv"), "writ set translation kjv"),
    (("set", "translation", "esv"), "not installed"),
    (("search", "  "), "nothing to search"),
    (("bm", "add", "x", "ge", "99", "1"), "no chapter 99"),
])
def test_friendly_errors(cli, args, fragment):
    result = cli(*args)
    assert result.exit_code == 1
    assert fragment in " ".join(result.output.split())


def test_search_treats_wildcards_literally(cli):
    assert "1 result" in cli("search", "100%").output
    assert "1 result" in cli("search", "dark_ness").output
    assert "no results" in cli("search", "dark%ness").output


def test_bookmark_roundtrip(cli):
    assert cli("bm", "add", "favs/john", "jn", "3", "16").exit_code == 0
    assert "John 3:16" in cli("bm", "list").output
    assert "so loved" in cli("bm", "go", "1").output
    assert cli("bm", "remove", "1").exit_code == 0
    assert cli("bm", "remove", "1").exit_code == 1


def test_history_collapses_repeats(cli):
    for _ in range(3):
        cli("ge", "1", "1")
    assert cli("history").output.count("Genesis 1:1") == 1


def test_plan_reload_keeps_progress_unless_confirmed(cli):
    assert cli("plan", "load", "gospels", input="y\n").exit_code == 0
    cli("done")
    assert "kept the existing plan" in cli("plan", "load", "gospels", input="n\n").output
    assert "1/89" in cli("plan", "status").output


def test_version(cli):
    from writ import __version__
    assert __version__ in cli("--version").output
