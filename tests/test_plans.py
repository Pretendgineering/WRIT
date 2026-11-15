from writ.plans import _parse_line, bundled_plans


def test_plain_entry():
    entry = _parse_line("ge 1")
    assert entry == {"book": 1, "chapter_start": 1, "chapter_end": 1, "target_date": None}


def test_chapter_range():
    entry = _parse_line("mt 1-3")
    assert entry["chapter_start"] == 1
    assert entry["chapter_end"] == 3


def test_dated_entry():
    entry = _parse_line("2026-01-01 ge 1-2")
    assert entry["target_date"] == "2026-01-01"
    assert entry["book"] == 1
    assert entry["chapter_end"] == 2


def test_comment_and_blank_lines_skipped():
    assert _parse_line("# comment") is None
    assert _parse_line("") is None
    assert _parse_line("   ") is None


def test_unknown_book_skipped():
    assert _parse_line("xyz 1") is None


def test_malformed_chapter_skipped():
    assert _parse_line("ge one") is None
    assert _parse_line("ge 1-x") is None


def test_reversed_range_normalized():
    entry = _parse_line("ge 3-1")
    assert (entry["chapter_start"], entry["chapter_end"]) == (1, 3)


def test_bundled_plans_present_and_parseable():
    plans = bundled_plans()
    assert {"gospels", "new-testament", "psalms-and-proverbs"} <= set(plans)
    for path in plans.values():
        entries = [e for e in (_parse_line(l) for l in path.read_text().splitlines()) if e]
        assert entries, f"no entries parsed from {path}"


def test_daily_verses_parseable():
    from writ.daily import _load_refs
    from writ.books import resolve_book

    refs = _load_refs()
    assert len(refs) > 50
    for abbrev, chapter, verse in refs:
        book = resolve_book(abbrev)
        assert book is not None, f"unknown book abbrev '{abbrev}' in daily_verses.txt"
        assert 1 <= chapter <= book.chapters, f"{abbrev} {chapter} out of range"
        assert verse >= 1


def test_chapter_beyond_book_skipped():
    assert _parse_line("ge 51") is None
    assert _parse_line("ge 0") is None
