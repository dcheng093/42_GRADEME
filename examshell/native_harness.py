"""Test harness for C and C++ questions. Runs in a subprocess:

    python3 -m examshell.native_harness <question_dir> <rendu_dir> [--report FILE]

What gets built and run is described by <question_dir>/spec.json. Every key is
optional, and the defaults are the rank02 setup (reference <name>.c, optional
main.c, argv cases in cases.json, stdout compared):

    {
      "compiler": "cc" | "c++",            default: "c++" if a .cpp is expected
      "std": "c++98",                      added as -std=…
      "flags": ["-Wall", "-Wextra", "-Werror"],
      "ref": ["ref/bigint.cpp"],           reference sources (default <name>.c)
      "given": ["given/bag.hpp", ...],     files the subject hands out: copied to
                                           rendu/, and always taken from here when
                                           grading, so editing them changes nothing
      "builds": [                          one binary per build (default: one)
        {"name": "basic", "main": "mains/basic.cpp", "defines": ["BUFFER_SIZE=1"],
         "cases": [...]}                   cases of that build (default cases.json)
      ],
      "compare": ["stdout"],               stdout | stdout_unordered | exit | stderr
      "timeout": 3,                        seconds per run
      "leaks": false,                      valgrind: leaks + invalid accesses
      "fds": false,                        valgrind: fds still open at exit
      "leak_cases": 6                      how many runs go through valgrind
    }

A case is an argv list, or {"argv": [...], "stdin": "...", "files": {"name":
"content"}, "compare": [...], "leaks": true}. Every case runs the reference and
your binary and compares the results.

If <question_dir>/tester.py exists, its run(ctx, check) does the testing
instead (servers, pipes, timing): see Context below.

Exit 0 = every check passed, 1 = failed, 2 = the question itself is broken.
The verdict is also written to --report as JSON, never parsed from output.
"""

import fnmatch
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from . import ui
from .harness import _card, _clear_line, load_module

CASE_TIMEOUT = 3  # seconds per run
VALGRIND_SLOWDOWN = 15  # valgrind runs get this many times the timeout
STRICT = ["-Wall", "-Wextra", "-Werror"]
SHOW_LINES = 10  # of expected/got output
MAX_DOTS = 40
SOURCE_EXT = (".c", ".cpp", ".cc")

CRASHES = {
    "SIGSEGV": "segmentation fault (bad pointer? NULL? out of bounds?)",
    "SIGBUS": "bus error (bad pointer?)",
    "SIGABRT": "abort (double free? corrupted malloc? uncaught exception?)",
    "SIGFPE": "floating point exception (division by zero?)",
}


class Fail(Exception):
    """A finished verdict: print `card`, exit with `code`."""

    def __init__(self, card, code=1):
        super().__init__(card)
        self.card, self.code = card, code


@dataclass
class Run:
    stdout: bytes
    stderr: bytes
    code: object  # int, or None when it timed out

    @property
    def timed_out(self):
        return self.code is None

    @property
    def crashed(self):
        return isinstance(self.code, int) and self.code < 0


