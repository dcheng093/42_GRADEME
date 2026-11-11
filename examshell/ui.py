"""Terminal drawing: theme, banner font, cards, bars, prompts."""

import contextlib
import os
import random
import re
import shutil
import sys
import textwrap
import time

from . import config

COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"

# ── theme ───────────────────────────────────────────────────────────────────
ACCENT = 37    # teal: titles, commands, prompt
HILITE = 221   # warm yellow: files, current level, warnings
OK = 78        # green: passed, solved
ERR = 203      # red: failed
MUTED = 245    # grey: labels, hints
LINE = 240     # dark grey: card borders
SHADOW = 238   # banner drop shadow

_STYLES = {
    "bold": "1", "dim": "2", "italic": "3", "under": "4",
    "red": "31", "green": "32", "yellow": "33", "blue": "34",
    "magenta": "35", "cyan": "36", "white": "97", "gray": "90",
}
_ANSI = re.compile(r"\x1b\[[0-9;]*m|[\x01\x02]")


def paint(text, *styles):
    """paint("hi", "bold", ACCENT); ("bg", n) sets a 256-colour background."""
    if not COLOR or not styles:
        return str(text)
    codes = []
    for s in styles:
        if isinstance(s, tuple):
            codes.append(f"48;5;{s[1]}")
        elif isinstance(s, int):
            codes.append(f"38;5;{s}")
        else:
            codes.append(_STYLES[s])
    return f"\x1b[{';'.join(codes)}m{text}\x1b[0m"


def chip(text, bg=ACCENT, fg=16):
    """A solid label: ' PRACTICE ' on a coloured background ([PRACTICE] without colour)."""
    if not COLOR:
        return f"[{text}]"
    return paint(f" {text} ", ("bg", bg), fg, "bold")


def visible_len(text):
    return len(_ANSI.sub("", text))


def width():
    return min(shutil.get_terminal_size((80, 24)).columns, 100)


def clear():
    if sys.stdout.isatty():
        sys.stdout.write("\x1b[H\x1b[2J\x1b[3J")
        sys.stdout.flush()


