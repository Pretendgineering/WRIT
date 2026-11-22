"""Interactive shell: a bare `writ` opens a persistent prompt.

Every command that works as `writ <args>` works here without the `writ`
prefix — `jn 3 16`, `search faith`, `bm list` — plus a few shell builtins
(help, clear, quit).
"""
from __future__ import annotations

import shlex
from typing import Callable, Optional

import typer
from rich.text import Text

from . import __version__
from .display import console, print_error

# Blackletter "WRIT", drawn on a 20-pixel grid and rendered with half-block
# characters (two pixels per character cell), so it is 10 lines tall.
SPLASH = [
    '▄ ▄█▄     ▄█▄     ▄█▄      ▄ ▄█▄ ▄▄▄▄▄▄▄     ▄ ▄█▄       ▄▄▄▄▄▄▄▄▄▄▄▄▄▄',
    ' ▀████   ▀████   ▀████      ▀████ ▀▀▀▀▀███▄   ▀████    ▄▀▀▀▀▀████▀▀▀▀█▀▀',
    '  ████    ████    ████       ████       ███    ████    ▀▄    ████     ▀',
    '  ████    ████    ████       ████    ▄▄██▀     ████          ████',
    '  ████    ████    ████       ████▄███▀▀      ▄ ████ ▄        ████',
    '  ████    ████    ████       ████  ▀██▄       ▀████▀         ████',
    '  ████   ▄████   ▄████       ████    ▀██▄      ████          ████',
    '  ████ ▄▀ ████ ▄▀ ████       ████      ▀██▄    ████▄         ████▄',
    '   ▀█▀▀    ▀█▀▀    ▀█▀        ▀█▀        █▀     ▀█▀           ▀█▀',
    '                                          ▀',
]

# Deep red fading to gold, one colour per line of the splash.
_SPLASH_COLOURS = [
    "#7a0b0b", "#8f1414", "#a31d1d", "#b5291f", "#c43d1f",
    "#cf5622", "#d87128", "#e08d30", "#e7a83b", "#edc24a",
]

BUILTINS_EXIT = {"exit", "quit", "q"}
BUILTINS_CLEAR = {"clear", "cls"}
BUILTINS_HELP = {"help", "?"}

# readline treats text between \001 and \002 as zero-width, so the colour
# codes don't break cursor positioning when editing a line.
_PROMPT = "\001\033[1;31m\002writ\001\033[0m\002 \001\033[2m\002›\001\033[0m\002 "


# ── Splash ────────────────────────────────────────────────────────────────────

def splash_width() -> int:
    return max(len(line) for line in SPLASH)