@dataclass
class Spec:
    qdir: Path
    data: dict
    expected: list = field(default_factory=list)

    @classmethod
    def load(cls, qdir, expected):
        path = qdir / "spec.json"
        data = json.loads(path.read_text()) if path.is_file() else {}
        return cls(qdir, data, expected)

    @property
    def name(self):
        return self.qdir.name

    @property
    def cpp(self):
        if "compiler" in self.data:
            return self.data["compiler"] == "c++"
        return any(f.endswith((".cpp", ".cc", ".hpp")) for f in self.expected + [s.name for s in self.ref_sources])

    @property
    def compiler(self):
        if self.cpp:
            return shutil.which("c++") or shutil.which("g++") or shutil.which("clang++") or "c++"
        return shutil.which("gcc") or shutil.which("cc") or shutil.which("clang") or "cc"

    @property
    def compiler_label(self):
        return "c++" if self.cpp else "gcc"

    @property
    def flags(self):
        flags = list(self.data.get("flags", STRICT))
        if self.data.get("std"):
            flags.append(f"-std={self.data['std']}")
        return flags

    @property
    def command_label(self):
        return " ".join([self.compiler_label, *self.flags])

    @property
    def ref_sources(self):
        refs = self.data.get("ref")
        if refs:
            return [self.qdir / r for r in refs]
        ref_dir = self.qdir / "ref"
        if ref_dir.is_dir():
            return sorted(f for f in ref_dir.iterdir() if f.name.endswith(SOURCE_EXT))
        return [self.qdir / f"{self.name}.c"]

    @property
    def given(self):
        """Files handed out with the subject, compiled from here (never from rendu/)."""
        if "given" in self.data:
            return [self.qdir / g for g in self.data["given"]]
        folder = self.qdir / "given"
        return sorted(folder.iterdir()) if folder.is_dir() else []

    def user_files_in(self, folder):
        """Expected file names, with patterns like *.c expanded against `folder`."""
        names = []
        for pattern in self.expected:
            if any(c in pattern for c in "*?["):
                names += sorted(f.name for f in folder.iterdir() if f.is_file() and fnmatch.fnmatch(f.name, pattern))
            else:
                names.append(pattern)
        return names

    def user_sources(self, folder):
        given = {g.name for g in self.given}
        return [f for f in self.user_files_in(folder) if f.endswith(SOURCE_EXT) and f not in given]

    @property
    def builds(self):
        builds = self.data.get("builds")
        if builds:
            return builds
        main = "main.cpp" if (self.qdir / "main.cpp").is_file() else "main.c"
        cases_file = self.qdir / "cases.json"
        cases = json.loads(cases_file.read_text()) if cases_file.is_file() else [[]]
        return [{"name": "", "main": main if (self.qdir / main).is_file() else None, "cases": cases}]

    @property
    def timeout(self):
        return self.data.get("timeout", CASE_TIMEOUT)

    @property
    def ldflags(self):
        return list(self.data.get("ldflags", []))


# ── compiling ───────────────────────────────────────────────────────────────
_DIAG = re.compile(r"^(.+?):(\d+):(?:\d+:)? (?:fatal )?error: (.+)$")
_LINK = re.compile(r"(undefined reference to|multiple definition of) [`'‘\"]([^'’`\"]+)['’`\"]")
_MAC_LINK = re.compile(r'"([^"]+)", referenced from')


def _binary_name(key):
    return f"{key[0]}_{hashlib.sha1(repr(key).encode()).hexdigest()[:10]}"