# ── block font ──────────────────────────────────────────────────────────────
_FONT = {
    "A": (" ## ", "#  #", "####", "#  #", "#  #"),
    "B": ("### ", "#  #", "### ", "#  #", "### "),
    "C": (" ###", "#   ", "#   ", "#   ", " ###"),
    "D": ("### ", "#  #", "#  #", "#  #", "### "),
    "E": ("####", "#   ", "### ", "#   ", "####"),
    "F": ("####", "#   ", "### ", "#   ", "#   "),
    "G": (" ###", "#   ", "# ##", "#  #", " ###"),
    "H": ("#  #", "#  #", "####", "#  #", "#  #"),
    "I": ("###", " # ", " # ", " # ", "###"),
    "J": ("  ##", "   #", "   #", "#  #", " ## "),
    "K": ("#  #", "# # ", "##  ", "# # ", "#  #"),
    "L": ("#   ", "#   ", "#   ", "#   ", "####"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #"),
    "O": (" ## ", "#  #", "#  #", "#  #", " ## "),
    "P": ("### ", "#  #", "### ", "#   ", "#   "),
    "Q": (" ## ", "#  #", "#  #", "# ##", " ###"),
    "R": ("### ", "#  #", "### ", "# # ", "#  #"),
    "S": (" ###", "#   ", " ## ", "   #", "### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#  #", "#  #", "#  #", "#  #", " ## "),
    "V": ("#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "# # #", "## ##", "#   #"),
    "X": ("#   #", " # # ", "  #  ", " # # ", "#   #"),
    "Y": ("#   #", " # # ", "  #  ", "  #  ", "  #  "),
    "Z": ("####", "   #", " ## ", "#   ", "####"),
    "0": (" ## ", "#  #", "#  #", "#  #", " ## "),
    "1": (" # ", "## ", " # ", " # ", "###"),
    "2": ("### ", "   #", " ## ", "#   ", "####"),
    "3": ("### ", "   #", " ## ", "   #", "### "),
    "4": ("#  #", "#  #", "####", "   #", "   #"),
    "5": ("####", "#   ", "### ", "   #", "### "),
    "6": (" ## ", "#   ", "### ", "#  #", " ## "),
    "7": ("####", "   #", "  # ", " #  ", " #  "),
    "8": (" ## ", "#  #", " ## ", "#  #", " ## "),
    "9": (" ## ", "#  #", " ###", "   #", " ## "),
    "!": ("#", "#", "#", " ", "#"),
    "/": ("   #", "  # ", " #  ", "#   ", "    "),
    " ": ("  ", "  ", "  ", "  ", "  "),
}


def _big_rows(text):
    glyphs = [_FONT[ch] for ch in text.upper() if ch in _FONT]
    rows = [" ".join(g[r] for g in glyphs).replace("#", "█") for r in range(5)]
    return [r.replace("█", "██").replace(" ", "  ") for r in rows]


def _big_fits(rows, indent):
    return len(rows[0]) + 1 + indent <= width()


def _big_cells(rows, color):
    """Grid of (char, colour) cells: solid letters plus a grey drop shadow one row taller."""
    w = len(rows[0]) + 1
    filled = [[c < len(r) and r[c] == "█" for c in range(w)] for r in rows]
    filled.append([False] * w)
    grid = []
    for r in range(len(filled)):
        cells = []
        for c in range(w):
            if filled[r][c]:
                cells.append(("█", color))
            elif r and c and filled[r - 1][c - 1]:
                cells.append(("░", SHADOW))
            else:
                cells.append((" ", None))
        grid.append(cells)
    return grid


def _render(grid, indent=2):
    out = []
    for cells in grid:
        line, run, run_color = "", "", None
        for ch, col in cells + [("", "end")]:
            if col != run_color:
                line += paint(run, run_color) if run_color else run
                run, run_color = "", col
            run += ch
        out.append(" " * indent + line.rstrip())
    return "\n".join(out)


def big(text, color=ACCENT, indent=2):
    """Render text in the block font, solid colour with a grey drop shadow."""
    rows = _big_rows(text)
    if not _big_fits(rows, indent):
        return " " * indent + paint(text, color, "bold")
    if not COLOR:
        return "\n".join(" " * indent + r for r in rows)
    return _render(_big_cells(rows, color), indent)


# ── animation ───────────────────────────────────────────────────────────────
GLEAM = 231  # bright white: shimmer and flash
CONFETTI = "✦*·•+"


def animated():
    return COLOR and sys.stdout.isatty() and config.ANIMATIONS


@contextlib.contextmanager
def _quiet_keyboard():
    """No echo while animating, and drop anything typed meanwhile (so a stray
    Enter doesn't answer the next prompt)."""
    try:
        import termios
        fd = sys.stdin.fileno()
        saved = termios.tcgetattr(fd)
        quiet = list(saved)
        quiet[3] &= ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSADRAIN, quiet)
    except Exception:  # noqa: BLE001 - no tty, no termios (Windows): just animate
        yield
        return
    try:
        yield
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, saved)
            termios.tcflush(fd, termios.TCIFLUSH)
        except termios.error:
            pass


def play(frames, delay=0.03):
    """Draw multi-line frames in place. A frame is a string or (string, seconds).

    Without a terminal (or with animations off) only the last frame is printed.
    Ctrl-C skips straight to the last frame.
    """
    frames = [f if isinstance(f, tuple) else (f, delay) for f in frames]
    if not frames:
        return
    if not animated():
        print(frames[-1][0])
        return
    height = max(text.count("\n") + 1 for text, _ in frames)
    out, drawn = sys.stdout, False

    def draw(text):
        nonlocal drawn
        lines = text.split("\n")
        lines += [""] * (height - len(lines))
        out.write((f"\x1b[{height}F" if drawn else "") + "".join(f"\r{l}\x1b[K\n" for l in lines))
        out.flush()
        drawn = True

    out.write("\x1b[?25l")
    try:
        with _quiet_keyboard():
            try:
                for i, (text, pause) in enumerate(frames):
                    draw(text)
                    if i + 1 < len(frames):
                        time.sleep(pause)
            except KeyboardInterrupt:
                draw(frames[-1][0])
    finally:
        out.write("\x1b[?25h")
        out.flush()


def _recolor(grid, fn):
    """Copy of `grid` with each letter cell's colour replaced by fn(row, col, colour)."""
    return [[(ch, fn(r, c, col)) if ch == "█" else (ch, col) for c, (ch, col) in enumerate(row)]
            for r, row in enumerate(grid)]


def _shimmer(grid, indent, step=4, band=3, delay=0.015):
    """A diagonal band of light sweeping left to right across the letters."""
    w, h = len(grid[0]), len(grid)
    return [(_render(_recolor(grid, lambda r, c, col: GLEAM if 0 <= c - r - p < band else col), indent), delay)
            for p in range(-band, w + h, step)]


