"""Rank03 test harness. Runs in a subprocess:

    python3 -m examshell.harness <question_dir> <candidate.py>

Exit 0 = every check passed, 1 = failed / crashed.
"""

import ast
import contextlib
import importlib.util
import io
import json
import sys
import time
import traceback
from pathlib import Path
from types import ModuleType
from typing import IO

from . import ui

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class CheckFailed(Exception):
    def __init__(
        self,
        number: int,
        description: str,
        result: object,
        expected: object,
        errors: list[str] | None,
    ) -> None:
        super().__init__(description)
        self.number, self.description = number, description
        self.result, self.expected, self.errors = result, expected, errors


class Checker:
    """The `check` callable handed to every tests.py `run()`."""

    def __init__(self, out: IO[str]) -> None:
        self.out = out
        self.live = out.isatty()
        self.count = 0
        self._last_draw = 0.0

    def __call__(
        self,
        description: str,
        result: object,
        expected: object = None,
        errors: list[str] | None = None,
    ) -> None:
        self.count += 1
        passed = result if expected is None else result == expected
        if not passed:
            raise CheckFailed(
                self.count, description, result, expected, errors
            )
        now = time.monotonic()
        if self.live and now - self._last_draw > 0.03:
            self._last_draw = now
            frame = SPINNER[self.count % len(SPINNER)]
            self.out.write(
                f"\r  {ui.paint(frame, ui.ACCENT)} {self.count} checks passed"
            )
            self.out.flush()


def _clear_line(out: IO[str]) -> None:
    if out.isatty():
        out.write("\r\x1b[K")


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _card(
    title: str, rows: list[tuple[str, object]], color: int = ui.ERR
) -> str:
    out = ["  " + ui.paint("✘ " + title, color, "bold")]
    for label, value in rows:
        lines = str(value).splitlines() or [""]
        for i, line in enumerate(lines):
            tag = (
                ui.paint(f"{label:<9}", ui.MUTED)
                if i == 0 and label
                else " " * 9
            )
            out.append(f"  {ui.paint('│', color)} {tag} {line}")
    return "\n".join(out)


def _crash_location(
    error: BaseException, candidate: Path
) -> traceback.FrameSummary | None:
    """Last traceback frame inside the student's file, if any."""
    frames = [
        f
        for f in traceback.extract_tb(error.__traceback__)
        if Path(f.filename).resolve() == candidate.resolve()
    ]
    return frames[-1] if frames else None


