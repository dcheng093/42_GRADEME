"""Entry point: python3 -m examshell  (or just `make`)."""

import argparse
import os
import random
import shutil
import subprocess
import sys
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from . import config, runner, session, ui, workspace
from .questions import Question, all_questions, missing_questions
from .stats import Stats

# ── screens ─────────────────────────────────────────────────────────────────
NOTICE: list[str] = []  # one-shot messages shown under the banner


def splash() -> None:
    ui.clear()
    print()
    ui.reveal(config.APP_NAME)
    print()
    print("  " + ui.paint(config.TAGLINE, ui.MUTED))
    print()
    while NOTICE:
        print("  " + NOTICE.pop(0))
    print()


def _archive() -> None:
    trace = workspace.archive()
    if trace:
        NOTICE.append(
            ui.paint("✔ ", ui.OK)
            + ui.paint("your code was saved to ", ui.MUTED)
            + ui.paint(f"{trace.relative_to(config.ROOT)}/", ui.HILITE)
        )


def choose_rank(purpose: str, exam: bool = False) -> config.Rank | None:
    ranks = [r for r in config.RANKS.values() if r.exam or not exam]
    options: list[tuple[int | None, str, str]] = []
    order: list[config.Rank] = []
    for curriculum, header, _ in config.CURRICULA:
        group = [r for r in ranks if r.curriculum == curriculum]
        if not group:
            continue
        options.append((None, header, ""))
        for r in group:
            order.append(r)
            n = len(r.exam_view().levels)
            hint = (
                f"{r.language_label} · {n} level{'s' * (n > 1)} · "
                f"{len(all_questions(r))} questions"
            )
            options.append((len(order), r.title, hint))
    choice = ui.menu(purpose, options, footer="enter = back")
    return None if choice is None else order[choice - 1]


def _mark(stats: Stats, q: Question) -> str:
    s = stats.question(q.id)
    if s.get("passes"):
        return ui.paint("✔", ui.OK)
    if s.get("fails"):
        return ui.paint("✘", ui.ERR)
    return ui.paint("·", ui.MUTED)


PICK_COMMANDS = (
    ("L2", "every question of level 2, shuffled — then on to level 3"),
    (
        "7",
        (
            "start at question 7 (or type its name), then the rest of its"
            " level shuffled"
        ),
    ),
    ("r", "start at a random question, then the rest of its level shuffled"),
    ("enter", "back"),
)