_REVEALED = set()


def reveal(text, color=ACCENT, indent=2):
    """Print a banner: wipe in left to right the first time, then a shimmer."""
    rows = _big_rows(text)
    if not (animated() and _big_fits(rows, indent)):
        print(big(text, color, indent))
        return
    grid = _big_cells(rows, color)
    frames = []
    if text not in _REVEALED:
        _REVEALED.add(text)
        blank = (" ", None)
        frames += [(_render([[cell if c < cut else blank for c, cell in enumerate(row)] for row in grid],
                            indent), 0.018)
                   for cut in range(0, len(grid[0]), 3)]
    frames += _shimmer(grid, indent)
    frames.append(_render(grid, indent))
    play(frames)


def pass_banner(text="PASSED", color=OK, indent=2):
    """Two quick white flashes, then a shimmer."""
    rows = _big_rows(text)
    if not (animated() and _big_fits(rows, indent)):
        print(big(text, color, indent))
        return
    grid = _big_cells(rows, color)
    lit = _render(_recolor(grid, lambda r, c, col: GLEAM), indent)
    calm = _render(grid, indent)
    play([(lit, 0.07), (calm, 0.07), (lit, 0.07), (calm, 0.05)] + _shimmer(grid, indent) + [calm])


def fail_banner(text="FAILED", color=ERR, indent=2):
    """A short sideways shake."""
    rows = _big_rows(text)
    if not (animated() and _big_fits(rows, indent + 4)):
        print(big(text, color, indent))
        return
    grid = _big_cells(rows, color)
    play([(_render(grid, indent + offset), 0.045) for offset in (3, -2, 2, -1, 1, 0)])


