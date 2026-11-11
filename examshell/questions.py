"""Question lookup: turns config.RANKS into concrete folders and files."""

import fnmatch
import functools
import json
import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

from . import config


@dataclass(frozen=True)
class Question:
    rank: config.Rank
    level: int  # 0-based index into rank.levels
    name: str

    @property
    def id(self) -> str:
        return f"{self.rank.key}/{self.name}"

    @property
    def path(self) -> Path:
        folder = self.rank.levels[self.level].folder
        own = config.SUBJECTS / self.rank.key / folder / self.name
        if own.is_dir() or not self.rank.borrow:
            return own
        return _borrowed(self.rank.borrow, self.name) or own

    @property
    def subject(self) -> str:
        return self.subject_in("en")

    def subject_in(self, lang: str = "en") -> str:
        """Subject text in `lang` (sub.<lang>.txt), falling back to English."""
        path = self.path / f"sub.{lang}.txt"
        if lang == "en" or not path.is_file():
            path = self.path / "sub.txt"
        return path.read_text(encoding="utf-8", errors="replace").rstrip()

    @property
    def languages(self) -> list[str]:
        return ["en"] + [
            lang
            for lang in config.LANGUAGES[1:]
            if (self.path / f"sub.{lang}.txt").is_file()
        ]

    @cached_property
    def expected_files(self) -> list[str]:
        match = re.search(
            r"^Expected files\s*:\s*(.+)$", self.subject, re.MULTILINE
        )
        if match:
            files = [
                f.strip()
                for f in re.split(r"[,\s]+", match.group(1))
                if f.strip()
            ]
            if files:
                return files
        if (self.path / "solution.py").is_file():
            return [self.name + ".py"]
        return [self.name + ".c"]

    @property
    def is_python(self) -> bool:
        return self.expected_files[0].endswith(".py")

    @property
    def language_label(self) -> str:
        if self.is_python:
            return "Python"
        return (
            "C++"
            if any(f.endswith((".cpp", ".hpp")) for f in self.expected_files)
            else "C"
        )

    @property
    def extra(self) -> bool:
        """A practice-only question: never drawn in a real exam."""
        return self.name in self.rank.levels[self.level].extras

    @cached_property
    def starter(self) -> str:
        """Initial answer file content (Python only): starter.py, or the
        subject's signature."""
        if not self.is_python:
            return ""
        custom = self.path / "starter.py"
        if custom.is_file():
            return custom.read_text(encoding="utf-8")
        match = re.search(r"^def \w+\(.*\).*:\s*$", self.subject, re.MULTILINE)
        return f"{match.group(0).strip()}\n    pass\n" if match else ""

    @property
    def rendu_dir(self) -> Path:
        return config.RENDU / self.name

    @property
    def candidate(self) -> Path:
        """Your main file: the first expected file (for `*.c`, <name>.c)."""
        first = self.expected_files[0]
        if _is_glob(first):
            return self.rendu_dir / (self.name + Path(first).suffix)
        return self.rendu_dir / first

    def files_in(self, folder: Path) -> list[str]:
        """Expected file names found in `folder` (patterns like *.c
        expanded)."""
        names: list[str] = []
        for pattern in self.expected_files:
            if _is_glob(pattern):
                if folder.is_dir():
                    names += sorted(
                        f.name
                        for f in folder.iterdir()
                        if f.is_file() and fnmatch.fnmatch(f.name, pattern)
                    )
            else:
                names.append(pattern)
        return names

    @property
    def spec(self) -> dict[str, Any]:
        path = self.path / "spec.json"
        if not path.is_file():
            return {}
        spec: dict[str, Any] = json.loads(path.read_text())
        return spec

    @property
    def given_files(self) -> list[Path]:
        """Files the subject hands out that tests compile from the subject
        folder (your copies in rendu/ are ignored)."""
        if "given" in self.spec:
            return [self.path / g for g in self.spec["given"]]
        folder = self.path / "given"
        return sorted(folder.iterdir()) if folder.is_dir() else []

    @property
    def handout_files(self) -> list[Path]:
        """Extra files handed out for you to read or compile yourself
        (a subject main)."""
        folder = self.path / "handout"
        return sorted(folder.iterdir()) if folder.is_dir() else []

    @property
    def reference_dir(self) -> Path:
        """Folder holding the reference answer under its expected file
        names."""
        ref = self.path / "ref"
        return ref if ref.is_dir() else self.path

    @property
    def solution_files(self) -> list[Path]:
        """The reference answer, one Path per file (empty if there is none)."""
        if self.is_python:
            sol = self.path / "solution.py"
            return [sol] if sol.is_file() else []
        given = {g.name for g in self.given_files}
        return [
            self.reference_dir / f
            for f in self.files_in(self.reference_dir)
            if f not in given and (self.reference_dir / f).is_file()
        ]

    @property
    def solution(self) -> Path | None:
        files = self.solution_files
        return files[0] if files else None


@functools.lru_cache(maxsize=None)
def _borrowed(folders: tuple[str, ...], name: str) -> Path | None:
    """The first <subjects>/<folder>/<name> that exists (a question shared
    between ranks)."""
    for folder in folders:
        path = config.SUBJECTS / folder / name
        if path.is_dir():
            return path
    return None


def _is_glob(name: str) -> bool:
    return any(c in name for c in "*?[")


def all_questions(rank: config.Rank) -> list[Question]:
    """Every question of a rank, level by level, in config order."""
    return [
        Question(rank, i, name)
        for i, lvl in enumerate(rank.levels)
        for name in lvl.practice_pool
    ]


def missing_questions() -> list[Question]:
    """Questions listed in config.py that have no folder on disk."""
    return [
        q
        for r in config.RANKS.values()
        for q in all_questions(r)
        if not q.path.is_dir()
    ]