def pick_question(
    rank: config.Rank, stats: Stats
) -> list[Question] | None:
    """Level map. Returns the playlist of questions to practise, or None."""
    questions = all_questions(rank)
    col = max(len(q.name) + (7 if q.extra else 0) for q in questions) + 10
    per_row = max(1, min(3, (ui.card_width() - 4) // col))
    print()
    print(
        ui.status_strip(
            ui.chip(config.APP_NAME)
            + "  "
            + ui.paint(rank.label, "bold")
            + "  "
            + ui.chip("PRACTICE"),
            ui.paint("pick where to start", ui.MUTED),
        )
    )
    print()
    for li, level in enumerate(rank.levels):
        entries = [(i, q) for i, q in enumerate(questions) if q.level == li]
        solved = sum(
            1 for _, q in entries if stats.question(q.id).get("passes")
        )
        lines = []
        for row in range(0, len(entries), per_row):
            cells = []
            for i, q in entries[row:row + per_row]:
                rare = ui.paint(" (rare)", ui.MUTED) if q.extra else ""
                cell = (
                    f"{ui.paint(f'{i + 1:>3}', ui.MUTED)}  {_mark(stats, q)}"
                    f" {q.name}{rare}"
                )
                cells.append(cell + " " * (col - ui.visible_len(cell)))
            lines.append("".join(cells).rstrip())
        print(
            ui.card(
                lines,
                title=f"L{li + 1}  {level.theme}",
                right=ui.level_bar(solved, len(entries), 10),
            )
        )
    print()
    print(ui.command_card(PICK_COMMANDS, title="how to start"))
    print()
    while True:
        choice = ui.ask().lower()
        if choice in ("", "b", "back", "menu"):
            return None
        if choice in ("q", "quit", "exit"):
            raise SystemExit(0)
        if choice == "r":
            return session.from_question(
                rank, random.randrange(len(questions))
            )
        if (
            choice.startswith("l")
            and choice[1:].isdigit()
            and 1 <= int(choice[1:]) <= len(rank.levels)
        ):
            return session.level_run(rank, int(choice[1:]) - 1)
        if choice.isdigit() and 1 <= int(choice) <= len(questions):
            return session.from_question(rank, int(choice) - 1)
        names = [q.name.lower() for q in questions]
        if choice in names:
            return session.from_question(rank, names.index(choice))
        print(
            "  "
            + ui.paint(
                f"'{choice}' is not a level, question number or name", ui.ERR
            )
        )


def stats_screen(stats: Stats) -> None:
    while True:
        ui.clear()
        print()
        ui.reveal("STATS")
        print()
        untouched = []
        for rank in config.RANKS.values():
            if not any(
                stats.question(q.id).get("attempts")
                for q in all_questions(rank)
            ):
                untouched.append(rank.label)
                continue
            lines = []
            for li, level in enumerate(rank.levels):
                qs = [q for q in all_questions(rank) if q.level == li]
                tried = [q for q in qs if stats.question(q.id).get("attempts")]
                solved = sum(
                    1 for q in qs if stats.question(q.id).get("passes")
                )
                if li:
                    lines.append("")
                lines.append(
                    ui.paint(f"L{li + 1} ", ui.HILITE, "bold")
                    + ui.paint(f"{level.theme:<20}", "bold")
                    + ui.level_bar(solved, len(qs), 12)
                    + ui.paint(f"  · {len(tried)} tried", ui.MUTED)
                )
                for q in tried:
                    s = stats.question(q.id)
                    rate = s["passes"] / s["attempts"]
                    best = (
                        ui.duration(s["best_time"])
                        if s.get("best_time") is not None
                        else "  -  "
                    )
                    weak = (
                        ui.paint("  weak", ui.ERR, "bold")
                        if s["fails"] > s["passes"]
                        else ""
                    )
                    rate_bar = ui.bar(
                        rate, 12, ui.OK if rate >= 0.5 else ui.HILITE
                    )
                    lines.append(
                        f"   {q.name:<24}"
                        f" {rate_bar}"
                        f" {s['passes']:>2}/{s['attempts']:<3}"
                        f" {ui.paint('best', ui.MUTED)} {best}{weak}"
                    )
            print(ui.card(lines, title=rank.label))
            print()
        if untouched:
            print(
                "  "
                + ui.paint("not tried yet: " + ", ".join(untouched), ui.MUTED)
            )
            print()
        exams = stats.data["exams"][-8:]
        if exams:
            lines = []
            for e in reversed(exams):
                g = e["grade"]
                g_color = (
                    ui.OK if g == 100 else ui.HILITE if g >= 50 else ui.ERR
                )
                title = (
                    config.RANKS[e["rank"]].label
                    if e["rank"] in config.RANKS
                    else e["rank"]
                )
                lines.append(
                    f"{ui.paint(e['date'].replace('T', ' '), ui.MUTED)} "
                    f" {title:<16}"
                    f" {ui.bar(g / 100, 10, g_color)}"
                    f" {g:>3}/100 "
                    f" {ui.paint(ui.duration(e['duration']), ui.MUTED)}"
                )
            print(ui.card(lines, title="recent exams"))
            print()
        print(
            ui.command_card(
                [("reset", "wipe all stats"), ("enter", "back")],
                title="options",
            )
        )
        print()
        choice = ui.ask().lower()
        if choice == "reset":
            if ui.confirm("really delete all your stats?"):
                stats.reset()
        else:
            return


def help_screen() -> None:
    ui.clear()
    print()
    ui.reveal("HELP")
    print()
    print(
        ui.card(
            [
                ui.paint("practice", ui.ACCENT, "bold"),
                (
                    "  pick a level and do every question in it (shuffled), or"
                    " start"
                ),
                (
                    "  anywhere and go in order. test as often as you like,"
                    " peek at"
                ),
                (
                    "  solutions, retry the ones you failed. a summary screen"
                    " tells you"
                ),
                "  when you finish a level.",
                "",
                ui.paint("real exam", ui.ACCENT, "bold"),
                "  one random question per level, a countdown clock,",
                "  a cooldown after each failed test, grade out of 100.",
                "",
                ui.paint("grading", ui.ACCENT, "bold"),
                (
                    "  Python: your function against hidden cases, forbidden"
                    " imports,"
                ),
                "  and a speed check where the subject asks for a complexity.",
                (
                    "  C / C++: compiled with the exam flags, run against a"
                    " reference"
                ),
                (
                    "  on hidden mains and inputs, then checked with valgrind"
                    " for leaks,"
                ),
                (
                    "  bad memory accesses and open fds (when valgrind is"
                    " installed)."
                ),
                "  servers (mini_serv, mini_db) are driven with real sockets.",
                "",
                (
                    "write your answer in"
                    f" {ui.paint('rendu/<question>/', ui.HILITE)} — the files"
                    " are created for you."
                ),
                (
                    "files a subject hands out are copied there too; the tests"
                    " always use the originals."
                ),
                (
                    "when you leave a session, rendu/ is moved to"
                    f" {ui.paint('.examshell/trace/<date>/', ui.HILITE)}."
                ),
            ],
            title="modes",
        )
    )
    print()
    session._help(session.PRACTICE_HELP)
    ui.say(
        "in the exam, `solution` and `retry` are disabled and `next` swaps the"
        " question."
    )
    print()
    ui.pause()


def update_screen() -> None:
    ui.clear()
    print()
    if not (config.ROOT / ".git").exists() or not shutil.which("git"):
        print(
            "  "
            + ui.paint(
                "not a git checkout — download the latest version manually",
                ui.HILITE,
            )
        )
    else:
        print("  " + ui.paint("pulling the latest version…", ui.ACCENT))
        proc = subprocess.run(
            ["git", "-C", str(config.ROOT), "pull", "--ff-only"],
            capture_output=True,
            text=True,
        )
        print(ui.indent_block((proc.stdout + proc.stderr).strip(), "  │ "))
        print()
        if proc.returncode == 0:
            print(
                "  "
                + ui.paint(
                    "✔ up to date — restart to load any new code", ui.OK
                )
            )
        else:
            print(
                "  "
                + ui.paint(
                    "✘ update failed (local changes? no network?)", ui.ERR
                )
            )
    print()
    ui.pause()


# ── main loop ───────────────────────────────────────────────────────────────
MAIN_MENU: list[tuple[int | str, str, str]] = [
    (1, "Practice", "whole levels or any question, peek allowed"),
    (2, "Real exam", "levels, clock, cooldowns, a grade"),
    (3, "Stats", "your history and weak spots"),
    (4, "Open rendu", "open your answer folder"),
    (5, "Update", "git pull the latest version"),
    (6, "Help", "how all of this works"),
    ("q", "Quit", ""),
]


def main_menu(stats: Stats) -> None:
    splash()
    choice = ui.menu(
        "main menu", MAIN_MENU, footer="type a number · q to quit"
    )
    if choice in (None, "q"):
        raise SystemExit(0)
    try:
        if choice == 1:
            rank = choose_rank("practice · choose a rank")
            if rank:
                ui.clear()
                playlist = pick_question(rank, stats)
                if playlist:
                    session.practice(rank, playlist, stats)
                    _archive()
        elif choice == 2:
            rank = choose_rank("real exam · choose a rank", exam=True)
            if rank:
                session.exam(rank, stats)
        elif choice == 3:
            stats_screen(stats)
        elif choice == 4:
            if not workspace.open_folder(config.RENDU):
                print(
                    "  "
                    + ui.paint(
                        "couldn't open a file manager — it's at"
                        f" {config.RENDU}",
                        ui.HILITE,
                    )
                )
                ui.pause()
        elif choice == 5:
            update_screen()
        elif choice == 6:
            help_screen()
    except KeyboardInterrupt:
        print()  # ctrl-c inside a screen = back to the main menu


def run_interactive() -> int:
    workspace.migrate_layout()
    missing = missing_questions()
    if missing:
        print(ui.paint("config.py lists questions with no folder:", ui.ERR))
        for q in missing:
            print("  " + str(q.path.relative_to(config.ROOT)))
        return 1
    stats = Stats.load()
    _archive()  # leftovers from a crashed session
    try:
        while True:
            main_menu(stats)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        trace = workspace.archive()
        print()
        if trace:
            print(
                "  "
                + ui.paint(
                    "your code was saved to"
                    f" {trace.relative_to(config.ROOT)}/",
                    ui.MUTED,
                )
            )
        print("  " + ui.paint("good luck on the exam :3", ui.ACCENT))
        print()
    return 0


# ── self-check ──────────────────────────────────────────────────────────────
def check(ranks: list[config.Rank], answers: Path | None = None) -> int:
    """Grade every question with the reference solution (or your answers
    folder)."""
    if config.RENDU.exists():
        workspace.archive()
    if answers is None:
        # the references are known not to leak: a smaller valgrind sample
        # keeps this quick
        os.environ.setdefault("EXAMSHELL_LEAK_SAMPLE", "2")
    failures: list[str] = []
    skipped: list[str] = []
    # every question has its own rendu/<q>/ and harness process, so grade
    # them side by side
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        # every question of every rank is queued at once; results print in
        # order. A subject folder shared by several ranks (the piscine borrows
        # rank02's) is graded once
        jobs: dict[
            str, list[tuple[Question, Future[runner.Result | None]]]
        ] = {}
        seen: set[Path] = set()
        shared: dict[str, int] = {}
        # owners first, borrowers after
        for r in sorted(ranks, key=lambda r: bool(r.borrow)):
            jobs[r.key] = []
            for q in all_questions(r):
                if q.path in seen:
                    shared[r.key] = shared.get(r.key, 0) + 1
                    continue
                seen.add(q.path)
                jobs[r.key].append((q, pool.submit(_check_one, q, answers)))
        for rank in ranks:
            print(ui.paint(f"\n{rank.label}", "bold"))
            if shared.get(rank.key):
                note = f"{shared[rank.key]} shared with another rank, checked"
                print(
                    f"  {ui.paint('·', 'gray')}"
                    f" {ui.paint(note + ' once', 'gray')}"
                )
            for q, job in jobs[rank.key]:
                result = job.result()
                if result is None:
                    skipped.append(q.id)
                    print(
                        f"  {ui.paint('-', 'gray')} {q.name:<26}"
                        f" {ui.paint('no answer found', 'gray')}"
                    )
                    continue
                mark = (
                    ui.paint("✔", ui.OK)
                    if result.passed
                    else ui.paint("✘", ui.ERR)
                )
                note = (
                    "timeout" if result.timed_out else f"{result.seconds:.1f}s"
                )
                print(f"  {mark} {q.name:<26} {ui.paint(note, 'gray')}")
                if not result.passed:
                    failures.append(q.id)
    shutil.rmtree(config.RENDU, ignore_errors=True)
    workspace.clean_caches()
    total = sum(len(j) for j in jobs.values()) - len(skipped)
    print()
    print(
        f"{total - len(failures)}/{total} passed"
        + (f", {len(skipped)} without an answer" if skipped else "")
    )
    for f in failures:
        print("  " + ui.paint("✘ " + f, ui.ERR))
    return 1 if failures else 0


_RENDU_LOCKS: dict[str, threading.Lock] = {}
_RENDU_GUARD = threading.Lock()


def _check_one(q: Question, answers: Path | None) -> runner.Result | None:
    """Grade one question with its reference (or your answer). None = no
    answer found."""
    # two ranks can share a question name, and so a rendu/<name>/ folder
    with _RENDU_GUARD:
        lock = _RENDU_LOCKS.setdefault(q.name, threading.Lock())
    with lock:
        return _check_one_locked(q, answers)


def _check_one_locked(
    q: Question, answers: Path | None
) -> runner.Result | None:
    source = _find_answer(q, answers) if answers else q.reference_dir
    if source is None:
        return None
    workspace.prepare(q)
    if q.is_python and not answers:
        shutil.copy(q.path / "solution.py", q.candidate)
    else:
        for name in q.files_in(source):
            if (source / name).is_file():
                shutil.copy(source / name, q.rendu_dir / name)
    try:
        return runner.run_tests(q, quiet=True)
    finally:
        shutil.rmtree(q.rendu_dir, ignore_errors=True)


def _find_answer(q: Question, root: Path) -> Path | None:
    """Look for <root>/**/<question>/ holding the expected files (at least
    the first)."""
    for path in sorted(root.rglob(q.expected_files[0])):
        if path.parent.name == q.name:
            return path.parent
    return None


def _ranks_for(choice: str) -> list[config.Rank]:
    if choice == "all":
        return list(config.RANKS.values())
    groups = {
        "piscine": "piscine",
        "python": "current",
        "current": "current",
        "c": "old",
        "old": "old",
    }
    if choice in groups:
        return [
            r for r in config.RANKS.values() if r.curriculum == groups[choice]
        ]
    return [config.RANKS[choice]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="examshell", description=f"{config.APP_NAME} — 42 exam practice"
    )
    parser.add_argument(
        "--check",
        nargs="?",
        const="all",
        choices=[
            "all",
            "piscine",
            "python",
            "c",
            "current",
            "old",
            *config.RANKS,
        ],
        help="grade every question with the reference solutions",
    )
    parser.add_argument(
        "--answers",
        metavar="DIR",
        help=(
            "with --check: grade your own answers from DIR (<question>/<file>"
            " anywhere inside)"
        ),
    )
    args = parser.parse_args(argv)
    if args.check:
        ranks = _ranks_for(args.check)
        return check(
            ranks, Path(args.answers).resolve() if args.answers else None
        )
    return run_interactive()


if __name__ == "__main__":
    sys.exit(main())