class Builder:
    """Compiles the reference and your files into a temp dir, once per build."""

    def __init__(self, spec, rendu, tmp):
        self.spec, self.rendu, self.tmp = spec, rendu, tmp
        self.user_dir = tmp / "user"
        self.user_dir.mkdir()
        # your files are copied (you can't break the run by editing mid-test);
        # the handed-out files are not, so the originals are what gets compiled
        given = {g.name for g in spec.given}
        if rendu.is_dir():
            for f in rendu.iterdir():
                if f.is_file() and f.name not in given:
                    shutil.copy(f, self.user_dir / f.name)
        self.given_dir = tmp / "given"
        self.given_dir.mkdir()
        for g in spec.given:
            shutil.copy(g, self.given_dir / g.name)
        self.cache = {}

    def _given_sources(self):
        return [str(self.given_dir / g.name) for g in self.spec.given if g.name.endswith(SOURCE_EXT)]

    def _main(self, main):
        return [str(self.spec.qdir / main)] if main else []

    def _defines(self, defines):
        return [f"-D{d}" for d in defines or ()]

    def ref(self, main=None, defines=(), out=None):
        key = ("ref", main, tuple(defines or ()))
        if key in self.cache:
            return self.cache[key]
        binary = self.tmp / (out or _binary_name(key))
        includes = {str(s.parent) for s in self.spec.ref_sources}
        cmd = [self.spec.compiler, "-w", *[f for f in self.spec.flags if f.startswith("-std")],
               *self._defines(defines), *[f"-I{i}" for i in sorted(includes)], f"-I{self.given_dir}",
               "-o", str(binary), *map(str, self.spec.ref_sources), *self._given_sources(), *self._main(main),
               *self.spec.ldflags]
        proc = subprocess.run(cmd, cwd=self.tmp, capture_output=True, text=True, errors="replace")
        if proc.returncode:
            log = (proc.stdout + proc.stderr).splitlines()
            raise Fail(_card("the reference solution doesn't compile (bug in this tool)",
                             [("output", "\n".join(log[:8]))]), code=2)
        self.cache[key] = binary
        return binary

    def user(self, main=None, defines=(), out=None, sources=None):
        key = ("user", main, tuple(defines or ()))
        if key in self.cache:
            return self.cache[key]
        sources = self.spec.user_sources(self.user_dir) if sources is None else sources
        missing = [s for s in sources if not (self.user_dir / s).is_file()]
        globs = [p for p in self.spec.expected if any(c in p for c in "*?[") and p.endswith(SOURCE_EXT)]
        if missing or not sources:
            rel = ", ".join(f"rendu/{self.rendu.name}/{m}" for m in (missing or globs or self.spec.expected))
            raise Fail(_card("file not found", [("expected", rel)]))
        binary = self.tmp / (out or _binary_name(key))
        cmd = [self.spec.compiler, *self.spec.flags, "-g", "-fdiagnostics-color=never",
               *self._defines(defines), f"-I{self.user_dir}", f"-I{self.given_dir}", "-o", str(binary),
               *[str(self.user_dir / s) for s in sources], *self._given_sources(), *self._main(main),
               *self.spec.ldflags]
        proc = subprocess.run(cmd, cwd=self.tmp, capture_output=True, text=True, errors="replace")
        if proc.returncode:
            raise Fail(self.compile_card(proc.stdout + proc.stderr, defines))
        self.cache[key] = binary
        return binary

    def preload(self, source):
        """Compile a test shim (e.g. a read() that returns short chunks) for LD_PRELOAD."""
        key = ("preload", source)
        if key in self.cache:
            return self.cache[key]
        lib = self.tmp / f"{_binary_name(key)}.so"
        cc = shutil.which("gcc") or shutil.which("cc") or "cc"
        proc = subprocess.run([cc, "-shared", "-fPIC", "-o", str(lib), str(self.spec.qdir / source), "-ldl"],
                              capture_output=True, text=True, errors="replace")
        if proc.returncode:
            raise Fail(_card("a test helper doesn't compile (bug in this tool)",
                             [("output", "\n".join((proc.stdout + proc.stderr).splitlines()[:8]))]), code=2)
        self.cache[key] = lib
        return lib

    def env_for(self, build):
        if not build.get("preload") or not sys.platform.startswith("linux"):
            return None
        return dict(os.environ, LD_PRELOAD=str(self.preload(build["preload"])))

    # ── messages ──
    def rel(self, path):
        path = Path(path)
        try:
            resolved = path.resolve()
        except OSError:
            return str(path)
        if resolved.parent == self.user_dir.resolve():
            return f"rendu/{self.rendu.name}/{path.name}"
        if resolved.parent == self.given_dir.resolve():
            return f"{path.name} (given with the subject)"
        if self.spec.qdir.resolve() in resolved.parents:
            return f"{path.name} (the test's own file)"
        return str(path)

    def compile_card(self, log, defines=()):
        title = f"doesn't compile  ({self.spec.command_label})"
        errors = [m for m in map(_DIAG.match, log.splitlines()) if m]
        if errors:
            mine = [m for m in errors if Path(m.group(1)).resolve().parent == self.user_dir.resolve()]
            first = (mine or errors)[0]
            path, line, msg = Path(first.group(1)), int(first.group(2)), first.group(3)
            try:
                code = path.read_text(errors="replace").splitlines()[line - 1].strip()
            except (OSError, IndexError):
                code = ""
            rows = [("where", f"{self.rel(path)} line {line}"), ("code", code), ("error", msg)]
            if "-Werror" in msg:
                rows.append(("hint", "warnings count as errors in the exam"))
            if "c++11" in msg or "C++11" in msg:
                rows.append(("hint", "the exam compiles with -std=c++98: no auto, nullptr, range-for…"))
            if not mine:
                rows.append(("hint", "the test includes your header: check its names and includes"))
            if defines:
                rows.append(("built with", " ".join(f"-D{d}" for d in defines)))
            if len(errors) > 1:
                rows.append(("", ui.paint(f"+{len(errors) - 1} more error{'s' * (len(errors) > 2)}", ui.MUTED)))
            return _card(title, rows)

        link = _LINK.search(log)
        name = link.group(2) if link else None
        kind = link.group(1) if link else None
        if not link:
            mac = _MAC_LINK.search(log)
            if mac:
                kind, name = "undefined reference to", mac.group(1).lstrip("_")
        if name:
            if kind == "undefined reference to":
                hint = ("this exercise is a program: it needs a main()" if name == "main"
                        else "declared but never defined: check the name and the signature in the subject")
                return _card("link error", [("missing", name), ("hint", hint)])
            hint = ("function exercises must not have a main(), the test brings its own" if name == "main"
                    else "it is defined twice (in a header without inline? in two files?)")
            return _card("link error", [("duplicate", name), ("hint", hint)])

        lines = [l for l in log.splitlines() if l.strip()]
        return _card(title, [(self.spec.compiler_label, "\n".join(lines[:8]))])


