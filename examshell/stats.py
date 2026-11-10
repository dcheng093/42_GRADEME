"""Local practice history, saved to .examshell/stats.json (gitignored)."""

import json
import os
import time
from datetime import datetime

from . import config

PATH = config.STATE_DIR / "stats.json"


class Stats:
    def __init__(self, data=None):
        self.data = data or {"questions": {}, "exams": []}
        self.data.setdefault("questions", {})
        self.data.setdefault("exams", [])
        self._migrate_legacy()

    def _migrate_legacy(self):
        """The old rank03 pool moved to rank03_legacy: carry its history over."""
        legacy = config.RANKS.get("rank03_legacy")
        if not legacy or self.data.get("legacy_migrated"):
            return
        old_names = {n for lvl in legacy.levels for n in lvl.pool}
        qs = self.data["questions"]
        # names in both pools (py_echo_validator…) changed signature: history belongs to the old one
        for name in old_names:
            if f"rank03/{name}" in qs:
                qs.setdefault(f"rank03_legacy/{name}", qs.pop(f"rank03/{name}"))
        self.data["legacy_migrated"] = True

    @classmethod
    def load(cls):
        try:
            return cls(json.loads(PATH.read_text()))
        except FileNotFoundError:
            return cls()
        except (ValueError, OSError):
            # corrupt file: keep a copy, start fresh
            try:
                PATH.replace(PATH.with_suffix(f".broken-{int(time.time())}.json"))
            except OSError:
                pass
            return cls()

    def save(self):
        config.STATE_DIR.mkdir(exist_ok=True)
        tmp = PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=1))
        os.replace(tmp, PATH)

    def question(self, qid):
        return self.data["questions"].get(qid, {})

    def record_test(self, qid, passed, seconds_on_question):
        q = self.data["questions"].setdefault(
            qid, {"attempts": 0, "passes": 0, "fails": 0, "best_time": None})
        q["attempts"] += 1
        q["passes" if passed else "fails"] += 1
        q["last"] = "pass" if passed else "fail"
        q["last_at"] = datetime.now().isoformat(timespec="seconds")
        if passed and (q["best_time"] is None or seconds_on_question < q["best_time"]):
            q["best_time"] = round(seconds_on_question, 1)
        self.save()

    def record_exam(self, rank_key, grade, seconds, levels_passed, levels_total):
        self.data["exams"].append({
            "rank": rank_key,
            "date": datetime.now().isoformat(timespec="minutes"),
            "grade": grade,
            "duration": round(seconds),
            "levels": f"{levels_passed}/{levels_total}",
        })
        self.save()

    def failed_questions(self, rank_key):
        """Questions whose most recent test failed, or that fail more than they pass."""
        prefix = rank_key + "/"
        return [qid[len(prefix):] for qid, q in self.data["questions"].items()
                if qid.startswith(prefix) and (q.get("last") == "fail" or q["fails"] > q["passes"])]

    def reset(self):
        self.data = {"questions": {}, "exams": []}
        self.save()
