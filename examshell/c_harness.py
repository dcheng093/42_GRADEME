"""Rank02 test harness. Runs in a subprocess:

    python3 -m examshell.c_harness <question_dir> <candidate.c>

Compiles the reference (<question>.c) and your file once each, plus main.c for
function exercises, then runs both on every argv list in cases.json and compares
stdout. Exit 0 = every case passed, 1 = failed, 2 = the subject itself is broken.
"""

import json
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from . import ui
from .harness import _card, _clear_line

CASE_TIMEOUT = 3  # seconds per run
STRICT = ["-Wall", "-Wextra", "-Werror"]
SHOW_LINES = 10  # of expected/got output
MAX_DOTS = 40

CRASHES = {
    "SIGSEGV": "segmentation fault (bad pointer? NULL? out of bounds?)",
    "SIGBUS": "bus error (bad pointer?)",
    "SIGABRT": "abort (double free? corrupted malloc?)",
    "SIGFPE": "floating point exception (division by zero?)",
}


class Fail(Exception):
    """A finished verdict: print `card`, exit with `code`."""

    def __init__(self, card, code=1):
        super().__init__(card)
        self.card, self.code = card, code


# ── compiling ───────────────────────────────────────────────────────────────
def _compiler():
    return shutil.which("gcc") or shutil.which("cc") or "gcc"


def _build(qdir, candidate, tmp):
    """Compile reference and candidate in parallel. Returns (ref, user) binaries."""
    extra = [str(qdir / "main.c")] if (qdir / "main.c").is_file() else []
    ref, user = tmp / "ref", tmp / "user"
    cc = _compiler()
    jobs = {
        "ref": subprocess.Popen([cc, "-w", "-o", str(ref), str(qdir / f"{qdir.name}.c"), *extra],
                                cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                errors="replace"),
        "user": subprocess.Popen([cc, *STRICT, "-fdiagnostics-color=never", "-o", str(user),
                                  str(candidate), *extra],
                                 cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                 errors="replace"),
    }
    logs = {name: proc.communicate()[0] for name, proc in jobs.items()}
    if jobs["ref"].returncode:
        raise Fail(_card("the reference solution doesn't compile (bug in this tool)",
                         [("output", "\n".join(logs["ref"].splitlines()[:8]))]), code=2)
    if jobs["user"].returncode:
        raise Fail(_compile_card(logs["user"], qdir, candidate))
    return ref, user


_DIAG = re.compile(r"^(.+?):(\d+):(?:\d+:)? (?:fatal )?error: (.+)$")
_LINK = re.compile(r"(undefined reference to|multiple definition of) [`'‘]([^'’`]+)['’]")


def _rel(path, qdir, candidate):
    path = Path(path)
    if path.name == candidate.name and path.resolve() == candidate.resolve():
        return f"rendu/{candidate.parent.name}/{candidate.name}"
    if path.resolve().parent == qdir.resolve():
        return f"{path.name} (the test's own file)"
    return str(path)


def _compile_card(log, qdir, candidate):
    errors = [m for m in map(_DIAG.match, log.splitlines()) if m]
    if errors:
        mine = [m for m in errors if Path(m.group(1)).resolve() == candidate.resolve()]
        first = (mine or errors)[0]
        path, line, msg = Path(first.group(1)), int(first.group(2)), first.group(3)
        try:
            code = path.read_text(errors="replace").splitlines()[line - 1].strip()
        except (OSError, IndexError):
            code = ""
        rows = [("where", f"{_rel(path, qdir, candidate)} line {line}"), ("code", code), ("error", msg)]
        if "-Werror" in msg:
            rows.append(("hint", "warnings count as errors in the exam"))
        if len(errors) > 1:
            rows.append(("", ui.paint(f"+{len(errors) - 1} more error{'s' * (len(errors) > 2)}", ui.MUTED)))
        return _card("doesn't compile  (gcc -Wall -Wextra -Werror)", rows)

    link = _LINK.search(log)
    if link:
        kind, name = link.groups()
        if kind == "undefined reference to":
            hint = ("this exercise is a program: it needs a main()" if name == "main"
                    else "check the function name and prototype in the subject")
            return _card("link error", [("missing", name), ("hint", hint)])
        hint = ("function exercises must not have a main(), the test brings its own" if name == "main"
                else "it is defined twice")
        return _card("link error", [("duplicate", name), ("hint", hint)])

    lines = [l for l in log.splitlines() if l.strip()]
    return _card("doesn't compile  (gcc -Wall -Wextra -Werror)", [("gcc", "\n".join(lines[:8]))])


