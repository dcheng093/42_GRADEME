"""Runs a question's tests with a timeout and reports the result."""

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from . import config, ui
from .questions import Question


@dataclass
class Result:
    passed: bool
    seconds: float
    timed_out: bool = False


def run_tests(question: Question, quiet: bool = False) -> Result:
    """Run the tests for `question` against what is in its rendu folder.

    The harness prints straight to the terminal; quiet=True captures and hides
    it.
    The verdict comes from the report file the harness writes, never from its
    output, so a program that prints "checks passed" gains nothing.
    """
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if quiet:
        env["NO_COLOR"] = "1"
    if question.is_python:
        harness, target, timeout = (
            "examshell.harness",
            question.candidate,
            config.TEST_TIMEOUT,
        )
    else:
        harness, target, timeout = (
            "examshell.native_harness",
            question.rendu_dir,
            config.NATIVE_TEST_TIMEOUT,
        )
    fd, report = tempfile.mkstemp(prefix="examshell-report-", suffix=".json")
    os.close(fd)
    try:
        cmd = [
            sys.executable,
            "-m",
            harness,
            str(question.path),
            str(target),
            "--report",
            report,
        ]
        result = _run(
            cmd, cwd=config.ROOT, env=env, quiet=quiet, timeout=timeout
        )
        try:
            verdict = json.loads(open(report).read() or "{}")
        except (OSError, ValueError):
            verdict = {}
        result.passed = result.passed and bool(verdict.get("passed"))
        return result
    finally:
        os.unlink(report)


def _run(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    quiet: bool = False,
    timeout: float | None = None,
) -> Result:
    timeout = timeout or config.TEST_TIMEOUT
    start = time.monotonic()
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        start_new_session=True,
        stdout=subprocess.PIPE if quiet else None,
        stderr=subprocess.STDOUT if quiet else None,
        text=True,
        errors="replace",
    )
    timed_out = False
    try:
        output, _ = proc.communicate(timeout=timeout)
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
            print(
                "  "
                + ui.paint(f"✘ timed out after {timeout}s", ui.ERR, "bold")
            )
            print(
                "  "
                + ui.paint("│", ui.ERR)
                + " probably an infinite loop (or waiting for input)"
            )
        return Result(False, seconds, True)

    return Result(proc.returncode == 0, seconds)


def _kill(proc: "subprocess.Popen[str]") -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        proc.kill()
