"""Practice mode and real exam mode."""

import math
import random
import sys
import time

from . import config, runner, ui, workspace
from .questions import Question, all_questions

PRACTICE_COMMANDS = (
    ("test", "run the tests on your rendu file"),
    ("next", "next question"),
    ("prev", "previous question"),
    ("sub", "show the subject again"),
    ("solution", "peek at the reference solution"),
    ("retry", "jump to a question you failed before"),
    ("time", "time spent on this question"),
    ("help", "this list"),
    ("menu", "back to the main menu"),
    ("exit", "quit"),
)
EXAM_COMMANDS = (
    ("test", "grade your rendu file"),
    ("next", "swap for another question of this level (counts as a skip)"),
    ("sub", "show the subject again"),
    ("time", "time left"),
    ("help", "this list"),
    ("menu", "give up and go back to the main menu"),
    ("exit", "give up and quit"),
)


# ── shared screen pieces ────────────────────────────────────────────────────
def _header(q, mode, right=""):
    lvl = q.rank.levels[q.level]
    dot = ui.paint("  ·  ", "gray")
    left = (ui.paint(config.APP_NAME, 207, "bold") + dot + f"{q.rank.title} {ui.paint(mode, 'gray')}" + dot
            + f"L{q.level + 1}/{len(q.rank.levels)} {ui.paint(lvl.theme, 'gray')}" + dot
            + ui.paint(q.name, "cyan", "bold"))
    gap = ui.width() - ui.visible_len(left) - ui.visible_len(right) - 2
    print(" " + left + " " * max(gap, 2) + right)
    print(" " + ui.rule())


def _subject(q):
    print()
    for line in q.subject.splitlines():
        if set(line.strip()) == {"-"}:
            print("  " + ui.rule("─"))
        elif ":" in line and line.split(":")[0].strip() in (
                "Assignment name", "Expected files", "Allowed functions", "Forbidden functions"):
            label, value = line.split(":", 1)
            print("  " + ui.paint(f"{label.strip():<20}", "gray") + ui.paint(value.strip(), "bold"))
        else:
            print("  " + line)
    print()
    rel = q.candidate.relative_to(config.ROOT)
    print("  " + ui.paint("your file  ", "gray") + ui.paint(str(rel), "yellow"))


def _command_hint(commands):
    names = "  ".join(ui.paint(name, 207) for name, _ in commands)
    print("  " + ui.paint("commands   ", "gray") + names)
    print()


def _help(commands):
    print(ui.box([f"{ui.paint(f'{n:<9}', 207, 'bold')} {d}" for n, d in commands], title="commands"))


def _is_empty(q):
    return not q.candidate.is_file() or q.candidate.stat().st_size == 0


def _grade(q, stats, started):
    """Run the tests, print the verdict, record it. Returns the Result or None."""
    if _is_empty(q):
        print("  " + ui.paint(f"{q.candidate.relative_to(config.ROOT)} is empty — write your answer there first",
                              "yellow"))
        return None
    print()
    result = runner.run_tests(q)
    stats.record_test(q.id, result.passed, time.monotonic() - started)
    print()
    print(ui.big("PASSED", 46) if result.passed else ui.big("FAILED", 196))
    print()
    return result


def _show_solution(q):
    if q.solution is None:
        print("  " + ui.paint("no reference solution for this one", "gray"))
        return
    lines = q.solution.read_text(errors="replace").rstrip().splitlines()
    print(ui.box([ui.paint(f"{i:>3} ", "gray") + line.replace("\t", "    ") for i, line in enumerate(lines, 1)],
                 title=f"solution · {q.solution.name}", color="yellow"))


def _ask(label):
    """Read a command. Ctrl-C means 'menu', Ctrl-D means 'exit'."""
    try:
        return ui.ask(label).lower()
    except KeyboardInterrupt:
        print()
        return "menu"
    except EOFError:
        print()
        return "exit"


# ── practice ────────────────────────────────────────────────────────────────
def practice(rank, start, stats):
    questions = all_questions(rank)
    idx = start
    while True:
        action = _practice_question(questions[idx], idx, len(questions), stats)
        if action == "next":
            idx = (idx + 1) % len(questions)
        elif action == "prev":
            idx = (idx - 1) % len(questions)
        elif isinstance(action, Question):
            idx = questions.index(action)
        else:  # menu
            return


