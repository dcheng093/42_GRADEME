"""The rendu/ folder you write your answers in, and trace/ where old ones go."""

import shutil
import subprocess
import sys
from datetime import datetime

from . import config


def prepare(question):
    """Create rendu/<question>/ with empty expected files. Returns the main file."""
    question.rendu_dir.mkdir(parents=True, exist_ok=True)
    for name in question.expected_files:
        (question.rendu_dir / name).touch(exist_ok=True)
    # headers the subject hands you (ft_list.h, list.h…) unless you must write them
    for header in question.path.glob("*.h"):
        target = question.rendu_dir / header.name
        if header.name not in question.expected_files and not target.exists():
            shutil.copy(header, target)
    return question.candidate


def _has_work(path):
    return any(f.is_file() and f.stat().st_size > 0 for f in path.rglob("*"))


def archive():
    """Move rendu/ to trace/<timestamp>/ if you wrote anything, else just remove it.

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


def clean_caches():
    for folder in (config.RENDU, config.SUBJECTS, config.ROOT / "examshell"):
        if folder.is_dir():
            for cache in folder.rglob("__pycache__"):
                shutil.rmtree(cache, ignore_errors=True)


def open_folder(path):
    """Open a folder in the OS file manager. Returns False if nothing worked."""
    path.mkdir(parents=True, exist_ok=True)
    candidates = []
    if sys.platform == "darwin":
        candidates.append(["open", str(path)])
    if shutil.which("wslpath") and shutil.which("explorer.exe"):
        win = subprocess.run(["wslpath", "-w", str(path)], capture_output=True, text=True).stdout.strip()
        candidates.append(["explorer.exe", win])
    candidates += [["xdg-open", str(path)], ["open", str(path)]]
    for cmd in candidates:
        if shutil.which(cmd[0]):
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except OSError:
                continue
    return False