# ── running ─────────────────────────────────────────────────────────────────
def execute(binary, argv=(), stdin=b"", timeout=CASE_TIMEOUT, cwd=None, env=None, prefix=()):
    """Run a binary. stdin may be bytes or str. Never raises on timeout.

    stdin comes from a file, like `./prog < file` in the subjects (seekable)."""
    if isinstance(stdin, str):
        stdin = stdin.encode()
    with tempfile.TemporaryFile() as feed:
        feed.write(stdin or b"")
        feed.seek(0)
        try:
            proc = subprocess.run([*prefix, str(binary), *argv], stdin=feed, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=timeout, cwd=cwd, env=env,
                                  start_new_session=True)
        except subprocess.TimeoutExpired as err:
            return Run(err.stdout or b"", err.stderr or b"", None)
    return Run(proc.stdout, proc.stderr, proc.returncode)


_BARE = re.compile(r"[\w@%+=:,./-]+")


def quote(arg):
    if _BARE.fullmatch(arg):
        return arg
    return '"' + re.sub(r'([\\"$`])', r"\\\1", arg) + '"'


def command_line(name, case):
    if case.get("show"):
        return case["show"]
    cmd = " ".join([f"./{name}", *map(quote, case.get("argv", []))])
    stdin = case.get("stdin")
    if stdin is not None:
        shown = stdin if len(stdin) <= 60 else stdin[:57] + "…"
        shown = shown.replace("\n", "\\n")
        cmd = f"printf '{shown}' | {cmd}" if stdin else f"{cmd} < /dev/null"
    return cmd


def signal_name(code):
    try:
        return signal.Signals(-code).name
    except ValueError:
        return f"signal {-code}"


def _normalize(case):
    if isinstance(case, list):
        return {"argv": case}
    return case


def _prepare_cwd(tmp, case, n):
    files = case.get("files")
    if not files:
        return None
    cwd = tmp / f"case_{n}"
    cwd.mkdir(exist_ok=True)
    for name, content in files.items():
        (cwd / name).write_text(content)
    return cwd


# ── valgrind ────────────────────────────────────────────────────────────────
LEAK_KINDS = {"Leak_DefinitelyLost": "definitely lost", "Leak_IndirectlyLost": "indirectly lost"}
MEMORY_KINDS = {
    "InvalidRead": "invalid read (reading memory you don't own)",
    "InvalidWrite": "invalid write (writing past the end? into freed memory?)",
    "InvalidFree": "invalid free (double free? freeing something not malloc'd?)",
    "MismatchedFree": "mismatched free (new/delete[] mixed? malloc/delete?)",
    "UninitCondition": "a decision depends on an uninitialised value",
}
_FD_LINE = re.compile(r"Open (?:file descriptor|AF_\w+ socket) (\d+): ?(.*)")