def confetti(text, color=OK, indent=2, count=34):
    """The banner with sparkles falling through it (only over empty cells)."""
    rows = _big_rows(text)
    if not (animated() and _big_fits(rows, indent)):
        print(big(text, color, indent))
        return
    grid = _big_cells(rows, color)
    h, w = len(grid), len(grid[0])
    colors = (OK, HILITE, ACCENT, 213)
    bits = [(random.randrange(w), -random.randrange(18), random.choice(CONFETTI), random.choice(colors))
            for _ in range(count)]
    frames = []
    for f in range(18 + h):
        frame = [list(row) for row in grid]
        for x, start, ch, col in bits:
            y = start + f
            if 0 <= y < h and frame[y][x][0] == " ":
                frame[y][x] = (CONFETTI[(CONFETTI.index(ch) + f // 3) % len(CONFETTI)], col)
        frames.append((_render(frame, indent), 0.04))
    frames.append(_render(grid, indent))
    play(frames)


def count_up(make_frame, start, end, duration=0.7, max_frames=20):
    """Ease-out tween: frames make_frame(v) for v from start to end (ints)."""
    n = max(2, min(max_frames, abs(end - start) + 1))
    values = []
    for i in range(n):
        t = i / (n - 1)
        v = round(start + (end - start) * (1 - (1 - t) ** 3))
        if not values or v != values[-1]:
            values.append(v)
    play([(make_frame(v), duration / len(values)) for v in values])


# ── layout pieces ───────────────────────────────────────────────────────────
def card_width():
    return width() - 4


def rule(char="─", color=LINE):
    return paint(char * (width() - 2), color)


def _fit(line, room):
    """Wrap plain lines that are too long; truncate coloured ones."""
    if visible_len(line) <= room:
        return [line]
    if _ANSI.search(line):
        return [_ANSI.sub("", line)[:room - 1] + "…"]
    lead = len(line) - len(line.lstrip(" "))
    return textwrap.wrap(line, room, subsequent_indent=" " * (lead + 2),
                         drop_whitespace=False, break_on_hyphens=False) or [""]


def card(lines, title="", right="", color=LINE, title_color=ACCENT):
    """Full-width rounded card. All cards share one width so they stack neatly."""
    w = card_width()
    room = w - 4
    left = paint("╭─ ", color) + paint(title, title_color, "bold") + " " if title else paint("╭", color)
    tail = (" " + right + " " + paint("─╮", color)) if right else paint("╮", color)
    dashes = max(w - visible_len(left) - visible_len(tail), 0)
    out = [left + paint("─" * dashes, color) + tail]
    for line in lines:
        for piece in _fit(line.replace("\t", "    "), room):
            gap = max(room - visible_len(piece), 0)
            out.append(paint("│", color) + " " + piece + " " * (gap + 1) + paint("│", color))
    out.append(paint("╰" + "─" * (w - 2) + "╯", color))
    return "\n".join("  " + l for l in out)


def command_card(commands, title="commands", footer="", color=LINE):
    """Commands one per line: ▸ name   what it does."""
    pad = max(visible_len(n) for n, _ in commands)
    lines = [paint("▸ ", ACCENT) + paint(n, ACCENT, "bold") + " " * (pad - visible_len(n) + 3) + d
             for n, d in commands]
    if footer:
        lines += ["", paint(footer, MUTED)]
    return card(lines, title=title, color=color)


def status_strip(left, right=""):
    gap = width() - visible_len(left) - visible_len(right) - 2
    return " " + left + " " * max(gap, 2) + right


def bar(fraction, size=20, color=OK):
    fraction = max(0.0, min(1.0, fraction))
    filled = round(fraction * size)
    return paint("█" * filled, color) + paint("░" * (size - filled), LINE)


def level_bar(solved, total, size=12):
    return bar(solved / total if total else 0, size) + " " + paint(f"{solved}/{total} solved", MUTED)


def roadmap(rank, current, passed):
    """● L1 ━━ ● L2 ━━ ◉ L3 ━━ ○ L4 ..."""
    parts = []
    for i in range(len(rank.levels)):
        if i < passed:
            dot = paint("●", OK)
        elif i == current:
            dot = paint("◉", HILITE, "bold")
        else:
            dot = paint("○", MUTED)
        label = paint(f"L{i + 1}", HILITE, "bold") if i == current else paint(f"L{i + 1}", MUTED)
        parts.append(f"{dot} {label}")
    return paint(" ━━ ", LINE).join(parts)


def duration(seconds):
    seconds = max(int(seconds), 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}"


def indent_block(text, prefix="  "):
    return "\n".join(prefix + line for line in text.splitlines())


def say(text, color=MUTED, *styles):
    print("  " + paint(text, color, *styles))


# ── input ───────────────────────────────────────────────────────────────────
try:
    import readline  # noqa: F401  (line editing + history for input())
except ImportError:
    pass


def _rl_safe(text):
    """Wrap colour codes so readline measures the prompt width correctly."""
    return re.sub(r"(\x1b\[[0-9;]*m)", "\x01\\1\x02", text)


def ask(label="", symbol="❯", color=ACCENT):
    prompt = (paint(label, MUTED) + " " if label else "") + paint(symbol, color, "bold") + " "
    return input(_rl_safe("  " + prompt)).strip()


def pause(text="press enter to continue"):
    input(_rl_safe("  " + paint(text, MUTED, "italic") + " "))


def confirm(question, default_yes=False):
    hint = " [Y/n] " if default_yes else " [y/N] "
    answer = input(_rl_safe("  " + paint(question, HILITE) + paint(hint, MUTED))).strip().lower()
    return answer in ("y", "yes") or (default_yes and answer == "")


def menu(title, options, footer=""):
    """options: list of (key, label, hint). Returns the chosen key, or None for back.

    An option with key None is a section header: options are then listed
    compactly under their headers.
    """
    lines = []
    real = [o for o in options if o[0] is not None]
    sections = len(real) != len(options)
    pad = max(len(label) for _, label, _ in real)
    keyw = max(len(str(k)) for k, _, _ in real)
    for i, (key, label, hint) in enumerate(options):
        if key is None:
            if i:
                lines.append("")
            lines.append(paint(label.upper(), ACCENT, "bold"))
            continue
        if i and not sections:
            lines.append("")
        k = chip(f"{key:^{keyw}}")
        lines.append(f"{k}  {paint(f'{label:<{pad}}', 'bold')}" + (f"   {paint(hint, MUTED)}" if hint else ""))
    if footer:
        lines += ["", paint(footer, MUTED)]
    print(card(lines, title=title))
    print()
    keys = {str(k).lower(): k for k, _, _ in real}
    while True:
        choice = ask().lower()
        if choice in keys:
            return keys[choice]
        if choice in ("", "b", "back", "menu"):
            return None
        if choice in ("q", "quit", "exit"):
            raise SystemExit(0)
        print("  " + paint(f"'{choice}' is not an option", ERR))