def find_forbidden(
    source: str, forbidden: list[str]
) -> list[tuple[str, int]]:
    """[(name, line)] for each forbidden call in `source`.

    `forbidden` entries look like "sorted()" (a function, also caught through
    aliases such as `from builtins import sorted as s`) or ".sort()" (any
    method with that name). Raises SyntaxError if the source does not parse.
    """
    if not forbidden:
        return []
    tree = ast.parse(source)
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                aliases[alias.asname or alias.name] = (
                    f"{node.module}.{alias.name}"
                )

    def qualified(node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            base = qualified(node.value)
            return f"{base}.{node.attr}" if base else "." + node.attr
        return None

    imported_modules = {v.split(".")[0] for v in aliases.values()}

    def match(name: str) -> str | None:
        for original in forbidden:
            target = original[:-2] if original.endswith("()") else original
            if target.startswith("."):
                if name.endswith(target):
                    return original
            elif name in (target, f"builtins.{target}") or name.startswith(
                target + "."
            ):
                return original
            # module.Class.method (collections.deque.rotate): any .method once
            # module is imported
            parts = target.split(".")
            if (
                len(parts) >= 3
                and parts[0] in imported_modules
                and name.endswith("." + parts[-1])
            ):
                return original
        return None

    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        # `import heapq` / `from heapq import x` when the whole module is
        # forbidden
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            for mod in modules:
                for original in forbidden:
                    target = (
                        original[:-2] if original.endswith("()") else original
                    )
                    if (
                        "." not in target
                        and mod.split(".")[0] == target
                        and (original, node.lineno) not in found
                    ):
                        found.append((original, node.lineno))
        # calls, plus bare references like `key=sorted` or `f = list.sort`
        ref = node.func if isinstance(node, ast.Call) else node
        if isinstance(ref, (ast.Name, ast.Attribute)):
            name = qualified(ref)
            hit = match(name) if name else None
            if hit and (hit, ref.lineno) not in found:
                found.append((hit, ref.lineno))
    return sorted(found, key=lambda f: f[1])


def main(argv: list[str]) -> int:
    argv = list(argv)
    report = None
    if "--report" in argv:
        i = argv.index("--report")
        report = argv[i + 1]
        del argv[i:i + 2]
        # the code under test never sees where the verdict goes
        sys.argv[:] = argv
    code, total = _main(argv)
    if report:
        Path(report).write_text(
            json.dumps({"passed": code == 0, "total": total})
        )
    return code


def _main(argv: list[str]) -> tuple[int, int]:
    """Returns (exit code, number of checks)."""
    if len(argv) != 3:
        print(
            "usage: python3 -m examshell.harness QUESTION_DIR CANDIDATE"
            " [--report FILE]",
            file=sys.stderr,
        )
        return 2, 0
    sys.dont_write_bytecode = True
    qdir, candidate = Path(argv[1]), Path(argv[2])
    question = qdir.name
    out = sys.stdout
    start = time.monotonic()
    checker = Checker(out)
    captured = io.StringIO()  # anything the student's code prints

    tests = load_module(f"tests_{question}", qdir / "tests.py")
    script_mode = getattr(tests, "MODE", "module") == "script"
    module: ModuleType | None = None

    forbidden = getattr(tests, "FORBIDDEN", None)
    if forbidden and candidate.is_file():
        source = candidate.read_text(errors="replace")
        try:
            used = find_forbidden(source, forbidden)
        except SyntaxError:
            used = []  # reported properly below
        if used:
            rel = f"rendu/{candidate.parent.name}/{candidate.name}"
            lines = source.splitlines()
            rows: list[tuple[str, object]] = [
                ("forbidden", ", ".join(forbidden))
            ]
            for name, lineno in used:
                rows += [
                    ("used", f"{name}  at {rel} line {lineno}"),
                    (
                        "code",
                        (
                            lines[lineno - 1].strip()
                            if lineno <= len(lines)
                            else ""
                        ),
                    ),
                ]
            print(_card("forbidden function used", rows))
            return 1, 0

    try:
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        with contextlib.redirect_stdout(captured):
            if script_mode:
                tests.run(str(candidate), checker)
            else:
                module = load_module(question, candidate)
                tests.run(module, checker)
    except CheckFailed as fail:
        _clear_line(out)
        rows = [("check", fail.description)]
        if fail.errors:
            rows += [
                ("", line.strip())
                for err in fail.errors
                for line in str(err).strip().splitlines()
            ]
        elif fail.expected is None:
            rows.append(("got", repr(fail.result)))
        else:
            rows += [
                ("expected", repr(fail.expected)),
                ("got", repr(fail.result)),
            ]
        print(
            _card(
                f"check {fail.number} failed  ({fail.number - 1} passed"
                " before it)",
                rows,
            )
        )
        _show_prints(captured)
        return 1, checker.count
    except KeyboardInterrupt:
        raise
    except BaseException as error:  # student code can raise anything
        _clear_line(out)
        print(
            _describe_crash(error, candidate, question, module, checker.count)
        )
        _show_prints(captured)
        return 1, checker.count

    _clear_line(out)
    took = ui.paint(f"· {time.monotonic() - start:.2f}s", ui.MUTED)
    print(
        f"  {ui.paint('✔', ui.OK, 'bold')} {checker.count}/{checker.count}"
        f" checks passed  {took}"
    )
    return 0, checker.count


def _describe_crash(
    error: BaseException,
    candidate: Path,
    question: str,
    module: ModuleType | None,
    passed: int,
) -> str:
    rel = f"rendu/{candidate.parent.name}/{candidate.name}"
    if isinstance(error, FileNotFoundError) and not candidate.is_file():
        return _card("file not found", [("expected", rel)])
    if (
        isinstance(error, SyntaxError)
        and Path(error.filename or "").name == candidate.name
    ):
        return _card(
            "syntax error",
            [
                ("where", f"{rel} line {error.lineno}"),
                ("code", (error.text or "").rstrip()),
                ("error", error.msg),
            ],
        )
    if (
        isinstance(error, AttributeError)
        and module is not None
        and getattr(error, "obj", None) is module
    ):
        return _card(
            "function missing",
            [
                ("expected", f"def {error.name}(...) in {rel}"),
                (
                    "hint",
                    "check the name in the subject, it must match exactly",
                ),
            ],
        )
    if isinstance(error, SystemExit):
        return _card(
            "your code called exit()", [("after", f"{passed} passing checks")]
        )
    rows: list[tuple[str, object]] = [
        ("error", f"{type(error).__name__}: {error}"),
        ("after", f"{passed} passing checks"),
    ]
    during = getattr(sys.modules.get("examshell.pytests"), "current", None)
    if during:
        rows.insert(0, ("during", during))
    if isinstance(error, RecursionError):
        rows.append((
            "hint",
            (
                "too deep: recursion on a big input? try a loop with your own"
                " stack"
            ),
        ))
    frame = _crash_location(error, candidate)
    if frame:
        rows.insert(1, ("where", f"{rel} line {frame.lineno}"))
        rows.insert(2, ("code", (frame.line or "").strip()))
    return _card("your code crashed", rows)


def _show_prints(captured: io.StringIO, limit: int = 8) -> None:
    lines = captured.getvalue().splitlines()
    if not lines:
        return
    print(
        "  " + ui.paint(f"your code printed ({len(lines)} lines):", ui.MUTED)
    )
    for line in lines[-limit:]:
        print("    " + ui.paint(line[:200], ui.MUTED))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