def valgrind_available():
    return shutil.which("valgrind") is not None and sys.platform.startswith("linux")


def valgrind(binary, argv=(), stdin=b"", timeout=CASE_TIMEOUT, cwd=None, user_files=(), fds=False, env=None):
    """Run under valgrind. Returns a list of (title, rows) problems."""
    with tempfile.TemporaryDirectory(prefix="examshell-vg-") as vg:
        xml, log = Path(vg) / "out.xml", Path(vg) / "out.log"
        prefix = ["valgrind", "--leak-check=full", "--show-leak-kinds=definite,indirect",
                  "--errors-for-leak-kinds=definite,indirect", "--num-callers=30",
                  "--xml=yes", f"--xml-file={xml}", f"--log-file={log}"]
        if fds:
            prefix.append("--track-fds=yes")
        run = execute(binary, argv, stdin, timeout * VALGRIND_SLOWDOWN, cwd, env, prefix=prefix)
        if run.timed_out:
            return [("timed out under valgrind", [("hint", "very slow, or an infinite loop")])]
        problems = _parse_valgrind_xml(xml, user_files)
        if fds:
            problems += _parse_fds(log)
        return problems


def _frame_text(frames, user_files):
    """'bigint.cpp line 42 (bigint::bigint)' for the first frame in your code."""
    for fr in frames:
        if fr.get("file") in user_files:
            fn = fr.get("fn", "?")
            return f"{fr['file']} line {fr.get('line', '?')}  ({fn})"
    for fr in frames:
        if fr.get("file"):
            return f"{fr['file']} line {fr.get('line', '?')}  ({fr.get('fn', '?')})"
    return frames[0].get("fn", "?") if frames else "?"


def _parse_valgrind_xml(path, user_files):
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return []
    problems = []
    for err in root.iter("error"):
        kind = err.findtext("kind", "")
        frames = [{c.tag: c.text for c in fr} for fr in err.iter("frame")]
        where = _frame_text(frames, user_files)
        if kind in LEAK_KINDS:
            what = err.find("xwhat")
            text = what.findtext("text") if what is not None else err.findtext("what", "")
            leaked = what.findtext("leakedbytes") if what is not None else None
            blocks = what.findtext("leakedblocks") if what is not None else None
            amount = f"{leaked} bytes in {blocks} block{'s' * (blocks != '1')}" if leaked else text
            problems.append(("memory leak", [("lost", f"{amount} ({LEAK_KINDS[kind]})"),
                                             ("allocated", where)]))
        elif kind in MEMORY_KINDS:
            problems.append(("memory error", [("error", MEMORY_KINDS[kind]), ("where", where)]))
    return problems


def _parse_fds(log_path):
    try:
        lines = log_path.read_text(errors="replace").splitlines()
    except OSError:
        return []
    open_fds = []
    for i, line in enumerate(lines):
        body = line.split("== ", 1)[-1]
        m = _FD_LINE.search(body)
        if not m:
            continue
        nxt = lines[i + 1].split("== ", 1)[-1] if i + 1 < len(lines) else ""
        fd = int(m.group(1))
        if fd > 2 and "inherited from parent" not in nxt:
            open_fds.append(f"fd {fd}: {m.group(2) or '?'}")
    if not open_fds:
        return []
    return [("file descriptor leak", [("still open", "\n".join(open_fds)),
                                      ("hint", "every open()/pipe()/dup() needs its close()")])]


# ── drawing ─────────────────────────────────────────────────────────────────
def strip(states, total):
    """●●●●✘○○○ for small counts, a bar for big ones."""
    if total > MAX_DOTS:
        ok = sum(1 for s in states if s == "ok")
        return ui.bar(ok / total, 20, ui.OK if "fail" not in states else ui.ERR)
    marks = {"ok": ui.paint("●", ui.OK), "fail": ui.paint("✘", ui.ERR, "bold"),
             "run": ui.paint("◉", ui.HILITE)}
    return "".join(marks[s] for s in states) + ui.paint("○" * (total - len(states)), ui.MUTED)