def _practice_question(q, pos, total, stats):
    workspace.prepare(q)
    started = time.monotonic()
    redraw = True
    while True:
        if redraw:
            ui.clear()
            right = ui.paint(f"{pos + 1}/{total}", "gray")
            _header(q, "practice", right)
            _subject(q)
            _command_hint(PRACTICE_COMMANDS)
            redraw = False
        cmd = _ask(q.name)
        if cmd == "test":
            result = _grade(q, stats, started)
            if result and result.passed:
                print("  " + ui.paint(f"solved in {ui.duration(time.monotonic() - started)}", "green"))
                try:
                    go = input(ui._rl_safe("  " + ui.paint("next question? [Y/n] ", "gray"))).strip().lower()
                except (KeyboardInterrupt, EOFError):
                    go = "n"
                if go in ("", "y", "yes"):
                    return "next"
        elif cmd in ("next", "n"):
            return "next"
        elif cmd in ("prev", "p"):
            return "prev"
        elif cmd in ("sub", "s", "clear"):
            redraw = True
        elif cmd in ("solution", "sol"):
            if ui.confirm("spoil the reference solution?"):
                _show_solution(q)
        elif cmd == "retry":
            failed = [n for n in stats.failed_questions(q.rank.key) if n != q.name]
            pool = [x for x in all_questions(q.rank) if x.name in failed]
            if not pool:
                print("  " + ui.paint("nothing to retry — no failed questions on record", "gray"))
            else:
                return random.choice(pool)
        elif cmd in ("time", "t"):
            print("  " + ui.paint(f"on this question for {ui.duration(time.monotonic() - started)}", "cyan"))
        elif cmd in ("help", "h", "?"):
            _help(PRACTICE_COMMANDS)
        elif cmd in ("menu", "m", "back"):
            return "menu"
        elif cmd in ("exit", "quit", "q"):
            raise SystemExit(0)
        elif cmd:
            print("  " + ui.paint(f"unknown command '{cmd}' — type help", "red"))


# ── real exam ───────────────────────────────────────────────────────────────
class _ExamOver(Exception):
    def __init__(self, reason, quit_after=False):
        super().__init__(reason)
        self.reason, self.quit_after = reason, quit_after


def exam(rank, stats):
    n = len(rank.levels)
    ui.clear()
    print(ui.big(rank.title.replace(" ", "")))
    print()
    rules = [
        f"{n} levels · one random question per level · {ui.duration(rank.time_limit)} on the clock",
        f"each level cleared is worth {100 / n:.0f} points · grade {ui.paint('100', 'green', 'bold')} = all cleared",
        "a failed test keeps the same question"
        + (f", and adds a cooldown ({', '.join(f'{s}s' for s in config.COOLDOWN_STEPS)})"
           if config.COOLDOWN_ENABLED else ""),
        "`next` swaps the question for another from the same level",
        "no solutions, no retry — just like the real thing",
    ]
    print(ui.box(["• " + r for r in rules], title=f"{rank.title} · real exam", color="magenta"))
    print()
    try:
        ui.pause("press enter to start the clock (ctrl-c to go back)")
    except (KeyboardInterrupt, EOFError):
        return

    workspace.archive()
    clock = {"start": time.monotonic()}
    clock["deadline"] = clock["start"] + rank.time_limit
    passed = 0
    quit_after = False
    reason = "finished"
    try:
        for level in range(n):
            _exam_level(rank, level, passed, clock, stats)
            passed += 1
    except _ExamOver as over:
        reason, quit_after = over.reason, over.quit_after

    elapsed = time.monotonic() - clock["start"]
    grade = round(passed * 100 / n)
    stats.record_exam(rank.key, grade, elapsed, passed, n)
    trace = workspace.archive()
    _exam_result(rank, grade, passed, elapsed, reason, trace)
    if quit_after:
        raise SystemExit(0)
    try:
        ui.pause("press enter to go back to the menu")
    except (KeyboardInterrupt, EOFError):
        pass


def _time_left(clock):
    return clock["deadline"] - time.monotonic()


