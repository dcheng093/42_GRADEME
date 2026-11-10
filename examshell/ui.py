"""Terminal drawing: theme, banner font, cards, bars, prompts."""

import os
import re
import shutil
import sys
import textwrap

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


def big(text, color=ACCENT, indent=2):
    """Render text in the block font, solid colour with a grey drop shadow."""
    glyphs = [_FONT[ch] for ch in text.upper() if ch in _FONT]
    rows = [" ".join(g[r] for g in glyphs).replace("#", "█") for r in range(5)]
    rows = [r.replace("█", "██").replace(" ", "  ") for r in rows]
    if len(rows[0]) + 1 + indent > width():
        return " " * indent + paint(text, color, "bold")
    if not COLOR:
        return "\n".join(" " * indent + r for r in rows)
    w = len(rows[0]) + 1
    filled = [[c < len(r) and r[c] == "█" for c in range(w)] for r in rows]
    filled.append([False] * w)
    out = []
    for r in range(len(filled)):
        cells = []
        for c in range(w):
            if filled[r][c]:
                cells.append(("█", color))
            elif r and c and filled[r - 1][c - 1]:
                cells.append(("░", SHADOW))
            else:
                cells.append((" ", None))
        line, run, run_color = "", "", None
        for ch, col in cells + [("", "end")]:
            if col != run_color:
                line += paint(run, run_color) if run_color else run
                run, run_color = "", col
            run += ch
        out.append(" " * indent + line.rstrip())
    return "\n".join(out)


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
    """options: list of (key, label, hint). Returns the chosen key, or None for back."""
    lines = []
    pad = max(len(label) for _, label, _ in options)
    keyw = max(len(str(k)) for k, _, _ in options)
    for i, (key, label, hint) in enumerate(options):
        if i:
            lines.append("")
        k = chip(f"{key:^{keyw}}")
        lines.append(f"{k}  {paint(f'{label:<{pad}}', 'bold')}" + (f"   {paint(hint, MUTED)}" if hint else ""))
    if footer:
        lines += ["", paint(footer, MUTED)]
    print(card(lines, title=title))
    print()
    keys = {str(k).lower(): k for k, _, _ in options}
    while True:
        choice = ask().lower()
        if choice in keys:
            return keys[choice]
        if choice in ("", "b", "back", "menu"):
            return None
        if choice in ("q", "quit", "exit"):
            raise SystemExit(0)
        print("  " + paint(f"'{choice}' is not an option", ERR))
