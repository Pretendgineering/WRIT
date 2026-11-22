"""Interactive shell: command loop, builtins, completion and splash."""
from writ.shell import SPLASH, completions, run_shell, splash_width


def _run(lines):
    """Run the shell over scripted input; returns the unread remainder."""
    feed = iter(lines)

    def read_line():
        try:
            return next(feed)
        except StopIteration:
            raise EOFError

    run_shell(read_line=read_line, show_splash=False)
    return list(feed)


def test_shell_runs_commands_and_survives_errors(cli, capsys):
    leftover = _run([
        "jn 3 16",            # default lookup without the 'writ' prefix
        "writ ge 1 1",        # habitual prefix is tolerated
        "xyz 1",              # unknown book: error, shell keeps going
        "set kjv",            # helpful hint
        '"unclosed quote',    # unparseable line
        "",                   # blank line ignored
        "bm add favs",        # bookmarks the last verse read (Genesis 1:1)
        "bm list",
        "quit",
        "ge 1 2",             # must never run
    ])
    out = " ".join(capsys.readouterr().out.split())
    assert "so loved the world" in out
    assert "In the beginning" in out
    assert "unknown book 'xyz'" in out
    assert "writ set translation kjv" in out
    assert "couldn't read that line" in out
    assert "favs Genesis 1:1" in out
    assert "bm add NAME" in out          # shell shows a hint, not a keypress bar
    assert "[b]ookmark" not in out
    assert leftover == ["ge 1 2"]


def test_shell_exits_on_eof_and_resets_mode(cli):
    import writ.cli

    assert _run(["help"]) == []
    assert writ.cli.SHELL_MODE is False


def test_help_builtin_shows_command_help(cli, capsys):
    _run(["help search", "q"])
    assert "Full-text search" in capsys.readouterr().out


def test_completions():
    assert "search" in completions([], "se")
    assert "setup" in completions([], "se")
    assert "jn" in completions([], "j")
    assert completions(["bm"], "") == ["add", "list", "go", "remove"]
    assert completions(["plan", "load"], "go") == ["gospels"]
    assert completions(["writ", "plan"], "st") == ["status"]
    assert completions(["ge", "1"], "") == []


def test_splash_is_ten_lines_and_fits_80_columns():
    assert len(SPLASH) == 10
    assert splash_width() <= 78