# ── running ─────────────────────────────────────────────────────────────────
def _exec(binary, argv):
    """(stdout bytes, returncode); returncode None = timed out."""
    try:
        proc = subprocess.run([str(binary), *argv], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, timeout=CASE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return b"", None
    return proc.stdout, proc.returncode


_BARE = re.compile(r"[\w@%+=:,./-]+")


def _command(name, argv):
    """./prog "arg one" two  — quoted the way you would type it."""
    def quote(arg):
        if _BARE.fullmatch(arg):
            return arg
        return '"' + re.sub(r'([\\"$`])', r"\\\1", arg) + '"'
    return " ".join([f"./{name}", *map(quote, argv)])


def _signal_name(code):
    try:
        return signal.Signals(-code).name
    except ValueError:
        return f"signal {-code}"


# ── drawing ─────────────────────────────────────────────────────────────────
def _strip(states, total):
    """●●●●✘○○○ for small counts, a bar for big ones."""
    if total > MAX_DOTS:
        ok = sum(1 for s in states if s == "ok")
        return ui.bar(ok / total, 20, ui.OK if "fail" not in states else ui.ERR)
    marks = {"ok": ui.paint("●", ui.OK), "fail": ui.paint("✘", ui.ERR, "bold"),
             "run": ui.paint("◉", ui.HILITE)}
    return "".join(marks[s] for s in states) + ui.paint("○" * (total - len(states)), ui.MUTED)


def _draw(out, states, total):
    if out.isatty():
        done = sum(1 for s in states if s == "ok")
        out.write(f"\r  {_strip(states, total)}  {ui.paint(f'{done}/{total}', ui.MUTED)}\x1b[K")
        out.flush()


def _visible(data, diff_at=None, other_len=None):
    """cat -e style rendering: `$` marks each newline, → a tab, ^X a control char.

    Highlights the character at `diff_at` (or a gap if the output stops there).
    Returns a list of display lines.
    """
    text = data.decode(errors="replace")
    lines, cur = [], ""
    for i, ch in enumerate(text):
        if ch == "\n":
            shown, special = "$", True
        elif ch == "\t":
            shown, special = "→", True
        elif ord(ch) < 32 or ord(ch) == 127:
            shown, special = "^" + chr((ord(ch) + 64) % 128), True
        else:
            shown, special = ch, False
        if i == diff_at:
            cur += ui.paint(shown, ("bg", ui.ERR), 16, "bold")
        else:
            cur += ui.paint(shown, ui.MUTED) if special else shown
        if ch == "\n":
            lines.append(cur)
            cur = ""
    if diff_at is not None and diff_at >= len(text) and other_len and other_len > len(text) and ui.COLOR:
        cur += ui.paint(" ", ("bg", ui.ERR))  # the output stops where it should go on
    if cur or not lines:
        lines.append(cur)
    return lines


def _window(lines, focus):
    """At most SHOW_LINES lines, keeping line `focus` in view."""
    start = 0 if focus < SHOW_LINES else focus - 2
    shown = lines[start:start + SHOW_LINES]
    if start:
        shown.insert(0, ui.paint(f"… {start} line{'s' * (start > 1)} above", ui.MUTED))
    rest = len(lines) - start - SHOW_LINES
    if rest > 0:
        shown.append(ui.paint(f"… {rest} more line{'s' * (rest > 1)}", ui.MUTED))
    return "\n".join(shown)


def _output_rows(expected, got):
    exp_t, got_t = expected.decode(errors="replace"), got.decode(errors="replace")
    diff = next((i for i, (a, b) in enumerate(zip(exp_t, got_t)) if a != b), min(len(exp_t), len(got_t)))
    focus = exp_t.count("\n", 0, diff)
    rows = []
    for label, data, mark, other in (("expected", expected, None, None),
                                      ("got", got, diff, len(exp_t))):
        if not data:
            rows.append((label, ui.paint("(no output)", ui.MUTED, "italic")))
        else:
            rows.append((label, _window(_visible(data, mark, other), focus)))
    if focus >= SHOW_LINES:
        rows.append(("first diff", f"line {focus + 1}"))
    return rows


# ── main ────────────────────────────────────────────────────────────────────
def run(qdir, candidate, out):
    rel = f"rendu/{candidate.parent.name}/{candidate.name}"
    if not candidate.is_file():
        raise Fail(_card("file not found", [("expected", rel)]))
    cases = json.loads((qdir / "cases.json").read_text())
    total = len(cases)

    with tempfile.TemporaryDirectory(prefix="examshell-") as tmp:
        if out.isatty():
            out.write(f"  {ui.paint('◌', ui.ACCENT)} {ui.paint('compiling…', ui.MUTED)}")
            out.flush()
        try:
            ref, user = _build(qdir, candidate, Path(tmp))
        finally:
            _clear_line(out)

        states = []
        for n, argv in enumerate(cases, 1):
            _draw(out, states + ["run"], total)
            expected, ref_code = _exec(ref, argv)
            got, code = _exec(user, argv)
            run_line = _command(qdir.name, argv)
            before = f"case {n} of {total}, {n - 1} passed before it"
            card = None
            if ref_code is None:
                card = _card("the reference solution timed out (bug in this tool)", [("run", run_line)])
                raise Fail(card, code=2)
            if code is None:
                card = _card(f"timed out after {CASE_TIMEOUT}s  ({before})", [
                    ("run", run_line), ("hint", "infinite loop? (or waiting for input)")])
            elif code < 0 <= ref_code:
                name = _signal_name(code)
                card = _card(f"your program crashed  ({before})", [
                    ("run", run_line), ("signal", f"{name}: {CRASHES.get(name, 'killed')}"),
                    *_output_rows(expected, got)])
            elif got != expected:
                card = _card(f"wrong output  ({before})", [("run", run_line), *_output_rows(expected, got)])
            if card:
                _clear_line(out)
                print(f"  {_strip(states + ['fail'], total)}  {ui.paint(f'{n - 1}/{total}', ui.MUTED)}")
                raise Fail(card)
            states.append("ok")
    return total


def main(argv):
    if len(argv) != 3:
        print("usage: python3 -m examshell.c_harness QUESTION_DIR CANDIDATE", file=sys.stderr)
        return 2
    qdir, candidate = Path(argv[1]).resolve(), Path(argv[2]).resolve()  # gcc runs in a temp dir
    out = sys.stdout
    start = time.monotonic()
    try:
        total = run(qdir, candidate, out)
    except Fail as fail:
        _clear_line(out)
        print(fail.card)
        return fail.code
    _clear_line(out)
    took = ui.paint(f"· {time.monotonic() - start:.2f}s", ui.MUTED)
    print(f"  {ui.paint('✔', ui.OK, 'bold')} {total}/{total} checks passed  "
          f"{_strip(['ok'] * total, total)}  {took}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
