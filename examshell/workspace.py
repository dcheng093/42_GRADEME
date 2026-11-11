"""The rendu/ folder you write your answers in, and trace/ where old ones
go."""

import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import config
from .questions import Question


def prepare(question: Question) -> Path:
    """Create rendu/<question>/ with the expected files. Returns the main file.

    Files the subject hands out (spec.json "given", headers like ft_list.h) are
    copied in too, unless you already have them.
    """
    question.rendu_dir.mkdir(parents=True, exist_ok=True)
    # handouts first: some are the file you complete (a skeleton, a broken gnl)
    for src in question.handout_files:
        target = question.rendu_dir / src.name
        if not target.exists():
            shutil.copy(src, target)
    for src in list(question.given_files) + sorted(question.path.glob("*.h")):
        target = question.rendu_dir / src.name
        if src.name not in question.expected_files and not target.exists():
            shutil.copy(src, target)
    for name in question.expected_files:
        if not any(c in name for c in "*?["):
            target = question.rendu_dir / name
            header = question.path / name
            # a header you turn in (ft_list_foreach's ft_list.h) starts as
            # the subject's copy
            if (
                name.endswith(".h")
                and header.is_file()
                and (not target.exists() or target.stat().st_size == 0)
            ):
                shutil.copy(header, target)
            target.touch(exist_ok=True)
    if not question.candidate.exists():  # `*.c`: start with <name>.c
        question.candidate.touch()
    # function subjects start with the signature already written
    if question.starter and question.candidate.stat().st_size == 0:
        question.candidate.write_text(question.starter)
    return question.candidate


_STUB_LINE = re.compile(
    r"(class \w+.*:|\s*def \w+\(.*\).*:|\s+pass|\s+raise NotImplementedError"
    r"|\s*\"\"\".*\"\"\"|\s*|from typing import [\w, ]+)"
)


# a C prototype line, `;` optional: the C starter
_C_SIGNATURE = re.compile(
    r"\s*[A-Za-z_]\w*(?:[ \t]+\w+)*[ \t*]+\w+[ \t]*\(.*\)\s*;?\s*"
)


def is_stub(text: str) -> bool:
    """True if `text` is an untouched starter written by prepare(): only
    class/def headers (and `pass` / `raise NotImplementedError` lines, as
    older starters had), or only C prototypes."""
    lines = text.splitlines()
    code = [line for line in lines if line.strip()]
    if code and all(_C_SIGNATURE.fullmatch(line) for line in code):
        return True
    return any(
        line.lstrip().startswith(("def ", "class ")) for line in lines
    ) and all(_STUB_LINE.fullmatch(line) for line in lines)


def _handed_out() -> set[tuple[str, bytes]]:
    """(name, content) of every file a subject hands out: copies of those
    aren't your work."""
    found = set()
    for folder in ("given", "handout"):
        for f in config.SUBJECTS.glob(f"*/*/{folder}/*"):
            found.add((f.name, f.read_bytes()))
        for f in config.SUBJECTS.glob(f"*/*/*/{folder}/*"):
            found.add((f.name, f.read_bytes()))
    for f in config.SUBJECTS.glob("*/*/*/*.h"):  # rank02 headers (ft_list.h…)
        found.add((f.name, f.read_bytes()))
    return found


def _has_work(path: Path) -> bool:
    handed_out: set[tuple[str, bytes]] | None = None
    for f in path.rglob("*"):
        if (
            not f.is_file()
            or f.stat().st_size == 0
            or is_stub(f.read_text(errors="replace"))
        ):
            continue
        if handed_out is None:
            handed_out = _handed_out()
        if (f.name, f.read_bytes()) not in handed_out:
            return True
    return False


def archive() -> Path | None:
    """Move rendu/ to trace/<timestamp>/ if you wrote anything, else just
    remove it.

    Returns the trace folder, or None.
    """
    clean_caches()
    if not config.RENDU.is_dir():
        return None
    if not _has_work(config.RENDU):
        shutil.rmtree(config.RENDU, ignore_errors=True)
        return None
    target = config.TRACE / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    config.TRACE.mkdir(exist_ok=True)
    shutil.move(str(config.RENDU), str(target))
    return target


def clean_caches() -> None:
    for folder in (config.RENDU, config.SUBJECTS, config.ROOT / "examshell"):
        if folder.is_dir():
            for cache in folder.rglob("__pycache__"):
                shutil.rmtree(cache, ignore_errors=True)


def open_folder(path: Path) -> bool:
    """Open a folder in the OS file manager. Returns False if nothing
    worked."""
    path.mkdir(parents=True, exist_ok=True)
    candidates: list[list[str]] = []
    if sys.platform == "darwin":
        candidates.append(["open", str(path)])
    if shutil.which("wslpath") and shutil.which("explorer.exe"):
        win = subprocess.run(
            ["wslpath", "-w", str(path)], capture_output=True, text=True
        ).stdout.strip()
        candidates.append(["explorer.exe", win])
    candidates += [["xdg-open", str(path)], ["open", str(path)]]
    for cmd in candidates:
        if shutil.which(cmd[0]):
            try:
                subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                return True
            except OSError:
                continue
    return False
