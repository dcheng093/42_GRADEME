"""Entry point: python3 -m examshell  (or just `make`)."""

import argparse
import random
import shutil
import subprocess
import sys

from . import config, runner, session, ui, workspace
from .questions import all_questions, missing_questions
from .stats import Stats


# ── screens ─────────────────────────────────────────────────────────────────
NOTICE = []  # one-shot messages shown under the banner


def splash():
    ui.clear()
    print()
    print(ui.big(config.APP_NAME))
    print()
    print("  " + ui.paint(config.TAGLINE, ui.MUTED))
    print()
    while NOTICE:
        print("  " + NOTICE.pop(0))
    print()


def _archive():
    trace = workspace.archive()
    if trace:
        NOTICE.append(ui.paint("✔ ", ui.OK) + ui.paint("your code was saved to ", ui.MUTED)
                      + ui.paint(f"{trace.relative_to(config.ROOT)}/", ui.HILITE))


def choose_rank(purpose, exam=False):
    ranks = [r for r in config.RANKS.values() if r.exam or not exam]
    options = [
        (i, r.title, f"{'C' if r.language == 'c' else 'Python'} · {len(r.levels)} levels · "
                     f"{len(all_questions(r))} questions")
        for i, r in enumerate(ranks, 1)
    ]
    choice = ui.menu(purpose, options, footer="enter = back")
    return None if choice is None else ranks[choice - 1]


def _mark(stats, q):
    s = stats.question(q.id)
    if s.get("passes"):
        return ui.paint("✔", ui.OK)
    if s.get("fails"):
        return ui.paint("✘", ui.ERR)
    return ui.paint("·", ui.MUTED)


PICK_COMMANDS = (
    ("L2", "every question of level 2, shuffled — then on to level 3"),
    ("7", "start at question 7 (or type its name) and go in order"),
    ("r", "start at a random question"),
    ("enter", "back"),
)


