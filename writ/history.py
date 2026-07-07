from datetime import datetime, timezone

from .books import book_by_number
from .db import get_app_db

_MAX_HISTORY = 500   # cap rows stored


def _to_local(ts: str) -> str:
    """SQLite CURRENT_TIMESTAMP is UTC; render in the user's local time."""
    try:
        dt = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).astimezone()
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts


def record(translation: str, book_num: int, chapter: int,
           verse_start: int | None = None, verse_end: int | None = None) -> None:
    conn = get_app_db()
    try:
        # Re-reading the same passage back-to-back just refreshes its timestamp,
        # so history doesn't fill with consecutive duplicates.
        last = conn.execute(
            "SELECT id, translation, book, chapter, verse_start, verse_end "
            "FROM history ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if (
            last
            and last["translation"] == translation
            and last["book"] == book_num
            and last["chapter"] == chapter
            and last["verse_start"] == verse_start
            and last["verse_end"] == verse_end
        ):
            conn.execute(
                "UPDATE history SET accessed_at=CURRENT_TIMESTAMP WHERE id=?",
                (last["id"],),
            )
        else:
            conn.execute(
                "INSERT INTO history (translation, book, chapter, verse_start, verse_end) VALUES (?,?,?,?,?)",
                (translation, book_num, chapter, verse_start, verse_end),
            )
        # Prune oldest rows beyond cap
        conn.execute(
            "DELETE FROM history WHERE id NOT IN "
            "(SELECT id FROM history ORDER BY id DESC LIMIT ?)",
            (_MAX_HISTORY,),
        )
        conn.commit()
    finally:
        conn.close()


def get_history(limit: int = 20) -> list[dict]:
    conn = get_app_db()
    try:
        rows = conn.execute(
            "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        result = []
        for r in rows:
            book = book_by_number(r["book"])
            result.append({
                "translation": r["translation"],
                "book_name":   book.name if book else f"Book {r['book']}",
                "chapter":     r["chapter"],
                "verse_start": r["verse_start"],
                "verse_end":   r["verse_end"],
                "accessed_at": _to_local(r["accessed_at"]),
            })
        return result
    finally:
        conn.close()


def get_last_position() -> dict | None:
    conn = get_app_db()
    try:
        row = conn.execute(
            "SELECT * FROM history ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        book = book_by_number(row["book"])
        return {
            "translation": row["translation"],
            "book":        row["book"],
            "book_name":   book.name if book else f"Book {row['book']}",
            "chapter":     row["chapter"],
        }
    finally:
        conn.close()


def get_reading_streak() -> int:
    """Count consecutive distinct calendar days with at least one history entry."""
    from datetime import date, timedelta

    conn = get_app_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT date(accessed_at, 'localtime') AS d FROM history ORDER BY d DESC"
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return 0

    today = date.today()
    streak = 0
    expected = today

    for row in rows:
        d = date.fromisoformat(row["d"])
        if d == expected:
            streak += 1
            expected -= timedelta(days=1)
        elif d == today - timedelta(days=1) and streak == 0:
            # Allow yesterday to start streak (not yet read today)
            streak += 1
            expected = d - timedelta(days=1)
        else:
            break

    return streak
