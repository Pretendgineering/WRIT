"""Shared fixtures: every test gets an isolated data dir with a tiny Bible."""
import sqlite3

import pytest
from typer.testing import CliRunner


@pytest.fixture()
def cli(tmp_path, monkeypatch):
    import writ.db as db

    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db, "TRANSLATIONS_DIR", tmp_path / "translations")
    monkeypatch.setattr(db, "APP_DB_PATH", tmp_path / "writ.db")
    db.ensure_dirs()
    conn = sqlite3.connect(tmp_path / "translations" / "kjv.db")
    conn.execute("CREATE TABLE verses (book INTEGER, chapter INTEGER, verse INTEGER, text TEXT)")
    conn.executemany("INSERT INTO verses VALUES (?,?,?,?)", [
        (1, 1, 1, "In the beginning God created the heaven and the earth."),
        (1, 1, 2, "And the earth was without form, and void; 100% dark_ness."),
        (43, 3, 16, "For God so loved the world."),
    ])
    conn.commit()
    conn.close()

    from writ.cli import _reroute, app

    runner = CliRunner()

    def run(*args, input="q\n"):
        return runner.invoke(app, _reroute(list(args)), input=input)

    return run