def _exam_level(rank, level, passed, clock, stats):
    pool = list(rank.levels[level].pool)
    random.shuffle(pool)
    seen = [pool.pop()]
    q = Question(rank, level, seen[0])
    workspace.prepare(q)
    started = time.monotonic()
    fails = 0
    cooldown_until = 0.0
    redraw = True
    while True:
        if _time_left(clock) <= 0:
            raise _ExamOver("time")
        if redraw:
            ui.clear()
            left = _time_left(clock)
            clock_color = "red" if left < 15 * 60 else "yellow" if left < 60 * 60 else "green"
            grade = round(passed * 100 / len(rank.levels))
            right = ui.paint(f"grade {grade}", "bold") + ui.paint("  ·  ", "gray") + ui.paint(ui.duration(left), clock_color)
            _header(q, "exam", right)
            print("  " + ui.roadmap(rank, level, passed))
            _subject(q)
            _command_hint(EXAM_COMMANDS)
            redraw = False

        cmd = _ask(ui.duration(_time_left(clock)))
        if _time_left(clock) <= 0:
            print("  " + ui.paint("time's up!", "red", "bold"))
            raise _ExamOver("time")

        if cmd == "test":
            wait = cooldown_until - time.monotonic()
            if wait > 0 and not _countdown(cooldown_until):
                continue
            result = _grade(q, stats, started)
            if result is None:
                continue
            if result.passed:
                print("  " + ui.paint(f"level {level + 1} cleared in {ui.duration(time.monotonic() - started)}"
                                      f"  +{100 / len(rank.levels):.0f} points", "green", "bold"))
                if level + 1 < len(rank.levels):
                    try:
                        ui.pause("press enter for the next level")
                    except (KeyboardInterrupt, EOFError):
                        pass
                return
            fails += 1
            if config.COOLDOWN_ENABLED:
                steps = config.COOLDOWN_STEPS
                delay = steps[min(fails - 1, len(steps) - 1)]
                cooldown_until = time.monotonic() + delay
                if delay:
                    print("  " + ui.paint(f"next test available in {delay}s", "yellow"))
        elif cmd in ("next", "n"):
            if not pool:
                print("  " + ui.paint("no other question left in this level", "gray"))
                continue
            seen.append(pool.pop())
            q = Question(rank, level, seen[-1])
            workspace.prepare(q)
            started = time.monotonic()
            redraw = True
        elif cmd in ("sub", "s", "clear"):
            redraw = True
        elif cmd in ("time", "t"):
            print("  " + ui.paint(f"{ui.duration(_time_left(clock))} left · "
                                  f"{ui.duration(time.monotonic() - clock['start'])} elapsed", "cyan"))
        elif cmd in ("help", "h", "?"):
            _help(EXAM_COMMANDS)
        elif cmd in ("solution", "sol", "retry"):
            print("  " + ui.paint("not in the real exam ;)", "gray"))
        elif cmd in ("menu", "m", "back"):
            if _safe_confirm("give up the exam?"):
                raise _ExamOver("abandoned")
        elif cmd in ("exit", "quit", "q"):
            if _safe_confirm("give up the exam and quit?"):
                raise _ExamOver("abandoned", quit_after=True)
        elif cmd:
            print("  " + ui.paint(f"unknown command '{cmd}' — type help", "red"))


def _safe_confirm(question):
    try:
        return ui.confirm(question)
    except (KeyboardInterrupt, EOFError):
        print()
        return False


def _countdown(until):
    """Live cooldown timer. Returns False if cancelled with ctrl-c."""
    try:
        while (left := until - time.monotonic()) > 0:
            sys.stdout.write("\r  " + ui.paint(f"◷ cooldown {math.ceil(left):>3}s", "yellow")
                             + ui.paint("  (ctrl-c to cancel)", "gray") + "\x1b[K")
            sys.stdout.flush()
            time.sleep(0.2)
    except KeyboardInterrupt:
        print()
        return False
    sys.stdout.write("\r\x1b[K")
    return True


def _exam_result(rank, grade, passed, elapsed, reason, trace):
    ui.clear()
    color = 46 if grade == 100 else 220 if grade >= 50 else 196
    print()
    print(ui.big(f"{grade}/100", color))
    print()
    print("  " + ui.roadmap(rank, -1, passed))
    print()
    verdict = {
        "finished": "all levels cleared — go get that rank!",
        "time": "the clock ran out",
        "abandoned": "you gave up this one",
    }[reason]
    lines = [
        f"{ui.paint('result', 'gray')}    {verdict}",
        f"{ui.paint('levels', 'gray')}    {passed}/{len(rank.levels)}",
        f"{ui.paint('time', 'gray')}      {ui.duration(elapsed)} of {ui.duration(rank.time_limit)}",
    ]
    if trace:
        lines.append(f"{ui.paint('your code', 'gray')} {trace.relative_to(config.ROOT)}/")
    print(ui.box(lines, title=f"{rank.title} · exam over", color="magenta"))
    print()
