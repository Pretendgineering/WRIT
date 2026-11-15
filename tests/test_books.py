from writ.books import resolve_book, book_by_number, BOOKS


def test_all_66_books_present():
    assert len(BOOKS) == 66


def test_resolve_by_short_abbrev():
    assert resolve_book("ge").name  == "Genesis"
    assert resolve_book("jn").name  == "John"
    assert resolve_book("re").name  == "Revelation"
    assert resolve_book("ps").name  == "Psalms"
    assert resolve_book("1co").name == "1 Corinthians"
    assert resolve_book("2jn").name == "2 John"


def test_resolve_case_insensitive():
    assert resolve_book("GE")  is resolve_book("ge")
    assert resolve_book("JN")  is resolve_book("jn")
    assert resolve_book("1CO") is resolve_book("1co")


def test_resolve_full_name():
    assert resolve_book("genesis").number   == 1
    assert resolve_book("Genesis").number   == 1
    assert resolve_book("revelation").number == 66


def test_resolve_full_name_no_space():
    assert resolve_book("1samuel").number == 9
    assert resolve_book("1john").number   == 62


def test_resolve_unknown():
    assert resolve_book("xyz") is None
    assert resolve_book("")    is None


def test_book_by_number():
    assert book_by_number(1).name  == "Genesis"
    assert book_by_number(66).name == "Revelation"
    assert book_by_number(0)       is None
    assert book_by_number(67)      is None


def test_john_disambiguation():
    jn   = resolve_book("jn")
    one  = resolve_book("1jn")
    two  = resolve_book("2jn")
    three= resolve_book("3jn")
    assert jn.number    == 43
    assert one.number   == 62
    assert two.number   == 63
    assert three.number == 64


def test_no_duplicate_abbrevs_across_books():
    seen: dict[str, str] = {}
    for book in BOOKS:
        for abbrev in book.abbrevs:
            assert abbrev not in seen, (
                f"abbrev '{abbrev}' claimed by both {seen.get(abbrev)} and {book.name}"
            )
            seen[abbrev] = book.name


def test_chapter_counts_sane():
    total = sum(b.chapters for b in BOOKS)
    assert total == 1189  # canonical Protestant chapter count


def test_roman_numeral_names():
    # scrollmapper CSVs use these forms
    assert resolve_book("I Samuel").number == 9
    assert resolve_book("II Kings").number == 12
    assert resolve_book("II Chronicles").number == 14
    assert resolve_book("I Corinthians").number == 46
    assert resolve_book("III John").number == 64
    assert resolve_book("ii peter").number == 61


def test_alternate_names():
    assert resolve_book("Revelation of John").number == 66
    assert resolve_book("Psalm").number == 19
    assert resolve_book("Song of Songs").number == 22


def test_song_alias():
    assert resolve_book("song").number == 22
