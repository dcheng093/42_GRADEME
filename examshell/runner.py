"""Runs a question's tests with a timeout and reports the result."""

import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass

from . import config, ui


@dataclass
class Result:
    passed: bool
    seconds: float
    timed_out: bool = False


HARNESS = {"python": "examshell.harness", "c": "examshell.c_harness"}


def run_tests(question, candidate=None, quiet=False):
    """Run the tests for `question` against `candidate` (default: rendu file).

    The harness prints straight to the terminal; quiet=True captures and hides it.
    """
    candidate = candidate or question.candidate
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if quiet:
        env["NO_COLOR"] = "1"
    cmd = [sys.executable, "-m", HARNESS[question.rank.language], str(question.path), str(candidate)]
    return _run(cmd, cwd=config.ROOT, env=env, quiet=quiet)


def _run(cmd, cwd, env, quiet=False):
    start = time.monotonic()
    proc = subprocess.Popen(
        cmd, cwd=cwd, env=env, start_new_session=True,
        stdout=subprocess.PIPE if quiet else None,
        stderr=subprocess.STDOUT if quiet else None,
        text=True, errors="replace",
    )
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
    seconds = time.monotonic() - start

    if timed_out:
        if not quiet:
            print()
            print("  " + ui.paint(f"✘ timed out after {config.TEST_TIMEOUT}s", ui.ERR, "bold"))
            print("  " + ui.paint("│", ui.ERR) + " probably an infinite loop (or waiting for input)")
        return Result(False, seconds, True)

    passed = proc.returncode == 0
    if quiet and passed and output and not re.search(r"checks passed", output):
        passed = False  # a harness that exits 0 without saying so is suspicious
    return Result(passed, seconds)


def _kill(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        proc.kill()