def draw(out, states, total, note=""):
    if out.isatty():
        done = sum(1 for s in states if s == "ok")
        extra = f"  {ui.paint(note, ui.MUTED)}" if note else ""
        out.write(f"\r  {strip(states, total)}  {ui.paint(f'{done}/{total}', ui.MUTED)}{extra}\x1b[K")
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


def output_rows(expected, got, labels=("expected", "got")):
    exp_t, got_t = expected.decode(errors="replace"), got.decode(errors="replace")
    diff = next((i for i, (a, b) in enumerate(zip(exp_t, got_t)) if a != b), min(len(exp_t), len(got_t)))
    focus = exp_t.count("\n", 0, diff)
    rows = []
    for label, data, mark, other in ((labels[0], expected, None, None),
                                      (labels[1], got, diff, len(exp_t))):
        if not data:
            rows.append((label, ui.paint("(nothing)", ui.MUTED, "italic")))
        else:
            rows.append((label, _window(_visible(data, mark, other), focus)))
    if focus >= SHOW_LINES:
        rows.append(("first diff", f"line {focus + 1}"))
    return rows


# ── comparing ───────────────────────────────────────────────────────────────
def _sorted_lines(data):
    return b"".join(sorted(data.splitlines(keepends=True)))


def _numbers_match(expected, got, tolerance=0.0101):
    a, b = expected.split(), got.split()
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        try:
            if abs(float(x) - float(y)) > tolerance:
                return False
        except ValueError:
            if x != y:
                return False
    return True


def compare(ref, got, modes, timeout):
    """None if `got` matches `ref` under `modes`, else (title, rows)."""
    if got.timed_out:
        return (f"timed out after {timeout}s", [("hint", "infinite loop? (or waiting for input)")])
    if got.crashed and not ref.crashed:
        name = signal_name(got.code)
        return ("your program crashed", [("signal", f"{name}: {CRASHES.get(name, 'killed')}"),
                                         *output_rows(ref.stdout, got.stdout)])
    for mode in modes:
        if mode == "stdout" and got.stdout != ref.stdout:
            return ("wrong output", output_rows(ref.stdout, got.stdout))
        if mode == "stdout_unordered" and _sorted_lines(got.stdout) != _sorted_lines(ref.stdout):
            return ("wrong output (line order doesn't matter here)",
                    output_rows(_sorted_lines(ref.stdout), _sorted_lines(got.stdout))
                    + [("note", "lines shown sorted")])
        if mode == "stdout_numbers" and not _numbers_match(ref.stdout, got.stdout):
            return ("wrong output (numbers may differ by 0.01)", output_rows(ref.stdout, got.stdout))
        if mode == "exit" and got.code != ref.code:
            return ("wrong exit status", [("expected", str(ref.code)), ("got", str(got.code)),
                                          *([("output", got.stdout.decode(errors='replace')[:200])]
                                            if got.stdout else [])])
        if mode == "stderr" and got.stderr != ref.stderr:
            return ("wrong error output (stderr)", output_rows(ref.stderr, got.stderr))
    return None


