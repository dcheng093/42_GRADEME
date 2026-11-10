"""Rank03 test harness. Runs in a subprocess:

    python3 -m examshell.harness <question_dir> <candidate.py>

Exit 0 = every check passed, 1 = failed / crashed.
"""

import contextlib
import importlib.util
import io
import sys
import time
import traceback
from pathlib import Path

from . import ui

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class CheckFailed(Exception):
    def __init__(self, number, description, result, expected, errors):
        super().__init__(description)
        self.number, self.description = number, description
        self.result, self.expected, self.errors = result, expected, errors


class Checker:
    """The `check` callable handed to every tests.py `run()`."""

    def __init__(self, out):
        self.out = out
        self.live = out.isatty()
        self.count = 0
        self._last_draw = 0.0

    def __call__(self, description, result, expected=None, errors=None):
        self.count += 1
        passed = result if expected is None else result == expected
        if not passed:
            raise CheckFailed(self.count, description, result, expected, errors)
        now = time.monotonic()
        if self.live and now - self._last_draw > 0.03:
            self._last_draw = now
            frame = SPINNER[self.count % len(SPINNER)]
            self.out.write(f"\r  {ui.paint(frame, 207)} {self.count} checks passed")
            self.out.flush()


def _clear_line(out):
    if out.isatty():
        out.write("\r\x1b[K")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _card(title, rows, color="red"):
    out = ["  " + ui.paint("✘ " + title, color, "bold")]
    for label, value in rows:
        lines = str(value).splitlines() or [""]
        for i, line in enumerate(lines):
            tag = ui.paint(f"{label:<9}", "gray") if i == 0 and label else " " * 9
            out.append(f"  {ui.paint('│', color)} {tag} {line}")
    return "\n".join(out)


def _crash_location(error, candidate):
    """Last traceback frame inside the student's file, if any."""
    frames = [f for f in traceback.extract_tb(error.__traceback__)
              if Path(f.filename).resolve() == candidate.resolve()]
    return frames[-1] if frames else None


def main(argv):
    if len(argv) != 3:
        print("usage: python3 -m examshell.harness QUESTION_DIR CANDIDATE", file=sys.stderr)
        return 2
    sys.dont_write_bytecode = True
    qdir, candidate = Path(argv[1]), Path(argv[2])
    question = qdir.name
    out = sys.stdout
    checker = Checker(out)
    captured = io.StringIO()  # anything the student's code prints

    tests = load_module(f"tests_{question}", qdir / "tests.py")
    script_mode = getattr(tests, "MODE", "module") == "script"
    module = None

    try:
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        with contextlib.redirect_stdout(captured):
            target = str(candidate) if script_mode else load_module(question, candidate)
            module = target if not script_mode else None
            tests.run(target, checker)
    except CheckFailed as fail:
        _clear_line(out)
        rows = [("check", fail.description)]
        if fail.errors:
            rows += [("", line.strip()) for err in fail.errors for line in str(err).strip().splitlines()]
        elif fail.expected is None:
            rows.append(("got", repr(fail.result)))
        else:
            rows += [("expected", repr(fail.expected)), ("got", repr(fail.result))]
        print(_card(f"check {fail.number} failed  ({fail.number - 1} passed before it)", rows))
        _show_prints(captured)
        return 1
    except KeyboardInterrupt:
        raise
    except BaseException as error:  # noqa: BLE001 - student code can raise anything
        _clear_line(out)
        print(_describe_crash(error, candidate, question, module, checker.count))
        _show_prints(captured)
        return 1

    _clear_line(out)
    print(f"  {ui.paint('✔', 'green', 'bold')} {checker.count}/{checker.count} checks passed")
    return 0


def _describe_crash(error, candidate, question, module, passed):
    rel = f"rendu/{candidate.parent.name}/{candidate.name}"
    if isinstance(error, FileNotFoundError) and not candidate.is_file():
        return _card("file not found", [("expected", rel)])
    if isinstance(error, SyntaxError) and Path(error.filename or "").name == candidate.name:
        return _card("syntax error", [
            ("where", f"{rel} line {error.lineno}"),
            ("code", (error.text or "").rstrip()),
            ("error", error.msg),
        ])
    if isinstance(error, AttributeError) and module is not None and getattr(error, "obj", None) is module:
        return _card("function missing", [
            ("expected", f"def {error.name}(...) in {rel}"),
            ("hint", "check the name in the subject, it must match exactly"),
        ])
    if isinstance(error, SystemExit):
        return _card("your code called exit()", [("after", f"{passed} passing checks")])
    rows = [("error", f"{type(error).__name__}: {error}"), ("after", f"{passed} passing checks")]
    frame = _crash_location(error, candidate)
    if frame:
        rows.insert(1, ("where", f"{rel} line {frame.lineno}"))
        rows.insert(2, ("code", (frame.line or "").strip()))
    return _card("your code crashed", rows)


def _show_prints(captured, limit=8):
    lines = captured.getvalue().splitlines()
    if not lines:
        return
    print("  " + ui.paint(f"your code printed ({len(lines)} lines):", "gray"))
    for line in lines[-limit:]:
        print("    " + ui.paint(line[:200], "gray"))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
