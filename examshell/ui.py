"""Terminal drawing: colours, banner font, boxes, bars, prompts."""

import os
import re
import shutil
import sys

COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"

_STYLES = {
    "bold": "1", "dim": "2", "italic": "3", "under": "4",
    "red": "31", "green": "32", "yellow": "33", "blue": "34",
    "magenta": "35", "cyan": "36", "white": "97", "gray": "90",
}
_ANSI = re.compile(r"\x1b\[[0-9;]*m|[\x01\x02]")

GRADIENT = (51, 45, 39, 33, 63, 99, 135, 171, 207, 213, 207, 171, 135, 99, 63, 33, 39, 45)


def paint(text, *styles):
    """paint("hi", "bold", "cyan") or paint("hi", 207) for a 256-colour code."""
    if not COLOR or not styles:
        return str(text)
    codes = [f"38;5;{s}" if isinstance(s, int) else _STYLES[s] for s in styles]
    return f"\x1b[{';'.join(codes)}m{text}\x1b[0m"


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


def big(text, colors=GRADIENT, indent=2):
    """Render text in the block font. A single int colour paints it flat."""
    glyphs = [_FONT[ch] for ch in text.upper() if ch in _FONT]
    rows = [" ".join(g[r] for g in glyphs).replace("#", "█") for r in range(5)]
    rows = [r.replace("█", "██").replace(" ", "  ") for r in rows]
    if len(rows[0]) + indent > width():
        return " " * indent + paint(text, "bold")
    if isinstance(colors, int):
        colors = (colors,)
    out = []
    for row in rows:
        line = "".join(
            paint(ch, colors[(i // 4) % len(colors)]) if ch != " " else " "
            for i, ch in enumerate(row)
        )
        out.append(" " * indent + line)
    return "\n".join(out)


# ── layout pieces ───────────────────────────────────────────────────────────
def rule(char="─", color="gray"):
    return paint(char * (width() - 2), color)


def box(lines, title="", color="cyan", pad=1):
    """Rounded box sized to its content (capped at terminal width)."""
    inner = max([visible_len(l) for l in lines] + [visible_len(title) + 2]) + pad * 2
    inner = min(inner, width() - 4)
    if title:
        out = [paint("╭─ ", color) + paint(title, "bold") + paint(" " + "─" * (inner - visible_len(title) - 3) + "╮", color)]
    else:
        out = [paint("╭" + "─" * inner + "╮", color)]
    for line in lines:
        if visible_len(line) > inner - pad * 2:
            line = _ANSI.sub("", line)[:inner - pad * 2 - 1] + "…"
        gap = max(inner - pad * 2 - visible_len(line), 0)
        out.append(paint("│", color) + " " * pad + line + " " * (gap + pad) + paint("│", color))
    out.append(paint("╰" + "─" * inner + "╯", color))
    return "\n".join("  " + l for l in out)


def bar(fraction, size=20, color="green"):
    fraction = max(0.0, min(1.0, fraction))
    filled = round(fraction * size)
    return paint("█" * filled, color) + paint("░" * (size - filled), "gray")


def roadmap(rank, current, passed):
    """L1 ●━━ L2 ●━━ L3 ◉━━ L4 ○ ..."""
    parts = []
    for i in range(len(rank.levels)):
        if i < passed:
            dot = paint("●", "green")
        elif i == current:
            dot = paint("◉", "yellow", "bold")
        else:
            dot = paint("○", "gray")
        parts.append(f"{dot} {paint(f'L{i + 1}', 'bold' if i == current else 'gray')}")
    return paint(" ━━ ", "gray").join(parts)


def duration(seconds):
    seconds = max(int(seconds), 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}"


def indent_block(text, prefix="  "):
    return "\n".join(prefix + line for line in text.splitlines())


# ── input ───────────────────────────────────────────────────────────────────
try:
    import readline  # noqa: F401  (line editing + history for input())
except ImportError:
    pass


def _rl_safe(text):
    """Wrap colour codes so readline measures the prompt width correctly."""
    return re.sub(r"(\x1b\[[0-9;]*m)", "\x01\\1\x02", text)


def ask(label="", symbol="❯", color=207):
    prompt = (paint(label, "gray") + " " if label else "") + paint(symbol, color, "bold") + " "
    return input(_rl_safe("  " + prompt)).strip()


def pause(text="press enter to continue"):
    input(_rl_safe("  " + paint(text, "gray", "italic") + " "))


def confirm(question):
    answer = input(_rl_safe("  " + paint(question, "yellow") + paint(" [y/N] ", "gray"))).strip().lower()
    return answer in ("y", "yes")


def menu(title, options, footer=""):
    """options: list of (key, label, hint). Returns the chosen key, or None for back."""
    lines = []
    pad = max(len(label) for _, label, _ in options)
    for key, label, hint in options:
        k = paint(f"{key:>2}", 207, "bold")
        lines.append(f"{k}  {paint(f'{label:<{pad}}', 'bold')}" + (f"   {paint(hint, 'gray')}" if hint else ""))
    print(box(lines, title=title))
    if footer:
        print("  " + paint(footer, "gray"))
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
        print("  " + paint(f"'{choice}' is not an option", "red"))