# ── testing with cases ──────────────────────────────────────────────────────
class Context:
    """What a tester.py `run(ctx, check)` gets.

    ctx.ref(main=None, defines=())   build the reference, returns its binary
    ctx.user(main=None, defines=())  build your files (prints the compile card on error)
    ctx.run(binary, argv, stdin, timeout, cwd, env)  -> Run(stdout, stderr, code)
    ctx.valgrind(binary, argv, stdin, fds=False)      -> problems (empty = clean)
    ctx.fail(title, rows)            stop with a failure card
    ctx.tmp                          a scratch directory
    ctx.warn(text)                   a yellow note under the verdict
    """

    def __init__(self, spec, builder, tmp, out):
        self.spec, self.builder, self.tmp, self.out = spec, builder, tmp, out
        self.warnings = []

    def ref(self, main=None, defines=(), out=None):
        return self.builder.ref(main, defines, out)

    def user(self, main=None, defines=(), out=None, sources=None):
        return self.builder.user(main, defines, out, sources)

    def run(self, binary, argv=(), stdin=b"", timeout=None, cwd=None, env=None):
        return execute(binary, argv, stdin, timeout or self.spec.timeout, cwd, env)

    def valgrind(self, binary, argv=(), stdin=b"", fds=False, cwd=None):
        if not valgrind_available():
            self.warn_no_valgrind()
            return []
        return valgrind(binary, argv, stdin, self.spec.timeout, cwd, self.user_files, fds)

    def warn(self, text):
        if text not in self.warnings:
            self.warnings.append(text)

    def warn_no_valgrind(self):
        self.warn("leak check skipped: valgrind isn't installed (Linux only)")

    @property
    def user_files(self):
        return set(self.spec.user_files_in(self.builder.user_dir))

    def fail(self, title, rows=()):
        raise Fail(_card(title, list(rows)))

    output_rows = staticmethod(output_rows)
    command = staticmethod(command_line)


class Checker:
    """check(description, ok, rows=()) for tester.py: counts and draws progress."""

    def __init__(self, out, total=None):
        self.out, self.total, self.count = out, total, 0
        self.states = []

    def __call__(self, description, ok, rows=()):
        self.count += 1
        if not ok:
            if self.out.isatty():
                _clear_line(self.out)
            raise Fail(_card(f"check {self.count} failed  ({self.count - 1} passed before it)",
                             [("check", description), *rows]))
        self.states.append("ok")
        draw(self.out, self.states, max(self.total or 0, self.count))


def run_cases(spec, builder, tmp, out, ctx):
    plan = []  # (build, case)
    for build in spec.builds:
        for case in build.get("cases", []):
            plan.append((build, _normalize(case)))
    total = len(plan)
    if out.isatty():
        out.write(f"  {ui.paint('◌', ui.ACCENT)} {ui.paint('compiling…', ui.MUTED)}")
        out.flush()
    try:
        # build everything up front: one compile error is reported before any run
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs = []
            for build in spec.builds:
                args = (build.get("main"), build.get("defines", ()))
                jobs.append(pool.submit(builder.ref, *args))
            for job in jobs:
                job.result()
        for build in spec.builds:
            builder.user(build.get("main"), build.get("defines", ()))
    finally:
        _clear_line(out)

    leak_candidates = []
    states = []
    for n, (build, case) in enumerate(plan, 1):
        draw(out, states + ["run"], total)
        args = (build.get("main"), build.get("defines", ()))
        ref_bin, user_bin = builder.ref(*args), builder.user(*args)
        cwd = _prepare_cwd(tmp, case, n)
        timeout = case.get("timeout", spec.timeout)
        argv, stdin = case.get("argv", []), case.get("stdin", "")
        env = builder.env_for(build)
        ref = execute(ref_bin, argv, stdin, timeout * 4, cwd, env)
        if ref.timed_out:
            raise Fail(_card("the reference solution timed out (bug in this tool)",
                             [("run", command_line(spec.name, case))]), code=2)
        got = execute(user_bin, argv, stdin, timeout, cwd, env)
        modes = case.get("compare", build.get("compare", spec.data.get("compare", ["stdout"])))
        problem = compare(ref, got, modes, timeout)
        if problem:
            _clear_line(out)
            print(f"  {strip(states + ['fail'], total)}  {ui.paint(f'{n - 1}/{total}', ui.MUTED)}")
            title, rows = problem
            run_rows = [("run", command_line(spec.name, case))]
            if build.get("name"):
                run_rows.insert(0, ("test", build["name"]))
            if build.get("defines"):
                run_rows.append(("built with", " ".join(f"-D{d}" for d in build["defines"])))
            raise Fail(_card(f"{title}  (case {n} of {total}, {n - 1} passed before it)", run_rows + rows))
        states.append("ok")
        wants = case.get("leaks", build.get("leaks", spec.data.get("leaks", False)))
        if wants:
            leak_candidates.append((n, build, case, user_bin, cwd, env))

    _clear_line(out)
    _leak_pass(spec, leak_candidates, ctx, out)
    return total


