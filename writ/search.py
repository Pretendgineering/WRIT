from .books import book_by_number
from .db import get_translation_db

RESULT_CAP = 100


def search_text(translation: str, query: str, book_num: int | None = None) -> list[dict]:
    conn = get_translation_db(translation)
    try:
        # Escape LIKE wildcards so '%' and '_' in the query match literally.
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        if book_num:
            rows = conn.execute(
                "SELECT book, chapter, verse, text FROM verses "
                "WHERE book=? AND text LIKE ? ESCAPE '\\' ORDER BY book, chapter, verse LIMIT ?",
                (book_num, pattern, RESULT_CAP),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT book, chapter, verse, text FROM verses "
                "WHERE text LIKE ? ESCAPE '\\' ORDER BY book, chapter, verse LIMIT ?",
                (pattern, RESULT_CAP),
            ).fetchall()

        result = []
        for r in rows:
            book = book_by_number(r["book"])
            result.append({
                "book_name":   book.name if book else f"Book {r['book']}",
                "chapter":     r["chapter"],
                "verse":       r["verse"],
                "text":        r["text"],
                "translation": translation,
            })
        return result
    finally:
        conn.close()
