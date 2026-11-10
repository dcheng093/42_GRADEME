"""Runs a question's tests with a timeout and reports the result."""

import os
import re
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass

from . import config, ui
from .harness import SPINNER


MAX_LINES = 30  # of tester output shown


@dataclass
class Result:
    passed: bool
    seconds: float
    timed_out: bool = False


def run_tests(question, candidate=None, quiet=False):
    """Run the tests for `question` against `candidate` (default: rendu file)."""
    candidate = candidate or question.candidate
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if quiet:
        env["NO_COLOR"] = "1"
    if question.rank.language == "python":
        cmd = [sys.executable, "-m", "examshell.harness", str(question.path), str(candidate)]
        return _run(cmd, cwd=config.ROOT, env=env, capture=quiet, quiet=quiet)
    # rank02 testers compile ../../../../rendu/<q>/<file> relative to their folder
    return _run(["bash", "tester.sh"], cwd=question.path, env=env, capture=True, quiet=quiet)


def _run(cmd, cwd, env, capture, quiet=False):
    start = time.monotonic()
    proc = subprocess.Popen(
        cmd, cwd=cwd, env=env, start_new_session=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        text=True, errors="replace",
    )
    stop = threading.Event()
    spinner = None
    if capture and not quiet and sys.stdout.isatty():
        spinner = threading.Thread(target=_spin, args=(stop,), daemon=True)
        spinner.start()
    timed_out = False
    try:
        output, _ = proc.communicate(timeout=config.TEST_TIMEOUT)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill(proc)
        output, _ = proc.communicate()
    except KeyboardInterrupt:
        _kill(proc)
        proc.communicate()
        raise
    finally:
        stop.set()
        if spinner:
            spinner.join()
    seconds = time.monotonic() - start

    if capture and output and not quiet:
        lines = output.rstrip("\n").splitlines()
        if len(lines) > MAX_LINES:
            more = len(lines) - MAX_LINES
            lines = lines[:MAX_LINES] + [ui.paint(f"… {more} more lines", "gray")]
        print(ui.indent_block("\n".join(lines), "  │ "))
    if timed_out:
        if not quiet:
            print()
            print("  " + ui.paint(f"✘ timed out after {config.TEST_TIMEOUT}s", "red", "bold"))
            print("  " + ui.paint("│", "red") + " probably an infinite loop (or waiting for input)")
        return Result(False, seconds, True)

    passed = proc.returncode == 0
    if capture and passed and output and not re.search(r"pass|success", output, re.IGNORECASE):
        passed = False  # a tester that exits 0 without saying so is suspicious
    return Result(passed, seconds)


def _spin(stop):
    i = 0
    while not stop.wait(0.08):
        sys.stdout.write(f"\r  {ui.paint(SPINNER[i % len(SPINNER)], 207)} compiling & testing…")
        sys.stdout.flush()
        i += 1
    sys.stdout.write("\r\x1b[K" if ui.COLOR else "\r")
    sys.stdout.flush()


def _kill(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        proc.kill()