def pick_question(rank, stats):
    """Level map. Returns the playlist of questions to practise, or None."""
    questions = all_questions(rank)
    col = max(len(q.name) for q in questions) + 10
    per_row = max(1, min(3, (ui.card_width() - 4) // col))
    print()
    print(ui.status_strip(ui.chip(config.APP_NAME) + "  " + ui.paint(rank.title, "bold") + "  " + ui.chip("PRACTICE"),
                          ui.paint("pick where to start", ui.MUTED)))
    print()
    for li, level in enumerate(rank.levels):
        entries = [(i, q) for i, q in enumerate(questions) if q.level == li]
        solved = sum(1 for _, q in entries if stats.question(q.id).get("passes"))
        lines = []
        for row in range(0, len(entries), per_row):
            cells = []
            for i, q in entries[row:row + per_row]:
                cell = f"{ui.paint(f'{i + 1:>3}', ui.MUTED)}  {_mark(stats, q)} {q.name}"
                cells.append(cell + " " * (col - ui.visible_len(cell)))
            lines.append("".join(cells).rstrip())
        print(ui.card(lines, title=f"L{li + 1}  {level.theme}", right=ui.level_bar(solved, len(entries), 10)))
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
            return session.from_question(rank, random.randrange(len(questions)))
        if choice.startswith("l") and choice[1:].isdigit() and 1 <= int(choice[1:]) <= len(rank.levels):
            return session.level_run(rank, int(choice[1:]) - 1)
        if choice.isdigit() and 1 <= int(choice) <= len(questions):
            return session.from_question(rank, int(choice) - 1)
        names = [q.name.lower() for q in questions]
        if choice in names:
            return session.from_question(rank, names.index(choice))
        print("  " + ui.paint(f"'{choice}' is not a level, question number or name", ui.ERR))


def stats_screen(stats):
    while True:
        ui.clear()
        print()
        print(ui.big("STATS"))
        print()
        for rank in config.RANKS.values():
            lines = []
            for li, level in enumerate(rank.levels):
                qs = [q for q in all_questions(rank) if q.level == li]
                tried = [q for q in qs if stats.question(q.id).get("attempts")]
                solved = sum(1 for q in qs if stats.question(q.id).get("passes"))
                if li:
                    lines.append("")
                lines.append(ui.paint(f"L{li + 1} ", ui.HILITE, "bold") + ui.paint(f"{level.theme:<20}", "bold")
                             + ui.level_bar(solved, len(qs), 12)
                             + ui.paint(f"  · {len(tried)} tried", ui.MUTED))
                for q in tried:
                    s = stats.question(q.id)
                    rate = s["passes"] / s["attempts"]
                    best = ui.duration(s["best_time"]) if s.get("best_time") is not None else "  -  "
                    weak = ui.paint("  weak", ui.ERR, "bold") if s["fails"] > s["passes"] else ""
                    lines.append(f"   {q.name:<24} {ui.bar(rate, 12, ui.OK if rate >= .5 else ui.HILITE)} "
                                 f"{s['passes']:>2}/{s['attempts']:<3} {ui.paint('best', ui.MUTED)} {best}{weak}")
            print(ui.card(lines, title=rank.title))
            print()
        exams = stats.data["exams"][-8:]
        if exams:
            lines = []
            for e in reversed(exams):
                g = e["grade"]
                title = config.RANKS[e["rank"]].title if e["rank"] in config.RANKS else e["rank"]
                lines.append(f"{ui.paint(e['date'].replace('T', ' '), ui.MUTED)}  {title:<8}"
                             f" {ui.bar(g / 100, 10, ui.OK if g == 100 else ui.HILITE if g >= 50 else ui.ERR)}"
                             f" {g:>3}/100  {ui.paint(ui.duration(e['duration']), ui.MUTED)}")
            print(ui.card(lines, title="recent exams"))
            print()
        print(ui.command_card([("reset", "wipe all stats"), ("enter", "back")], title="options"))
        print()
        choice = ui.ask().lower()
        if choice == "reset":
            if ui.confirm("really delete all your stats?"):
                stats.reset()
        else:
            return


def help_screen():
    ui.clear()
    print()
    print(ui.big("HELP"))
    print()
    print(ui.card([
        ui.paint("practice", ui.ACCENT, "bold"),
        "  pick a level and do every question in it (shuffled), or start",
        "  anywhere and go in order. test as often as you like, peek at",
        "  solutions, retry the ones you failed. a summary screen tells you",
        "  when you finish a level.",
        "",
        ui.paint("real exam", ui.ACCENT, "bold"),
        "  one random question per level, a countdown clock,",
        "  a cooldown after each failed test, grade out of 100.",
        "",
        f"write your answer in {ui.paint('rendu/<question>/', ui.HILITE)} — the file is created for you.",
        f"when you leave a session, rendu/ is moved to {ui.paint('trace/<date>/', ui.HILITE)}.",
    ], title="modes"))
    print()
    session._help(session.PRACTICE_HELP)
    ui.say("in the exam, `solution` and `retry` are disabled and `next` swaps the question.")
    print()
    ui.pause()


def update_screen():
    ui.clear()
    print()
    if not (config.ROOT / ".git").exists() or not shutil.which("git"):
        print("  " + ui.paint("not a git checkout — download the latest version manually", ui.HILITE))
    else:
        print("  " + ui.paint("pulling the latest version…", ui.ACCENT))
        proc = subprocess.run(["git", "-C", str(config.ROOT), "pull", "--ff-only"],
                              capture_output=True, text=True)
        print(ui.indent_block((proc.stdout + proc.stderr).strip(), "  │ "))
        print()
        if proc.returncode == 0:
            print("  " + ui.paint("✔ up to date — restart to load any new code", ui.OK))
        else:
            print("  " + ui.paint("✘ update failed (local changes? no network?)", ui.ERR))
    print()
    ui.pause()


# ── main loop ───────────────────────────────────────────────────────────────
MAIN_MENU = [
    (1, "Practice", "whole levels or any question, peek allowed"),
    (2, "Real exam", "levels, clock, cooldowns, a grade"),
    (3, "Stats", "your history and weak spots"),
    (4, "Open rendu", "open your answer folder"),
    (5, "Update", "git pull the latest version"),
    (6, "Help", "how all of this works"),
    ("q", "Quit", ""),
]


def main_menu(stats):
    splash()
    choice = ui.menu("main menu", MAIN_MENU, footer="type a number · q to quit")
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
                print("  " + ui.paint(f"couldn't open a file manager — it's at {config.RENDU}", ui.HILITE))
                ui.pause()
        elif choice == 5:
            update_screen()
        elif choice == 6:
            help_screen()
    except KeyboardInterrupt:
        print()  # ctrl-c inside a screen = back to the main menu


def run_interactive():
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
            print("  " + ui.paint(f"your code was saved to {trace.relative_to(config.ROOT)}/", ui.MUTED))
        print("  " + ui.paint("good luck on the exam :3", ui.ACCENT))
        print()
    return 0


# ── self-check ──────────────────────────────────────────────────────────────
def check(ranks, answers=None):
    """Grade every question with the reference solution (or your answers folder)."""
    if config.RENDU.exists():
        workspace.archive()
    failures, skipped = [], []
    for rank in ranks:
        print(ui.paint(f"\n{rank.title}", "bold"))
        for q in all_questions(rank):
            source = _find_answer(q, answers) if answers else q.path
            if source is None:
                skipped.append(q.id)
                print(f"  {ui.paint('-', 'gray')} {q.name:<26} {ui.paint('no answer found', 'gray')}")
                continue
            workspace.prepare(q)
            if rank.language == "python":
                src = source / "solution.py" if source == q.path else source / q.expected_files[0]
                shutil.copy(src, q.candidate)
            else:
                for name in q.expected_files:
                    if (source / name).is_file():
                        shutil.copy(source / name, q.rendu_dir / name)
            result = runner.run_tests(q, quiet=True)
            mark = ui.paint("✔", ui.OK) if result.passed else ui.paint("✘", ui.ERR)
            note = "timeout" if result.timed_out else f"{result.seconds:.1f}s"
            print(f"  {mark} {q.name:<26} {ui.paint(note, 'gray')}")
            if not result.passed:
                failures.append(q.id)
            shutil.rmtree(q.rendu_dir, ignore_errors=True)
    shutil.rmtree(config.RENDU, ignore_errors=True)
    workspace.clean_caches()
    total = sum(len(all_questions(r)) for r in ranks) - len(skipped)
    print()
    print(f"{total - len(failures)}/{total} passed" + (f", {len(skipped)} without an answer" if skipped else ""))
    for f in failures:
        print("  " + ui.paint("✘ " + f, ui.ERR))
    return 1 if failures else 0


def _find_answer(q, root):
    """Look for <root>/**/<question>/<expected file>."""
    for path in sorted(root.rglob(q.expected_files[0])):
        if path.parent.name == q.name:
            return path.parent
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(prog="examshell", description=f"{config.APP_NAME} — 42 exam practice")
    parser.add_argument("--check", nargs="?", const="all", choices=["all", *config.RANKS],
                        help="grade every question with the reference solutions")
    parser.add_argument("--answers", metavar="DIR",
                        help="with --check: grade your own answers from DIR (<question>/<file> anywhere inside)")
    args = parser.parse_args(argv)
    if args.check:
        from pathlib import Path
        ranks = list(config.RANKS.values()) if args.check == "all" else [config.RANKS[args.check]]
        return check(ranks, Path(args.answers).resolve() if args.answers else None)
    return run_interactive()


if __name__ == "__main__":
    sys.exit(main())
