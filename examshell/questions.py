"""Question lookup: turns config.RANKS into concrete folders and files."""

import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from . import config


@dataclass(frozen=True)
class Question:
    rank: config.Rank
    level: int  # 0-based index into rank.levels
    name: str

    @property
    def id(self):
        return f"{self.rank.key}/{self.name}"

    @property
    def path(self) -> Path:
        folder = self.rank.levels[self.level].folder
        return config.SUBJECTS / self.rank.key / folder / self.name

    @property
    def subject(self) -> str:
        return (self.path / "sub.txt").read_text(errors="replace").rstrip()

    @cached_property
    def expected_files(self) -> list:
        match = re.search(r"^Expected files\s*:\s*(.+)$", self.subject, re.MULTILINE)
        if match:
            files = [f.strip() for f in match.group(1).split(",") if f.strip()]
            if files:
                return files
        ext = ".py" if self.rank.language == "python" else ".c"
        return [self.name + ext]

    @cached_property
    def starter(self) -> str:
        """Initial answer file content: the subject's function signature (Python only)."""
        if self.rank.language != "python":
            return ""
        match = re.search(r"^def \w+\(.*\).*:\s*$", self.subject, re.MULTILINE)
        return f"{match.group(0).strip()}\n    pass\n" if match else ""

    @property
    def rendu_dir(self) -> Path:
        return config.RENDU / self.name

    @property
    def candidate(self) -> Path:
        return self.rendu_dir / self.expected_files[0]

    @property
    def solution(self):
        for name in ("solution.py", self.name + ".c"):
            if (self.path / name).is_file():
                return self.path / name
        return None


def all_questions(rank):
    """Every question of a rank, level by level, in config order."""
    return [Question(rank, i, name) for i, lvl in enumerate(rank.levels) for name in lvl.pool]


def missing_questions():
    """Questions listed in config.py that have no folder on disk."""
    return [q for r in config.RANKS.values() for q in all_questions(r) if not q.path.is_dir()]