def print_splash() -> None:
    from .db import list_translations

    console.print()
    width = splash_width()
    if console.width >= width + 2:
        # Centre the art as one block. (Centring line by line would shift the
        # shorter lines, since trailing padding is ignored.)
        margin = " " * ((console.width - width) // 2)
        for line, colour in zip(SPLASH, _SPLASH_COLOURS):
            console.print(Text.assemble(margin, (line, f"bold {colour}")), no_wrap=True, overflow="crop")
    else:
        # Terminal too narrow for the full art.
        console.print(Text("W R I T", style="bold #c43d1f"), justify="center")
    console.print()
    console.print(
        f"[dim]v{__version__} · type a passage like[/dim] [bold]jn 3 16[/bold] "
        "[dim]·[/dim] [bold]help[/bold] [dim]for commands ·[/dim] "
        "[bold]quit[/bold] [dim]to exit[/dim]",
        justify="center",
    )
    if not list_translations():
        console.print(
            "[yellow]No Bible installed yet — type[/yellow] [bold]setup[/bold] "
            "[yellow]to download the King James Bible.[/yellow]",
            justify="center",
        )
    console.print()


# ── Tab completion ────────────────────────────────────────────────────────────

_SUBCOMMANDS = {
    "bookmark": ["add", "list", "go", "remove"],
    "bm":       ["add", "list", "go", "remove"],
    "note":     ["add", "list", "remove"],
    "plan":     ["load", "list", "set", "status"],
    "set":      ["translation", "plan"],
}


def _top_level_words() -> list[str]:
    from .books import BOOKS
    from .cli import _command_names

    commands = _command_names() - {"lookup"}
    builtins = BUILTINS_EXIT | BUILTINS_CLEAR | BUILTINS_HELP
    books = {b.abbrevs[0] for b in BOOKS}
    return sorted(commands | builtins | books)


def completions(words: list[str], current: str) -> list[str]:
    """Candidates for the word being typed, given the complete words before it."""
    if words and words[0] == "writ":
        words = words[1:]
    if not words:
        pool = _top_level_words()
    elif words[0] in ("help", "?") and len(words) == 1:
        pool = sorted(set(_top_level_words()) - BUILTINS_EXIT - BUILTINS_CLEAR - BUILTINS_HELP)
    elif len(words) == 1 and words[0] in _SUBCOMMANDS:
        pool = _SUBCOMMANDS[words[0]]
    elif len(words) == 2 and words[0] == "plan" and words[1] == "load":
        from .plans import bundled_plans
        pool = sorted(bundled_plans())
    elif len(words) == 2 and words[0] == "plan" and words[1] == "set":
        from .plans import list_plans
        pool = list_plans()
    elif len(words) == 2 and words[0] == "set":
        from .db import list_translations
        from .plans import list_plans
        pool = list_translations() if words[1] == "translation" else list_plans()
    else:
        pool = []
    return [p for p in pool if p.startswith(current)]


def _setup_readline() -> Optional[Callable[[], None]]:
    """Enable line editing, history and tab completion. Returns a save-history hook."""
    try:
        import readline
    except ImportError:  # e.g. Windows without pyreadline
        return None

    from .db import DATA_DIR, ensure_dirs

    ensure_dirs()
    history_file = DATA_DIR / "shell_history"
    try:
        readline.read_history_file(history_file)
    except OSError:
        pass
    readline.set_history_length(1000)

    def complete(text: str, state: int) -> Optional[str]:
        before = readline.get_line_buffer()[: readline.get_begidx()]
        matches = completions(before.split(), text)
        return matches[state] + " " if state < len(matches) else None

    readline.set_completer(complete)
    readline.set_completer_delims(" \t")
    if "libedit" in (readline.__doc__ or ""):  # macOS system Python
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    def save() -> None:
        try:
            readline.write_history_file(history_file)
        except OSError:
            pass

    return save


# ── Command loop ──────────────────────────────────────────────────────────────

def _dispatch(command, args: list[str]) -> None:
    """Run one command line; never let a failure end the shell."""
    from .cli import _reroute

    try:
        command.main(args=_reroute(args), prog_name="writ", standalone_mode=True)
    except SystemExit:
        pass  # every click command ends this way, success or not
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
    except KeyboardInterrupt:
        console.print()
    except Exception as exc:  # pragma: no cover - defensive
        print_error(f"unexpected error: {exc}")


def run_shell(
    read_line: Optional[Callable[[], str]] = None,
    show_splash: bool = True,
) -> None:
    """Run the interactive prompt until the user quits.

    read_line is injectable for tests; by default it reads from the terminal
    with line editing, history and tab completion.
    """
    from . import cli

    save_history = None
    if read_line is None:
        save_history = _setup_readline()
        read_line = lambda: input(_PROMPT)  # noqa: E731

    command = typer.main.get_command(cli.app)
    cli.SHELL_MODE = True
    if show_splash:
        print_splash()

    try:
        while True:
            try:
                line = read_line()
            except EOFError:  # Ctrl-D
                console.print()
                break
            except KeyboardInterrupt:  # Ctrl-C clears the line, like a normal shell
                console.print()
                continue

            try:
                args = shlex.split(line)
            except ValueError as exc:  # e.g. an unclosed quote
                print_error(f"couldn't read that line: {exc}")
                continue
            if args and args[0] == "writ":  # tolerate habitual 'writ ...'
                args = args[1:]
            if not args:
                continue

            head = args[0].lower()
            if head in BUILTINS_EXIT:
                break
            if head in BUILTINS_CLEAR:
                console.clear()
                continue
            if head in BUILTINS_HELP:
                args = [*args[1:], "--help"]

            _dispatch(command, args)
    finally:
        cli.SHELL_MODE = False
        if save_history:
            save_history()