def _leak_pass(spec, candidates, ctx, out):
    if not candidates:
        return
    if not valgrind_available():
        ctx.warn_no_valgrind()
        return
    explicit = [c for c in candidates if c[2].get("leaks") is True]
    limit = spec.data.get("leak_cases", 6)
    chosen = explicit or candidates
    if len(chosen) > limit:  # spread over the list: first, last and in between
        step = (len(chosen) - 1) / (limit - 1)
        chosen = [chosen[round(i * step)] for i in range(limit)]
    if out.isatty():
        out.write(f"  {ui.paint('◌', ui.ACCENT)} {ui.paint(f'leak check ({len(chosen)} runs under valgrind)…', ui.MUTED)}")
        out.flush()
    fds = spec.data.get("fds", False)

    def one(item):
        n, build, case, binary, cwd, env = item
        return item, valgrind(binary, case.get("argv", []), case.get("stdin", ""),
                              case.get("timeout", spec.timeout), cwd, ctx.user_files, fds, env)

    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        results = list(pool.map(one, chosen))
    _clear_line(out)
    for (n, build, case, _, _, _), problems in results:
        if problems:
            title, rows = problems[0]
            run_rows = [("run", command_line(spec.name, case))]
            if build.get("name"):
                run_rows.insert(0, ("test", build["name"]))
            more = len(problems) - 1
            extra = [("", ui.paint(f"+{more} more problem{'s' * (more > 1)}", ui.MUTED))] if more else []
            raise Fail(_card(f"{title}  (output was right, case {n})", run_rows + rows + extra))


# ── main ────────────────────────────────────────────────────────────────────
def expected_files(qdir):
    match = re.search(r"^Expected files\s*:\s*(.+)$",
                      (qdir / "sub.txt").read_text(errors="replace"), re.MULTILINE)
    if match:
        files = [f.strip() for f in re.split(r"[,\s]+", match.group(1)) if f.strip()]
        if files:
            return files
    return [qdir.name + ".c"]


def run(qdir, rendu, out):
    spec = Spec.load(qdir, expected_files(qdir))
    with tempfile.TemporaryDirectory(prefix="examshell-") as tmp:
        tmp = Path(tmp)
        builder = Builder(spec, rendu, tmp)
        ctx = Context(spec, builder, tmp, out)
        tester = qdir / "tester.py"
        if tester.is_file():
            module = load_module(f"tester_{qdir.name}", tester)
            checker = Checker(out, getattr(module, "TOTAL", None))
            module.run(ctx, checker)
            _clear_line(out)
            return checker.count, ctx.warnings
        return run_cases(spec, builder, tmp, out, ctx), ctx.warnings


def write_report(path, passed, total=0, warnings=()):
    if path:
        Path(path).write_text(json.dumps({"passed": passed, "total": total, "warnings": list(warnings)}))


def main(argv):
    args = argv[1:]
    report = None
    if "--report" in args:
        i = args.index("--report")
        report = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        print("usage: python3 -m examshell.native_harness QUESTION_DIR RENDU_DIR [--report FILE]",
              file=sys.stderr)
        return 2
    qdir, rendu = Path(args[0]).resolve(), Path(args[1]).resolve()
    if rendu.is_file():  # older callers pass the main file
        rendu = rendu.parent
    out = sys.stdout
    start = time.monotonic()
    try:
        total, warnings = run(qdir, rendu, out)
    except Fail as fail:
        _clear_line(out)
        print(fail.card)
        write_report(report, False)
        return fail.code
    _clear_line(out)
    took = ui.paint(f"· {time.monotonic() - start:.2f}s", ui.MUTED)
    print(f"  {ui.paint('✔', ui.OK, 'bold')} {total}/{total} checks passed  "
          f"{strip(['ok'] * total, total)}  {took}")
    for w in warnings:
        print("  " + ui.paint("⚠ " + w, ui.HILITE))
    write_report(report, True, total, warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
